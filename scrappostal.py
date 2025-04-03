# -*- coding: utf-8 -*- # Add this line for better encoding support
import time
import re # Import regular expression module for parsing
import csv # Import CSV module for file writing
import os # To check if file exists for header writing
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
# List of postal codes to test (you can expand this list)
POSTAL_CODES_TO_TEST = [
    "75001", # Paris 1er
    "13001", # Marseille 1er
    "69001", # Lyon 1er
    "59000", # Lille
    "31000", # Toulouse
    "33000", # Bordeaux
    "44000", # Nantes
    "06000", # Nice
    "67000", # Strasbourg
    "34000", # Montpellier
    # Add more postal codes here as needed
    # "92100", # Boulogne-Billancourt (Example IDF)
    # "29200", # Brest (Example Bretagne)
]

# Output CSV file name
CSV_FILENAME = "auchan_prix_multi_cp.csv"

# URL of the product to scrape
URL_PRODUIT = "https://www.auchan.fr/fleury-michon-jambon-le-torchon-reduit-en-sel/pr-C1215581"

# --- Scraping Function (Modified slightly for clarity) ---
def scrape_auchan_price(url, postal_code, attente_initiale=5, timeout_duration=30):
    """
    Scrape le prix et les informations d'un produit Auchan en utilisant un code postal spécifique.
    Prioritise la sélection du premier point relais/magasin trouvé.
    Returns a dictionary with scraped data or error information.
    """
    print(f"\n--- Début du scraping pour CP {postal_code} ---")
    print(f"URL: {url}")

    options = Options()
    # options.add_argument("--headless") # Uncomment for headless mode
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument('--log-level=3') # Suppress unnecessary logs
    options.add_argument('--disable-gpu') # Often needed for headless
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    options.add_argument('--lang=fr-FR') # Try setting language

    driver = None
    screenshot_suffix = f"cp_{postal_code}" # Suffix for screenshots specific to this postal code

    try:
        print(f"[{postal_code}] Initialisation du WebDriver Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, timeout_duration) # General wait
        print(f"[{postal_code}] WebDriver initialisé.")

        print(f"[{postal_code}] Chargement de l'URL: {url}")
        driver.get(url)
        print(f"[{postal_code}] Page chargée. Attente initiale ({attente_initiale}s)...")
        time.sleep(attente_initiale)

        # Accepter les cookies
        try:
            print(f"[{postal_code}] Recherche du bouton cookies...")
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print(f"[{postal_code}] Cookies acceptés.")
            time.sleep(1)
        except TimeoutException:
            print(f"[{postal_code}] Pas de popup de cookies trouvée ou déjà acceptée.")
        except Exception as e:
            print(f"[{postal_code}] Erreur lors de l'acceptation des cookies: {e}")

        # --- Logique principale ---
        try:
            # 1. Find and click the button to open the location modal
            show_price_button_xpath = "//button[contains(., 'Afficher le prix') or contains(., 'Choisir mon magasin') or contains(., 'Retrait') or contains(., 'Livraison') or contains(@data-testid, 'delivery-method') or contains(@class, 'context-button')]" # Added context-button
            print(f"[{postal_code}] Recherche du bouton de localisation via XPath...")
            show_price_button = wait.until(EC.element_to_be_clickable((By.XPATH, show_price_button_xpath)))
            print(f"[{postal_code}] Bouton trouvé: '{show_price_button.text}'. Clic...")
            # Use JavaScript click for robustness
            driver.execute_script("arguments[0].click();", show_price_button)
            print(f"[{postal_code}] Bouton cliqué. Attente de l'ouverture du modal/popup...")
            time.sleep(3) # Wait for modal animation/loading

            # 2. Find the postal code input field
            postal_input_selectors = [
                "input[placeholder*='postal']", "input[name*='postal']", "input[id*='postal']",
                "input[data-testid*='postal']", "input#search-input", "input[aria-label*='postal']",
                "input.journeySearchInput"
            ]
            postal_input = None
            postal_wait = WebDriverWait(driver, 15) # Wait specifically for the input
            for selector in postal_input_selectors:
                try:
                    print(f"[{postal_code}] Tentative de trouver le champ postal avec le sélecteur CSS: {selector}")
                    postal_input = postal_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"[{postal_code}] Champ de code postal trouvé.")
                    break
                except TimeoutException:
                    print(f"[{postal_code}] Sélecteur '{selector}' n'a pas fonctionné.")
                    continue
            if not postal_input:
                print(f"[{postal_code}] ERREUR: Impossible de trouver le champ de saisie du code postal.")
                driver.save_screenshot(f"error_postal_input_not_found_{screenshot_suffix}.png")
                raise TimeoutException("Impossible de trouver le champ de saisie du code postal.")

            # 3. Enter postal code and select suggestion
            print(f"[{postal_code}] Saisie du code postal '{postal_code}'...")
            postal_input.clear()
            postal_input.send_keys(postal_code)
            print(f"[{postal_code}] Attente des suggestions de localisation...")
            time.sleep(2.5) # Allow time for suggestions to appear

            # Try clicking the first suggestion
            first_suggestion_xpath = f"//ul[contains(@class, 'journey__search-suggests-list') and not(contains(@class, 'hidden'))]//li[contains(.,'{postal_code}')][1]"
            suggestion_clicked = False
            try:
                 suggestion_wait = WebDriverWait(driver, 10)
                 print(f"[{postal_code}] Recherche de la première suggestion...")
                 first_suggestion = suggestion_wait.until(EC.element_to_be_clickable((By.XPATH, first_suggestion_xpath)))
                 suggestion_text = first_suggestion.text.strip().replace('\n', ' ')
                 print(f"[{postal_code}] Première suggestion trouvée: '{suggestion_text}'. Clic...")
                 # Scroll and JS click
                 driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_suggestion)
                 time.sleep(0.5)
                 driver.execute_script("arguments[0].click();", first_suggestion)
                 suggestion_clicked = True
                 print(f"[{postal_code}] Suggestion cliquée. Attente de l'affichage de la liste des magasins...")
                 time.sleep(4) # Wait for store list to load after suggestion click
            except TimeoutException:
                 print(f"[{postal_code}] WARN: Aucune suggestion cliquable trouvée pour '{postal_code}'. Tentative Entrée.")
                 try:
                    postal_input.send_keys(Keys.ENTER)
                    print(f"[{postal_code}] Touche Entrée envoyée. Attente...")
                    suggestion_clicked = True # Assume Enter worked for now
                    time.sleep(5) # Longer wait after Enter key
                 except Exception as e_enter:
                     print(f"[{postal_code}] INFO: Échec de l'envoi de la touche Entrée: {e_enter}. Le script essaiera quand même de trouver la liste.")
                     suggestion_clicked = False # Enter failed, may still work if list loaded previously

            # =================== SECTION SELECTION MAGASIN ===================
            store_selected = False
            selected_store_name = "Non sélectionné"
            print(f"[{postal_code}] Attente (max 20s) de l'apparition de la liste des magasins/points relais...")
            store_list_wait = WebDriverWait(driver, 20)
            store_container_base_xpath = "//div[contains(@class, 'journey-offering-context__wrapper') and contains(@class, 'journeyPosItem')]" # Main container for each store/point

            try:
                # Wait for at least one store item to be present
                print(f"[{postal_code}] Attente du premier élément de la liste via XPath...")
                store_list_wait.until(
                    EC.presence_of_element_located((By.XPATH, store_container_base_xpath))
                )
                print(f"[{postal_code}] Au moins un magasin/point relais détecté. Recherche de la liste complète...")
                # Give it a slight pause to ensure all items render if dynamically loaded
                time.sleep(1.5)
                store_containers = driver.find_elements(By.XPATH, store_container_base_xpath)
                print(f"[{postal_code}] Liste des magasins/points relais trouvée ({len(store_containers)} éléments).")

                if store_containers:
                    # Iterate through found stores/points and try to select the first available one
                    for i, container in enumerate(store_containers):
                        store_name_current = f"Magasin/Point #{i+1} (Nom non trouvé)"
                        is_available = True

                        # Try to get the name
                        try:
                            name_el = container.find_element(By.XPATH, ".//span[contains(@class, 'place-pos__name')]")
                            store_name_current = name_el.text.strip().replace('\n', ' ')
                        except NoSuchElementException:
                             print(f"[{postal_code}] WARN: Impossible de trouver le nom pour l'item #{i+1}.")

                        # Check for unavailability indicators
                        try:
                             # Check for specific "Pas de créneau" text
                             container.find_element(By.XPATH, ".//span[contains(@class, 'no-slot-info') and contains(normalize-space(), 'Pas de créneau disponible')]")
                             print(f"[{postal_code}] -> '{store_name_current}' (item {i+1}) est INDISPONIBLE (texte 'Pas de créneau').")
                             is_available = False
                        except NoSuchElementException:
                             # Check if the 'Choisir' button is disabled (another indicator)
                             try:
                                 choose_button_check = container.find_element(By.XPATH, ".//button[contains(@class, 'btnJourneySubmit') and normalize-space()='Choisir']")
                                 if not choose_button_check.is_enabled():
                                     print(f"[{postal_code}] -> '{store_name_current}' (item {i+1}) est INDISPONIBLE (bouton 'Choisir' désactivé).")
                                     is_available = False
                                 #else: button is present and enabled, likely available
                             except NoSuchElementException:
                                 # If the button itself is missing, treat as unavailable for safety
                                 print(f"[{postal_code}] -> '{store_name_current}' (item {i+1}) est INDISPONIBLE (bouton 'Choisir' non trouvé).")
                                 is_available = False

                        # If available, try to click 'Choisir'
                        if is_available:
                            print(f"[{postal_code}] -> '{store_name_current}' (item {i+1}) semble DISPONIBLE. Tentative de sélection...")
                            try:
                                choose_button = container.find_element(By.XPATH, ".//button[contains(@class, 'btnJourneySubmit') and normalize-space()='Choisir']")
                                # Scroll button into view
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", choose_button)
                                time.sleep(1) # Wait after scroll

                                # Wait for button to be truly clickable
                                button_wait = WebDriverWait(driver, 10)
                                choose_button_clickable = button_wait.until(
                                    EC.element_to_be_clickable(choose_button)
                                )
                                print(f"[{postal_code}] Bouton 'Choisir' pour '{store_name_current}' est cliquable. Clic...")
                                driver.execute_script("arguments[0].click();", choose_button_clickable) # JS Click
                                store_selected = True
                                selected_store_name = store_name_current
                                print(f"[{postal_code}] Magasin '{selected_store_name}' sélectionné avec succès.")
                                break # Exit the loop once a store is selected
                            except (NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as e_click:
                                print(f"[{postal_code}]    WARN: Impossible de cliquer sur 'Choisir' pour '{store_name_current}': {type(e_click).__name__}. Essai du suivant.")
                                # Continue to the next container in the loop
                        else:
                            # Just continue to the next container if not available
                            continue

                else:
                    # This case should ideally not happen if the initial wait succeeded, but handle it
                    print(f"[{postal_code}] ERREUR: Aucun conteneur de magasin trouvé via find_elements après la détection initiale.")
                    driver.save_screenshot(f"error_no_store_containers_post_wait_{screenshot_suffix}.png")
                    raise NoSuchElementException("Aucun conteneur de magasin trouvé (post-wait).")

            except TimeoutException:
                # This catches the timeout waiting for the *first* store item
                print(f"[{postal_code}] ERREUR: La liste des magasins n'est pas apparue dans le délai imparti.")
                driver.save_screenshot(f"error_store_list_timeout_{screenshot_suffix}.png")
                raise TimeoutException("Timeout en attendant la liste des magasins/points relais.")
            except Exception as e_list:
                print(f"[{postal_code}] ERREUR inattendue lors du traitement de la liste des magasins: {type(e_list).__name__} - {e_list}")
                driver.save_screenshot(f"error_store_list_processing_{screenshot_suffix}.png")
                raise # Re-raise the unexpected error

            # Check if a store was successfully selected
            if not store_selected:
                print(f"[{postal_code}] ERREUR: Aucun magasin/point relais disponible n'a pu être sélectionné pour le CP {postal_code}.")
                driver.save_screenshot(f"error_no_store_selected_{screenshot_suffix}.png")
                raise TimeoutException(f"Échec final de la sélection d'un magasin pour CP {postal_code}.")
            else:
                 print(f"[{postal_code}] Sélection du magasin '{selected_store_name}' réussie. Attente de la mise à jour de la page produit (5s)...")
                 time.sleep(5) # Crucial wait for page/price update after selection

            # =================== FIN SECTION SELECTION MAGASIN ===================

            # 6. Récupérer Prix final et Prix au Kilo/Unité
            print(f"[{postal_code}] Tentative de récupération des prix...")
            price_final = "Non trouvé"
            price_per_unit = "Non trouvé"
            # Use a more specific container if possible, otherwise keep the general one
            price_container_xpath = "//div[contains(@class,'product-price--main') or contains(@class,'default-price')]" # Added main price container

            try:
                price_wait = WebDriverWait(driver, 15)
                price_container = price_wait.until(
                    EC.visibility_of_element_located((By.XPATH, price_container_xpath))
                )
                print(f"[{postal_code}] Conteneur de prix principal trouvé.")

                # Prix final
                try:
                    # Try common patterns for the main price
                    price_final_element = price_container.find_element(By.XPATH, ".//div[contains(@class,'product-price--large')] | .//span[@data-price]") # Added span data-price
                    raw_price = price_final_element.text.strip()
                    if not raw_price: # Check if text is empty, maybe price is in attribute
                        raw_price = price_final_element.get_attribute('data-price') or price_final_element.get_attribute('content')

                    # Clean up the price (remove currency symbols, spaces, use dot as decimal)
                    if raw_price:
                        price_final = re.sub(r'[^\d,.]', '', raw_price).replace(',', '.').strip()
                        if price_final and price_final != '.': # Ensure it's not empty or just a dot
                             print(f"[{postal_code}] Prix final trouvé: {price_final} €")
                        else: price_final = "Format Invalide"
                    else:
                        price_final = "Non trouvé (vide)"

                except NoSuchElementException:
                    print(f"[{postal_code}] WARN: Prix final (large/data-price) non trouvé DANS le conteneur.")
                    price_final = "Non trouvé"

                # Prix au Kilo/Unité
                try:
                    price_per_unit_element = price_container.find_element(By.XPATH, ".//div[contains(@class,'product-price--smaller')]/span | .//div[contains(@class,'product-price__pricePerKilogram')]") # Added kilogram class
                    price_per_unit = price_per_unit_element.text.strip().replace('\n', ' ')
                    if price_per_unit:
                        print(f"[{postal_code}] Prix par unité trouvé: {price_per_unit}")
                    else: price_per_unit = "Non trouvé (vide)"
                except NoSuchElementException:
                    print(f"[{postal_code}] WARN: Prix par unité (smaller/kilogram) non trouvé DANS le conteneur.")
                    price_per_unit = "Non trouvé"

            except TimeoutException:
                print(f"[{postal_code}] ERREUR: Conteneur de prix principal ({price_container_xpath}) non trouvé ou non visible après sélection du magasin.")
                driver.save_screenshot(f"error_price_container_not_found_{screenshot_suffix}.png")
                # Keep default "Non trouvé" values

            # Raise error only if *neither* price was found (or format was invalid)
            if price_final in ["Non trouvé", "Format Invalide", "Non trouvé (vide)"] and price_per_unit in ["Non trouvé", "Non trouvé (vide)"]:
                 print(f"[{postal_code}] ERREUR: Impossible de trouver les éléments de prix valides sur la page finale.")
                 # Don't raise an exception here, let it return failure in the dict
                 # We want to record the failure in the CSV

            # 7. Récupérer les informations additionnelles
            print(f"[{postal_code}] Récupération des informations additionnelles...")
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
                 print(f"[{postal_code}] Nom produit: {product_name}")
            except TimeoutException:
                 print(f"[{postal_code}] WARN: Titre H1 (nom produit) non trouvé.")

            # Brand (Try different methods)
            try:
                # Method 1: Meta tag
                brand = driver.find_element(By.XPATH, "//meta[@itemprop='brand']").get_attribute('content').strip()
            except NoSuchElementException:
                try:
                   # Method 2: Specific class (adjust if needed)
                   brand_element = driver.find_element(By.XPATH, "//a[contains(@href, '/marques/')] | //div[contains(@class,'brand-logo')]//img[@alt]") # Common patterns
                   brand = brand_element.text.strip() if brand_element.text.strip() else brand_element.get_attribute('alt').strip() # Use text or alt
                   if not brand: brand = "Marque Inconnue (méthode 2 échouée)"
                except NoSuchElementException:
                   print(f"[{postal_code}] WARN: Marque non trouvée (ni meta, ni lien/logo).")
                   brand = "Marque Inconnue"
            print(f"[{postal_code}] Marque: {brand}")


            # Attributes (Weight, Slices etc.) - Often near title or price
            try:
                attr_container = driver.find_element(By.XPATH, "//div[contains(@class,'product-title__package') or contains(@class,'offer-selector__attributes')]") # Common containers
                attributes_list = [elem.text.strip() for elem in attr_container.find_elements(By.XPATH, ".//span") if elem.text.strip()] # Find spans inside
                attributes = " | ".join(attributes_list) if attributes_list else "Non trouvé"
            except NoSuchElementException:
                 print(f"[{postal_code}] WARN: Section attributs (poids/quantité) non trouvée.")
            print(f"[{postal_code}] Attributs: {attributes}")

            # Nutri-Score
            try:
                nutri_img = driver.find_element(By.XPATH, "//div[contains(@class,'product-nutriscore')]/img | //img[contains(@src,'nutriscore')]") # Find image by class or src
                alt_text = nutri_img.get_attribute('alt') or nutri_img.get_attribute('title') or "" # Check alt and title
                match = re.search(r'[Nn]utri-?[Ss]core\s*:?\s*([A-E])', alt_text, re.IGNORECASE) # More robust regex
                if match:
                    nutri_score = match.group(1).upper()
                else:
                    # Fallback: Try extracting from src if alt failed
                    src_text = nutri_img.get_attribute('src') or ""
                    match_src = re.search(r'/([A-E])\.(?:svg|png|jpg)', src_text, re.IGNORECASE)
                    if match_src:
                        nutri_score = match_src.group(1).upper()
                    else:
                        print(f"[{postal_code}] WARN: Lettre Nutri-Score non trouvée dans alt ('{alt_text}') ou src ('{src_text}').")
                        nutri_score = "Non trouvé (Format?)"
            except NoSuchElementException:
                 print(f"[{postal_code}] WARN: Image Nutri-Score non trouvée.")
            print(f"[{postal_code}] Nutri-Score: {nutri_score}")


            # --- Extracting from Description Section (Handles potential accordion clicks) ---
            description_section_xpath = "//div[@id='product-features' or contains(@class,'description-bloc-content')]" # Common description sections
            try:
                # Wait for the description section container
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, description_section_xpath)))
                desc_section_element = driver.find_element(By.XPATH, description_section_xpath)

                # Function to find text based on a preceding label/header
                def get_feature_value(driver, base_element, label_texts):
                    for label_text in label_texts:
                        try:
                            # Look for a header/label element containing the text
                            # Then find the following sibling div/span with the value
                            # This handles various structures like h5/div or span/div
                            xpath = f".//(*[self::h5 or self::h6 or self::span or self::dt][contains(.,'{label_text}')]/following-sibling::*[self::div or self::dd][1]/*[self::span[contains(@class,'value')] or self::p] | .//div[contains(@class,'feature')][.//span[contains(@class,'label')][contains(.,'{label_text}')]]//span[contains(@class,'value')])"
                            value_element = base_element.find_element(By.XPATH, xpath)
                            value = value_element.text.strip()
                            if value: return value
                        except NoSuchElementException:
                            continue # Try next label text
                    return "Non trouvé" # Return not found if none of the labels work

                # Description
                description = get_feature_value(driver, desc_section_element, ["Description"])
                print(f"[{postal_code}] Description trouvée: {'Oui' if description != 'Non trouvé' else 'Non'}")

                # Ingredients
                ingredients = get_feature_value(driver, desc_section_element, ["Ingrédients", "Ingr", "Composition"])
                print(f"[{postal_code}] Ingrédients trouvés: {'Oui' if ingredients != 'Non trouvé' else 'Non'}")

                # Conservation
                conservation = get_feature_value(driver, desc_section_element, ["Conditions particul", "Conservation", "Mode d'emploi"])
                print(f"[{postal_code}] Conservation trouvée: {'Oui' if conservation != 'Non trouvé' else 'Non'}")

                # EAN
                ean_raw = get_feature_value(driver, desc_section_element, ["EAN", "Code article", "Gencode"])
                if ean_raw != "Non trouvé":
                     ean_match = re.search(r'\b(\d{13})\b', ean_raw) # Look for 13 digits
                     if ean_match:
                         ean = ean_match.group(1)
                     else:
                         ean = ean_raw # Keep raw value if no 13 digits found
                print(f"[{postal_code}] EAN trouvé: {ean}")

            except TimeoutException:
                 print(f"[{postal_code}] WARN: Section description/caractéristiques principale ({description_section_xpath}) non trouvée.")
            except NoSuchElementException:
                 print(f"[{postal_code}] WARN: Problème lors de la recherche d'éléments dans la section description.")
            except Exception as e_desc:
                 print(f"[{postal_code}] ERREUR inattendue lors de l'extraction de la description: {type(e_desc).__name__} - {e_desc}")


            # 8. Return Results
            print(f"[{postal_code}] Scrapping terminé avec succès pour ce CP.")
            return {
                "success": True,
                "postal_code_used": postal_code,
                "selected_store": selected_store_name,
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
                "url": url,
                "error": None # Explicitly None for success
            }

        # =================== ERROR HANDLING FOR MAIN PROCESS ===================
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, ValueError) as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"[{postal_code}] ERREUR lors du processus principal : {error_msg}")
            error_screenshot_path = f"error_process_{type(e).__name__}_{screenshot_suffix}.png"
            try:
                driver.save_screenshot(error_screenshot_path)
                print(f"[{postal_code}] Capture d'écran '{error_screenshot_path}' prise.")
            except Exception as ss_err:
                 print(f"[{postal_code}] Impossible de prendre capture d'écran d'erreur: {ss_err}")

            # Try to get product name even on failure for context
            product_name_fallback = "Nom non récupéré"
            try:
                 h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                 if h1_elements: product_name_fallback = h1_elements[0].text.strip()
            except: pass

            return {
                "success": False,
                "postal_code_used": postal_code,
                "selected_store": "Non sélectionné (Erreur)",
                "product_name": product_name_fallback,
                "brand": "Non récupérée",
                "attributes": "Non trouvé",
                "price": "Erreur",
                "price_per_unit": "Erreur",
                "nutri_score": "Non trouvé",
                "description": "Non trouvé",
                "ingredients": "Non trouvé",
                "conservation": "Non trouvé",
                "ean": "Non trouvé",
                "url": url,
                "error": error_msg # Include the error message
                }
    # =================== GENERAL ERROR HANDLING ===================
    except Exception as e:
        error_msg = f"Erreur générale non interceptée pour CP {postal_code}: {type(e).__name__} - {e}"
        print(error_msg)
        if driver:
            try:
                driver.save_screenshot(f"general_error_screenshot_{screenshot_suffix}.png")
                print(f"[{postal_code}] Capture d'écran 'general_error_screenshot_{screenshot_suffix}.png' prise.")
            except Exception as screenshot_error:
                print(f"[{postal_code}] Impossible de prendre capture d'écran générale: {screenshot_error}")
        return {
            "success": False,
            "postal_code_used": postal_code,
            "selected_store": "Non sélectionné (Erreur Générale)",
            "product_name": "Erreur Générale",
            "brand": "Erreur Générale",
            "attributes": "Erreur",
            "price": "Erreur",
            "price_per_unit": "Erreur",
            "nutri_score": "Erreur",
            "description": "Erreur",
            "ingredients": "Erreur",
            "conservation": "Erreur",
            "ean": "Erreur",
            "url": url,
            "error": error_msg
            }
    # =================== FINALLY BLOCK (Always Executes) ===================
    finally:
        if driver:
            print(f"[{postal_code}] Fermeture du WebDriver...")
            driver.quit()
            print(f"[{postal_code}] WebDriver fermé.")
        print(f"--- Fin du scraping pour CP {postal_code} ---")

# --- Main Script Execution Logic ---
if __name__ == "__main__":
    all_results = []
    print(f"Lancement du scraping pour {len(POSTAL_CODES_TO_TEST)} codes postaux...")
    print(f"Produit cible: {URL_PRODUIT}")
    print(f"Les résultats seront sauvegardés dans: {CSV_FILENAME}")

    # Loop through each postal code
    for cp in POSTAL_CODES_TO_TEST:
        result = scrape_auchan_price(URL_PRODUIT, postal_code=cp, attente_initiale=5, timeout_duration=45) # Increased timeout slightly
        all_results.append(result)
        print(f"Résultat pour {cp} ajouté. Pause de 2 secondes...")
        time.sleep(2) # Small delay between requests to be polite

    # --- Write results to CSV ---
    if not all_results:
        print("Aucun résultat n'a été collecté. Le fichier CSV ne sera pas créé.")
    else:
        # Define the headers based on the dictionary keys (ensure consistency)
        # It's safer to define them explicitly to control the order and ensure all columns are present
        fieldnames = [
            "success", "postal_code_used", "selected_store", "product_name", "brand",
            "attributes", "price", "price_per_unit", "nutri_score", "ean",
            "description", "ingredients", "conservation", "url", "error"
        ]

        # Check if file exists to write header only once
        file_exists = os.path.isfile(CSV_FILENAME)

        print(f"\nÉcriture des {len(all_results)} résultats dans {CSV_FILENAME}...")
        try:
            with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as csvfile: # Use 'a' to append
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)

                # Write header only if the file is new or empty
                if not file_exists or os.path.getsize(CSV_FILENAME) == 0:
                    writer.writeheader()
                    print("En-tête CSV écrit.")

                # Write the data rows
                for row_data in all_results:
                    # Ensure all keys exist in the dictionary, adding missing ones with a default value if necessary
                    # (Our function should already return all keys, but this is safer)
                    for key in fieldnames:
                        row_data.setdefault(key, 'N/A')
                    writer.writerow(row_data)

            print(f"Écriture terminée avec succès dans {CSV_FILENAME}")

        except IOError as e:
            print(f"ERREUR: Impossible d'écrire dans le fichier CSV {CSV_FILENAME}. Erreur: {e}")
        except Exception as e:
             print(f"ERREUR inattendue lors de l'écriture CSV: {type(e).__name__} - {e}")

    print("\nScript terminé.")