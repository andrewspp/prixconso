# -*- coding: utf-8 -*- # Add this line for better encoding support
import time
import re # Import regular expression module for parsing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# Corrected import line: ValueError removed
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

def scrape_auchan_price(url, postal_code="75001", attente_initiale=5, timeout_duration=30):
    """
    Scrape le prix et les informations d'un produit Auchan en utilisant un code postal spécifique.
    Prioritise la sélection du premier point relais/magasin trouvé.
    """
    print(f"--- Début du scraping ---")
    print(f"URL: {url}")
    print(f"Code Postal Cible: {postal_code}")

    options = Options()
    # options.add_argument("--headless") # Uncomment for headless mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument('--log-level=3') # Suppress unnecessary logs
    options.add_argument('--disable-gpu') # Often needed for headless
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    options.add_argument('--lang=fr-FR') # Try setting language

    driver = None
    try:
        print("Initialisation du WebDriver Chrome...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, timeout_duration) # General wait
        print("WebDriver initialisé.")

        print(f"Chargement de l'URL: {url}")
        driver.get(url)
        print("Page chargée. Attente initiale...")
        time.sleep(attente_initiale)

        # Accepter les cookies
        try:
            print("Recherche du bouton cookies...")
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print("Cookies acceptés.")
            time.sleep(1)
        except TimeoutException:
            print("Pas de popup de cookies trouvée ou déjà acceptée.")
        except Exception as e:
            print(f"Erreur lors de l'acceptation des cookies: {e}")

        # --- Logique principale ---
        try:
            # 1. Find and click the button to open the location modal
            show_price_button_xpath = "//button[contains(., 'Afficher le prix') or contains(., 'Choisir mon magasin') or contains(., 'Retrait') or contains(., 'Livraison') or contains(@data-testid, 'delivery-method')]"
            print(f"Recherche du bouton de localisation via XPath: {show_price_button_xpath}")
            show_price_button = wait.until(EC.element_to_be_clickable((By.XPATH, show_price_button_xpath)))
            print(f"Bouton trouvé: '{show_price_button.text}'. Clic...")
            driver.execute_script("arguments[0].click();", show_price_button)
            print("Bouton cliqué. Attente de l'ouverture du modal/popup...")
            time.sleep(3)

            # 2. Find the postal code input field
            postal_input_selectors = [
                "input[placeholder*='postal']", "input[name*='postal']", "input[id*='postal']",
                "input[data-testid*='postal']", "input#search-input", "input[aria-label*='postal']",
                "input.journeySearchInput"
            ]
            postal_input = None
            postal_wait = WebDriverWait(driver, 15)
            for selector in postal_input_selectors:
                try:
                    print(f"Tentative de trouver le champ postal avec le sélecteur CSS: {selector}")
                    postal_input = postal_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print("Champ de code postal trouvé et cliquable.")
                    break
                except TimeoutException:
                    print(f"Sélecteur '{selector}' n'a pas fonctionné.")
                    continue
            if not postal_input:
                print("ERREUR: Impossible de trouver le champ de saisie du code postal.")
                driver.save_screenshot("error_postal_input_not_found.png")
                raise TimeoutException("Impossible de trouver le champ de saisie du code postal.")

            # 3. Enter postal code and select suggestion
            print(f"Saisie du code postal '{postal_code}'...")
            postal_input.clear()
            postal_input.send_keys(postal_code)
            print("Attente des suggestions de localisation...")
            time.sleep(2.5)

            first_suggestion_xpath = f"//ul[contains(@class, 'journey__search-suggests-list') and not(contains(@class, 'hidden'))]//li[contains(.,'{postal_code}')][1]"
            print(f"Recherche de la première suggestion avec XPath: {first_suggestion_xpath}")
            suggestion_clicked = False
            try:
                 suggestion_wait = WebDriverWait(driver, 10)
                 first_suggestion = suggestion_wait.until(EC.element_to_be_clickable((By.XPATH, first_suggestion_xpath)))
                 suggestion_text = first_suggestion.text.strip().replace('\n', ' ')
                 print(f"Première suggestion trouvée: '{suggestion_text}'. Clic...")
                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_suggestion)
                 time.sleep(0.5)
                 driver.execute_script("arguments[0].click();", first_suggestion)
                 suggestion_clicked = True
                 print("Suggestion cliquée. Attente de l'affichage de la liste des magasins...")
            except TimeoutException:
                 print(f"WARN: Aucune suggestion cliquable trouvée pour '{postal_code}'. Tentative Entrée (peut échouer).")
                 try:
                    postal_input.send_keys(Keys.ENTER)
                    print("Touche Entrée envoyée. Attente...")
                    suggestion_clicked = True
                    time.sleep(4)
                 except Exception as e_enter:
                     print(f"INFO: Échec de l'envoi de la touche Entrée: {e_enter}. Le script essaiera quand même de trouver la liste.")
                     suggestion_clicked = False

            # =================== SECTION SELECTION MAGASIN (avec HTML) ===================
            store_selected = False
            if True: # Toujours essayer de trouver la liste
                print("Attente (jusqu'à 20s) de l'apparition du premier magasin/point relais...")
                store_list_wait = WebDriverWait(driver, 20)
                store_container_base_xpath = "//div[contains(@class, 'journey-offering-context__wrapper') and contains(@class, 'journeyPosItem')]"

                try:
                    print(f"Attente du premier élément avec XPath : {store_container_base_xpath}")
                    store_list_wait.until(
                        EC.presence_of_element_located((By.XPATH, store_container_base_xpath))
                    )
                    print("Premier magasin/point relais détecté. Recherche de la liste complète...")
                    store_containers = driver.find_elements(By.XPATH, store_container_base_xpath)
                    print(f"Liste complète des magasins/points relais trouvée ({len(store_containers)} éléments).")

                    if store_containers:
                        first_container = store_containers[0]
                        store_name_first = "Premier Magasin/Point (Nom non trouvé)"
                        try:
                            name_el = first_container.find_element(By.XPATH, ".//span[contains(@class, 'place-pos__name')]")
                            store_name_first = name_el.text.strip().replace('\n', ' ')
                        except NoSuchElementException:
                             print(f"WARN: Impossible de trouver le nom pour le premier item.")

                        print(f"Tentative prioritaire de sélection du premier: '{store_name_first}'")
                        try:
                            first_choose_button = first_container.find_element(By.XPATH, ".//button[contains(@class, 'btnJourneySubmit') and normalize-space()='Choisir']")
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_choose_button)
                            time.sleep(1)
                            first_button_wait = WebDriverWait(driver, 10)
                            first_choose_button_clickable = first_button_wait.until(
                                EC.element_to_be_clickable(first_choose_button)
                            )
                            print(f"Premier bouton 'Choisir' pour '{store_name_first}' est cliquable. Clic...")
                            driver.execute_script("arguments[0].click();", first_choose_button_clickable)
                            store_selected = True
                            print("Premier bouton 'Choisir' cliqué avec succès.")
                        except (NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e1:
                            print(f"WARN: Échec de la tentative prioritaire sur le premier magasin/point ('{store_name_first}'): {type(e1).__name__}. Passage à la vérification des suivants.")
                            if not store_selected:
                                remaining_containers = store_containers[1:]
                                if not remaining_containers:
                                    print("INFO: Aucun autre magasin/point à vérifier après l'échec du premier.")
                                for i, container in enumerate(remaining_containers):
                                    store_name_current = f"Magasin/Point #{i+2} (Nom non trouvé)"
                                    try:
                                        name_el = container.find_element(By.XPATH, ".//span[contains(@class, 'place-pos__name')]")
                                        store_name_current = name_el.text.strip().replace('\n', ' ')
                                    except NoSuchElementException:
                                        print(f"WARN: Impossible de trouver le nom pour l'item #{i+2}.")
                                    try:
                                        container.find_element(By.XPATH, ".//span[contains(@class, 'no-slot-info') and contains(normalize-space(), 'Pas de créneau disponible')]")
                                        print(f"-> Magasin/Point '{store_name_current}' (item {i+2}) est INDISPONIBLE (texte trouvé).")
                                        continue
                                    except NoSuchElementException:
                                        print(f"-> Magasin/Point '{store_name_current}' (item {i+2}) semble DISPONIBLE (pas de texte d'indisponibilité).")
                                        try:
                                            choose_button = container.find_element(By.XPATH, ".//button[contains(@class, 'btnJourneySubmit') and normalize-space()='Choisir']")
                                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", choose_button)
                                            time.sleep(0.5)
                                            button_wait = WebDriverWait(driver, 5)
                                            choose_button_clickable = button_wait.until(
                                                EC.element_to_be_clickable(choose_button)
                                            )
                                            print(f"Bouton 'Choisir' pour '{store_name_current}' est cliquable. Clic...")
                                            driver.execute_script("arguments[0].click();", choose_button_clickable)
                                            store_selected = True
                                            print(f"Bouton 'Choisir' pour '{store_name_current}' cliqué.")
                                            break
                                        except (NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e2:
                                            print(f"   WARN: Impossible de trouver/cliquer sur 'Choisir' pour le magasin disponible '{store_name_current}': {type(e2).__name__}. Essai du suivant.")
                                            continue
                    else:
                        print("ERREUR: Aucun conteneur de magasin/point relais trouvé via find_elements même après la détection initiale.")
                        driver.save_screenshot("error_no_store_containers_post_wait.png")
                        raise NoSuchElementException("Aucun conteneur de magasin/point relais trouvé (post-wait).")
                except TimeoutException:
                    print(f"ERREUR: La liste des magasins (le premier élément avec XPath: {store_container_base_xpath}) n'est pas apparue ou n'a pas été détectée dans le délai imparti.")
                    driver.save_screenshot("error_store_list_timeout.png")
                    raise TimeoutException("Timeout en attendant le premier élément de la liste des magasins/points relais.")
                except Exception as e_list:
                    print(f"ERREUR inattendue lors du traitement de la liste des magasins: {type(e_list).__name__} - {e_list}")
                    driver.save_screenshot("error_store_list_processing.png")
                    raise

                if not store_selected:
                    print("ERREUR: Impossible de sélectionner un magasin/point relais disponible.")
                    driver.save_screenshot("error_no_store_selected.png")
                    raise TimeoutException("Échec final de la sélection d'un magasin/point relais.")
                else:
                     print("Sélection du magasin réussie. Attente de la mise à jour de la page produit...")
                     time.sleep(5) # Crucial wait for page/price update

            # =================== FIN SECTION SELECTION MAGASIN ===================

            # 6. Récupérer Prix final et Prix au Kilo/Unité
            print("Tentative de récupération des prix...")
            price_final = "Non trouvé"
            price_per_unit = "Non trouvé"
            price_container_xpath = "//div[contains(@class,'default-price')]" # Container for grocery prices

            try:
                price_container = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.XPATH, price_container_xpath))
                )
                # Prix final
                try:
                    price_final_element = price_container.find_element(By.XPATH, ".//div[contains(@class,'product-price--large')]")
                    price_final = price_final_element.text.strip()
                    if not price_final or price_final == '€':
                         raise ValueError("Prix final invalide")
                    print(f"Prix final trouvé: {price_final}")
                except (NoSuchElementException, ValueError):
                    print("WARN: Prix final non trouvé dans le conteneur.")
                    price_final = "Non trouvé" # Reset if error

                # Prix au Kilo/Unité
                try:
                    price_per_unit_element = price_container.find_element(By.XPATH, ".//div[contains(@class,'product-price--smaller')]/span")
                    price_per_unit = price_per_unit_element.text.strip()
                    print(f"Prix par unité trouvé: {price_per_unit}")
                except NoSuchElementException:
                    print("WARN: Prix par unité non trouvé dans le conteneur.")
                    price_per_unit = "Non trouvé" # Reset if error

            except TimeoutException:
                print("ERREUR: Conteneur de prix principal non trouvé.")
                driver.save_screenshot("error_price_container_not_found.png")
                # Keep default "Non trouvé" values

            # Raise error only if *neither* price was found
            if price_final == "Non trouvé" and price_per_unit == "Non trouvé":
                 raise NoSuchElementException("Impossible de trouver les éléments de prix sur la page finale.")

            # 7. Récupérer les informations additionnelles
            print("Récupération des informations additionnelles...")
            product_name = "Nom Inconnu"
            brand = "Marque inconnue"
            attributes = "Non trouvé"
            nutri_score = "Non trouvé"
            description = "Non trouvé"
            ingredients = "Non trouvé"
            conservation = "Non trouvé"
            ean = "Non trouvé"

            # Product Name (Main title)
            try:
                 h1_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
                 product_name = h1_element.text.strip()
            except TimeoutException:
                 print("WARN: Titre H1 (nom produit) non trouvé.")

            # Brand (using meta tag first, then fallback)
            try:
                brand = driver.find_element(By.XPATH, "//meta[@itemprop='brand']").get_attribute('content').strip()
            except NoSuchElementException:
                try:
                   brand_element = driver.find_element(By.XPATH, "//bold[contains(@class,'offer-selector__brand')]")
                   brand = brand_element.text.strip()
                except NoSuchElementException:
                   print("WARN: Marque non trouvée (ni meta, ni bold).")

            # Attributes (Weight, Slices etc.)
            try:
                attribute_elements = driver.find_elements(By.XPATH, "//div[contains(@class,'offer-selector__attributes')]/span[@class='product-attribute']")
                attributes_list = [elem.text.strip() for elem in attribute_elements if elem.text.strip()]
                attributes = " | ".join(attributes_list) if attributes_list else "Non trouvé"
            except NoSuchElementException:
                 print("WARN: Section attributs non trouvée.")

            # Nutri-Score
            try:
                nutri_img = driver.find_element(By.XPATH, "//div[contains(@class,'product-nutriscore')]/img")
                alt_text = nutri_img.get_attribute('alt')
                match = re.search(r'=\s*([A-E])', alt_text, re.IGNORECASE)
                if match:
                    nutri_score = match.group(1).upper()
                else:
                    print("WARN: Lettre Nutri-Score non trouvée dans l'attribut alt.")
            except NoSuchElementException:
                 print("WARN: Image Nutri-Score non trouvée.")

            # --- Extracting from Description Section ---
            description_section_xpath = "//div[@id='product-features']"
            try:
                # Wait for the description section container to be potentially present
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, description_section_xpath)))

                # Description
                try:
                    desc_element = driver.find_element(By.XPATH, f"{description_section_xpath}//h5[contains(.,'Description')]/following-sibling::div/span[contains(@class,'product-features__value')]")
                    description = desc_element.text.strip()
                except NoSuchElementException:
                    print("WARN: Champ Description non trouvé.")

                # Ingredients
                try:
                    ingr_element = driver.find_element(By.XPATH, f"{description_section_xpath}//h5[contains(.,'Ingr')]/following-sibling::div/span[contains(@class,'product-features__value')]")
                    ingredients = ingr_element.text.strip()
                except NoSuchElementException:
                    print("WARN: Champ Ingrédients non trouvé.")

                # Conservation
                try:
                    cons_element = driver.find_element(By.XPATH, f"{description_section_xpath}//span[contains(.,'Conditions particuli')]/following-sibling::div/span[contains(@class,'product-features__value')]")
                    conservation = cons_element.text.strip()
                except NoSuchElementException:
                    print("WARN: Champ Conservation non trouvé.")

                # EAN
                try:
                    ean_container = driver.find_element(By.XPATH, f"{description_section_xpath}//span[contains(.,'EAN')]/following-sibling::div")
                    full_text = ean_container.text.strip()
                    # Extract EAN using regex (assuming it's a 13-digit number)
                    ean_match = re.search(r'\b(\d{13})\b', full_text)
                    if ean_match:
                        ean = ean_match.group(1)
                    else:
                         print("WARN: Numéro EAN (13 chiffres) non trouvé dans le texte.")
                         ean = full_text # Fallback to full text if regex fails
                except NoSuchElementException:
                    print("WARN: Champ EAN non trouvé.")

            except TimeoutException:
                 print("WARN: Section description/caractéristiques (product-features) non trouvée.")

            # 8. Return Results
            return {
                "success": True,
                "product_name": product_name,
                "brand": brand,
                "attributes": attributes,
                "price": price_final,
                "price_per_unit": price_per_unit,
                "nutri_score": nutri_score,
                "description": description,
                "ingredients": ingredients,
                "conservation": conservation,
                "ean": ean,
                "postal_code_used": postal_code,
                "url": url
            }

        # =================== ERROR HANDLING FOR MAIN PROCESS ===================
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, ValueError) as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"Erreur lors du processus principal : {error_msg}")
            error_screenshot_path = f"error_process_{type(e).__name__}.png"
            try:
                driver.save_screenshot(error_screenshot_path)
                print(f"Capture d'écran '{error_screenshot_path}' prise.")
            except Exception as ss_err:
                 print(f"Impossible de prendre capture d'écran d'erreur: {ss_err}")

            product_name_fallback = "Nom non récupéré"
            try:
                 h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                 if h1_elements: product_name_fallback = h1_elements[0].text.strip()
            except: pass

            return {
                "success": False,
                "product_name": product_name_fallback,
                "brand": "Marque non récupérée",
                "attributes": "Non trouvé",
                "price": "Non disponible",
                "price_per_unit": "Non trouvé",
                "nutri_score": "Non trouvé",
                "description": "Non trouvé",
                "ingredients": "Non trouvé",
                "conservation": "Non trouvé",
                "ean": "Non trouvé",
                "error": error_msg,
                 "url": url
                }
    # =================== GENERAL ERROR HANDLING ===================
    except Exception as e:
        error_msg = f"Erreur générale non interceptée: {type(e).__name__} - {e}"
        print(error_msg)
        if driver:
            try:
                driver.save_screenshot("general_error_screenshot.png")
                print("Capture d'écran 'general_error_screenshot.png' prise.")
            except Exception as screenshot_error:
                print(f"Impossible de prendre capture d'écran générale: {screenshot_error}")
        return {
            "success": False,
            "product_name": "Non disponible",
            "brand": "Non disponible",
            "attributes": "Non trouvé",
            "price": "Non disponible",
            "price_per_unit": "Non trouvé",
            "nutri_score": "Non trouvé",
            "description": "Non trouvé",
            "ingredients": "Non trouvé",
            "conservation": "Non trouvé",
            "ean": "Non trouvé",
            "error": error_msg,
            "url": url
            }
    # =================== FINALLY BLOCK (Always Executes) ===================
    finally:
        if driver:
            print("Fermeture du WebDriver...")
            driver.quit()
            print("WebDriver fermé.")
        print("--- Fin du scraping ---")

# --- Script Execution ---
if __name__ == "__main__":
    url_produit = "https://www.auchan.fr/fleury-michon-jambon-le-torchon-reduit-en-sel/pr-C1215581"
    code_postal_paris = "75001"

    resultat = scrape_auchan_price(url_produit, postal_code=code_postal_paris, attente_initiale=5, timeout_duration=30)

    print("\n" + "="*60)
    print("          RÉSULTATS DU SCRAPING - AUCHAN")
    print("="*60)
    if resultat.get("success"):
        print(f"✅ Succès:          Oui")
        print(f"URL:               {resultat.get('url', 'N/A')}")
        print(f"Produit:           {resultat.get('product_name', 'Non trouvé')}")
        print(f"Marque:            {resultat.get('brand', 'Non trouvée')}")
        print(f"Attributs:         {resultat.get('attributes', 'Non trouvé')}")
        print(f"Prix:              {resultat.get('price', 'Non trouvé')}")
        print(f"Prix par Unité:    {resultat.get('price_per_unit', 'Non trouvé')}")
        print(f"Nutri-Score:       {resultat.get('nutri_score', 'Non trouvé')}")
        print(f"EAN:               {resultat.get('ean', 'Non trouvé')}")
        print(f"Conservation:      {resultat.get('conservation', 'Non trouvé')}")
        # Limit length of description/ingredients for cleaner output
        desc_short = resultat.get('description', 'Non trouvé')[:100] + '...' if len(resultat.get('description', '')) > 100 else resultat.get('description', 'Non trouvé')
        ingr_short = resultat.get('ingredients', 'Non trouvé')[:100] + '...' if len(resultat.get('ingredients', '')) > 100 else resultat.get('ingredients', 'Non trouvé')
        print(f"Description:       {desc_short}")
        print(f"Ingrédients:       {ingr_short}")
        print(f"Code Postal Utilisé: {resultat.get('postal_code_used', 'N/A')}")
    else:
        print(f"❌ Succès:          Non")
        print(f"URL:               {resultat.get('url', 'N/A')}")
        print(f"Produit:           {resultat.get('product_name', 'N/A')}")
        print(f"Erreur:            {resultat.get('error', 'Erreur inconnue')}")
    print("="*60)