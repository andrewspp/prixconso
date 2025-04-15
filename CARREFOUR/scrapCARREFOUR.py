from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import csv
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration CSV ---
CSV_FILENAME = 'carrefour_product_data.csv'
CSV_HEADERS = ['PostalCode', 'StoreName', 'PricePerUnit', 'ProductName']

def write_to_csv(data_row):
    """Fonction pour écrire une ligne de données dans le fichier CSV."""
    file_exists = os.path.isfile(CSV_FILENAME)
    try:
        with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists or os.path.getsize(CSV_FILENAME) == 0: # Vérifie aussi si le fichier est vide
                writer.writerow(CSV_HEADERS)
            writer.writerow(data_row)
        logging.info(f"Données écrites dans {CSV_FILENAME}: {data_row}")
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture dans le fichier CSV: {e}")

def visiter_produit_et_choisir_drive(
    product_url="https://www.carrefour.fr/p/neufchatel-au-lait-cru-aop-reflets-de-france-3560070753802",
    postal_code_to_search="05500"
):
    driver = None
    store_name = "N/A"
    price_per_unit = "N/A"
    product_name = "N/A"

    try:
        # --- Setup Chrome ---
        options = Options()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless")
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        logging.info("Configuration du WebDriver Chrome...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 25)
        short_wait = WebDriverWait(driver, 10)
        logging.info(f"Navigation vers la page produit: {product_url}")
        driver.get(product_url)

        # --- 1. Gérer les Cookies ---
        logging.info("Attente et gestion de la bannière de cookies...")
        try:
            cookies_button = wait.until(EC.element_to_be_clickable(
                (By.ID, "onetrust-accept-btn-handler")))
            driver.execute_script("arguments[0].click();", cookies_button)
            logging.info("Bouton de cookies cliqué via JS.")
            time.sleep(0.5)
        except TimeoutException:
            logging.warning("Bouton de cookies non trouvé ou pas cliquable.")
        except Exception as e:
            logging.error(f"Erreur cookies: {e}")

        # --- Extraire le nom du produit initial ---
        try:
            product_title_xpath = "//h1[contains(@class, 'product-title')]"
            product_title_element = wait.until(EC.presence_of_element_located((By.XPATH, product_title_xpath)))
            product_name = product_title_element.text.strip()
            logging.info(f"Nom du produit: '{product_name}'")
        except Exception as e:
            logging.warning(f"Impossible d'extraire le nom du produit: {e}")

        # --- 2. Cliquer "Voir les options d'achat" ---
        logging.info("Recherche 'Voir les options d'achat'...")
        try:
            options_button_xpath = "//button[contains(., 'Voir les options d')] | //a[contains(., 'Voir les options d')]"
            options_button = wait.until(EC.element_to_be_clickable((By.XPATH, options_button_xpath)))
            logging.info("Bouton 'Options' trouvé. Clic...")
            driver.execute_script("arguments[0].scrollIntoView(true);", options_button)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", options_button)
            logging.info("Bouton 'Options' cliqué via JS.")
            time.sleep(1)
        except TimeoutException:
            logging.error("Impossible de trouver/cliquer 'Voir les options d'achat'.")
            driver.save_screenshot("error_screenshot_options_button.png")
            raise
        except Exception as e:
            logging.error(f"Erreur clic 'Options': {e}")
            driver.save_screenshot("error_screenshot_options_click_error.png")
            raise


        # --- 3. Cliquer "Drive" dans Modale 1 ---
        logging.info("Attente modale 1 et recherche bouton 'Drive'...")
        try:
            drive_button_xpath = "//div[@role='dialog' or contains(@class, 'modal')]//button[contains(., 'Drive')]"
            drive_button = wait.until(EC.element_to_be_clickable((By.XPATH, drive_button_xpath)))
            logging.info("Bouton 'Drive' trouvé. Clic...")
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", drive_button)
            logging.info("Bouton 'Drive' cliqué via JS.")
            time.sleep(1.5)
        except TimeoutException:
            logging.error("Impossible de trouver/cliquer 'Drive' dans modale 1.")
            driver.save_screenshot("error_screenshot_drive_button_modal1.png")
            raise
        except Exception as e:
            logging.error(f"Erreur clic 'Drive': {e}")
            driver.save_screenshot("error_screenshot_drive_click_error.png")
            raise


        # --- 4. Interagir Modale 2 (Adresse) ---
        logging.info("Attente modale 2 (adresse)...")
        address_input_xpath = "//input[@placeholder='Ex: 34 rue de Monge, 75005']"
        try:
            logging.info(f"Attente champ saisie: {address_input_xpath}")
            address_input = wait.until(EC.visibility_of_element_located((By.XPATH, address_input_xpath)))
            logging.info("Champ saisie trouvé.")
            logging.info(f"Saisie code postal: {postal_code_to_search}")
            address_input.clear()
            address_input.send_keys(postal_code_to_search)
            logging.info("Code postal saisi.")
            time.sleep(1.5)
        except TimeoutException as e:
            logging.error(f"Timeout: Modale 2 ou champ input introuvable. {e}")
            driver.save_screenshot("error_screenshot_modal2_input_timeout.png")
            raise
        except Exception as e:
            logging.error(f"Erreur saisie adresse: {e}")
            driver.save_screenshot("error_screenshot_modal2_input_generic.png")
            raise


        # --- 5. Sélectionner la 2ème Suggestion (XPath très spécifique) ---
        logging.info("Attente et sélection de la 2ème suggestion (1ère adresse)...")
        modal_updated_indicator_xpath = "//*[contains(text(), 'magasins proposés')]"
        try:
            target_suggestion_button_xpath = ("//ul[contains(@class, 'c-autocomplete__suggestions')]//li[2]//button[contains(@class, 'c-autocomplete__suggestion-button')]")
            logging.info(f"Attente du bouton de la 2ème suggestion: {target_suggestion_button_xpath}")
            target_suggestion_button = wait.until(EC.element_to_be_clickable((By.XPATH, target_suggestion_button_xpath)))
            try:
                suggestion_text = target_suggestion_button.find_element(By.XPATH, "./ancestor::li[1]").text.strip()
                logging.info(f"Bouton de la 2ème suggestion trouvé et cliquable: '{suggestion_text}'")
            except Exception:
                logging.info("Bouton de la 2ème suggestion trouvé et cliquable (texte non récupéré).")

            logging.info("Tentative de clic sur le bouton de la suggestion...")
            # Prioriser JS click
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", target_suggestion_button)
            logging.info("Clic JS sur le bouton de suggestion effectué.")

            logging.info("Vérification de l'apparition de la liste des magasins...")
            wait.until(EC.visibility_of_element_located((By.XPATH, modal_updated_indicator_xpath)))
            logging.info("La liste des magasins est apparue.")

        except TimeoutException:
            # Si le JS click échoue à mettre à jour, tenter ActionChains
            logging.warning("La liste des magasins n'est pas apparue après le clic JS. Tentative avec ActionChains...")
            try:
                time.sleep(0.5)
                # Il faut parfois re-localiser l'élément avant ActionChains
                target_suggestion_button = wait.until(EC.element_to_be_clickable((By.XPATH, target_suggestion_button_xpath)))
                actions = ActionChains(driver)
                actions.move_to_element(target_suggestion_button).pause(0.2).click().perform()
                logging.info("Clic via ActionChains effectué.")
                wait.until(EC.visibility_of_element_located((By.XPATH, modal_updated_indicator_xpath)))
                logging.info("La liste des magasins est apparue après ActionChains.")
            except Exception as action_err:
                logging.error(f"Le clic ActionChains a aussi échoué ou la liste magasins n'est pas apparue: {action_err}")
                driver.save_screenshot("error_screenshot_modal2_suggestions_actionchains_fail.png")
                raise TimeoutException("Impossible de confirmer le clic sur la suggestion et la mise à jour de la modale.") from action_err
        except Exception as e:
            logging.error(f"Erreur lors de la sélection de la 2ème suggestion: {e}")
            driver.save_screenshot("error_screenshot_modal2_suggestions_generic.png")
            raise


        # --- 6. Cliquer sur le premier bouton "Choisir" ---
        logging.info("Recherche du premier bouton 'Choisir' dans la liste des magasins...")
        try:
            first_choose_button_xpath = "(//div[contains(@class, 'store-list')] | //ul[contains(@class, 'store-list')] | //div[@role='dialog'])//button[normalize-space()='Choisir'][1]"
            logging.info(f"Attente du premier bouton 'Choisir': {first_choose_button_xpath}")
            first_choose_button = wait.until(EC.element_to_be_clickable((By.XPATH, first_choose_button_xpath)))
            logging.info("Premier bouton 'Choisir' trouvé. Clic...")
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", first_choose_button)
            logging.info("Premier bouton 'Choisir' cliqué via JS.")

            modal_container_xpath = "//div[@role='dialog' and contains(., 'magasins proposés')]"
            logging.info("Attente de la disparition de la modale des magasins...")
            wait.until(EC.invisibility_of_element_located((By.XPATH, modal_container_xpath)))
            logging.info("Modale des magasins disparue.")
            time.sleep(2.0)  # Augmentation du délai pour s'assurer que la page est complètement chargée

        except TimeoutException:
            logging.error("Impossible de trouver/cliquer 'Choisir', ou la modale n'a pas disparu après.")
            driver.save_screenshot("error_screenshot_choose_button.png")
            raise
        except Exception as e:
            logging.error(f"Erreur lors du clic sur 'Choisir': {e}")
            driver.save_screenshot("error_screenshot_choose_click_error.png")
            raise

        # --- 7. Extraire le nom du magasin ---
        try:
            store_name_xpath = "//div[@id='data-service-crf-1']//div[contains(@class, 'delivery-choice__title-content')]"
            logging.info(f"Attente du nom du magasin sélectionné: {store_name_xpath}")
            store_name_element = wait.until(EC.visibility_of_element_located((By.XPATH, store_name_xpath)))
            store_name = store_name_element.text.strip()
            logging.info(f"Nom du magasin extrait: '{store_name}'")
        except Exception as e:
            logging.warning(f"Impossible d'extraire le nom du magasin: {e}")
            driver.save_screenshot("error_store_name.png")

        # --- 8. Extraire le prix par unité ---
        logging.info("Tentative d'extraction du prix par unité...")
        time.sleep(2)  # Attendre que la page soit complètement chargée
        
        try:
            # Méthode 0 (PRIORITAIRE): Extraire du JSON dans window.__INITIAL_STATE__
            logging.info("Extraction du prix depuis le JSON window.__INITIAL_STATE__")
            
            js_json_script = """
            try {
                const state = window.__INITIAL_STATE__;
                
                // Chercher l'EAN du produit à partir de l'URL actuelle
                const url = window.location.href;
                const eanMatch = url.match(/\\d{13}/);
                const ean = eanMatch ? eanMatch[0] : null;
                
                // Si nous avons trouvé l'EAN, chercher les détails du produit
                if (ean && state.vuex.analytics.indexedEntities.product && state.vuex.analytics.indexedEntities.product[ean]) {
                    const productData = state.vuex.analytics.indexedEntities.product[ean];
                    
                    // Chercher la première offre disponible
                    const offers = productData.attributes.offers[ean];
                    if (offers) {
                        const firstOfferId = Object.keys(offers)[0];
                        if (firstOfferId) {
                            const offer = offers[firstOfferId];
                            if (offer && offer.attributes && offer.attributes.price) {
                                return offer.attributes.price.perUnitLabel || null;
                            }
                        }
                    }
                }
                
                // Si on ne trouve pas avec l'approche structurée, on fait une recherche plus générique
                if (state.vuex.analytics.indexedEntities.offer) {
                    const offerEntities = state.vuex.analytics.indexedEntities.offer;
                    for (const offerId in offerEntities) {
                        const offer = offerEntities[offerId];
                        if (offer && offer.attributes && offer.attributes.price && offer.attributes.price.perUnitLabel) {
                            return offer.attributes.price.perUnitLabel;
                        }
                    }
                }
                
                return null;
            } catch (e) {
                console.error("Erreur lors de l'extraction JSON:", e);
                return null;
            }
            """
            price_per_unit_json = driver.execute_script(js_json_script)
            
            if price_per_unit_json:
                price_per_unit = price_per_unit_json
                logging.info(f"Prix extrait du JSON: '{price_per_unit}'")
            else:
                raise Exception("Pas de prix trouvé dans le JSON")
                
        except Exception as json_err:
            logging.warning(f"Échec extraction JSON: {json_err}")
            
            # Méthodes alternatives
            logging.info("Tentative avec méthodes alternatives...")
            try:
                # Méthode 1: XPath
                price_per_unit_xpath = "//p[contains(@class, 'product-title__per-unit-label')]"
                price_per_unit_element = driver.find_element(By.XPATH, price_per_unit_xpath)
                price_per_unit = price_per_unit_element.text.strip()
                logging.info(f"Prix extrait via XPath: '{price_per_unit}'")
            except Exception as xpath_err:
                logging.warning(f"Échec XPath: {xpath_err}")
                
                try:
                    # Méthode 2: CSS Selector
                    css_selector = "p.product-title__per-unit-label"
                    price_per_unit_element = driver.find_element(By.CSS_SELECTOR, css_selector)
                    price_per_unit = price_per_unit_element.text.strip()
                    logging.info(f"Prix extrait via CSS: '{price_per_unit}'")
                except Exception as css_err:
                    logging.warning(f"Échec CSS: {css_err}")
                    
                    try:
                        # Méthode 3: JavaScript
                        js_script = """
                        var elements = document.getElementsByClassName('product-title__per-unit-label');
                        if (elements && elements.length > 0) {
                            return elements[0].textContent.trim();
                        } else {
                            return "Non trouvé via JS";
                        }
                        """
                        price_per_unit = driver.execute_script(js_script)
                        logging.info(f"Prix extrait via JS: '{price_per_unit}'")
                        
                        if price_per_unit == "Non trouvé via JS":
                            # Méthode 4: Contenu
                            try:
                                euro_element_xpath = "//*[contains(text(), '€ / L') or contains(text(), '€/L')]"
                                euro_element = driver.find_element(By.XPATH, euro_element_xpath)
                                price_per_unit = euro_element.text.strip()
                                logging.info(f"Prix trouvé par contenu: '{price_per_unit}'")
                            except Exception as content_err:
                                logging.error(f"Échec méthode contenu: {content_err}")
                                price_per_unit = "N/A (extraction impossible)"
                                driver.save_screenshot("error_price_extraction_failed.png")
                    except Exception as js_err:
                        logging.error(f"Échec méthode JS: {js_err}")
                        price_per_unit = "N/A (extraction impossible)"
                        driver.save_screenshot("error_price_extraction_failed.png")

        # --- 9. Sauvegarde CSV ---
        data_to_save = [postal_code_to_search, store_name, price_per_unit, product_name]
        write_to_csv(data_to_save)
        logging.info("Données enregistrées dans le CSV.")

        # --- 10. Attente finale ---
        logging.info("Script terminé avec succès.")
        time.sleep(2)

    # --- Gestion Erreurs et Finally ---
    except Exception as e:
        logging.critical(f"Une erreur générale et inattendue s'est produite: {e}")
        if store_name != "N/A" or price_per_unit != "N/A":
            logging.info("Tentative de sauvegarde des données partielles avant de quitter...")
            data_to_save = [postal_code_to_search, store_name, price_per_unit, product_name]
            write_to_csv(data_to_save)
        if driver:
            try:
                driver.save_screenshot("error_screenshot_critical.png")
                logging.info("Screenshot 'error_screenshot_critical.png' sauvegardé.")
            except Exception as screen_err:
                logging.error(f"Impossible de prendre le screenshot final: {screen_err}")
    finally:
        if driver:
            driver.quit()
            logging.info("Navigateur fermé.")

# --- Exécution ---
if __name__ == "__main__":
    visiter_produit_et_choisir_drive()