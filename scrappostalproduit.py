# -*- coding: utf-8 -*-
import time
import re
import csv
import os
import concurrent.futures # Ajout pour la parallélisation
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    ElementNotInteractableException, StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---

# List of product URLs to scrape (Generated List)
PRODUCT_URLS = [
    # == Produits Frais ==
    "https://www.auchan.fr/fleury-michon-jambon-le-torchon-reduit-en-sel/pr-C1215581", # Jambon
    "https://www.auchan.fr/auchan-bio-oeufs-de-poules-elevees-en-plein-air/pr-C1171259", # Œufs Bio
    "https://www.auchan.fr/president-camembert-au-lait-pasteurise/pr-C1180565", # Fromage
    "https://www.auchan.fr/auchan-yaourt-nature/pr-C1177759", # Yaourt nature
    "https://www.auchan.fr/auchan-filets-de-poulet-blanc/pr-C1164797", # Filet de poulet
    "https://www.auchan.fr/carottes/pr-C1348314", # Carottes

    # == Épicerie ==
    "https://www.auchan.fr/barilla-spaghetti-n5/pr-C1241472", # Pâtes
    "https://www.auchan.fr/lustucru-riz-long-grain-incollable-pret-en-10-min/pr-C1624714", # Riz
    "https://www.auchan.fr/nutella-pate-a-tartiner-aux-noisettes/pr-C1266974", # Nutella
    "https://www.auchan.fr/carte-noire-cafe-moulu-pur-arabica-arome-intense/pr-C1264820", # Café moulu

    # == Boissons ==
    "https://www.auchan.fr/coca-cola-boisson-gazeuse-aux-extraits-vegetaux-gout-original/pr-C1211988", # Coca-Cola
    "https://www.auchan.fr/cristaline-eau-de-source-plate/pr-C1222322", # Eau Cristaline
    "https://www.auchan.fr/auchan-pur-jus-d-orange-sans-pulpe/pr-C1207658", # Jus d'orange

    # == Hygiène / Entretien ==
    "https://www.auchan.fr/colgate-total-dentifrice-classique/pr-C1565048", # Dentifrice
    "https://www.auchan.fr/ariel-lessive-liquide-original/pr-C1763569", # Lessive liquide

    # == Surgelés ==
    "https://www.auchan.fr/buitoni-pizza-la-grandiosa-4-fromages/pr-C1174261", # Pizza surgelée
]

POSTAL_CODE_CATEGORIES = {
    "Grande Ville": ["13003", "13008", "13009", "13010", "13011", "13012", "13013", "13090", "31000", "31170", "31200", "31400", "33000", "33130", "33140", "33170", "33200", "33270", "33300", "33400", "33600", "33700", "34070", "44230", "44600", "44800", "54000", "57000", "57050", "57070", "59000", "59139", "59300", "59650", "59790", "59810", "67000", "67200", "67300", "67400", "69003", "69005", "69006", "69007", "69300", "69800", "75002", "75005", "75011", "75012", "75013", "75014", "75015", "75017", "75019", "75020", "77000", "78140", "78310", "78370", "78500", "78700", "91140", "91220", "91300", "91400", "92100", "92120", "92130", "92160", "92250", "92260", "92320", "92330", "92500", "92600", "92800", "93130", "93160", "93170", "93230", "93290", "93300", "93370", "93420", "93800", "94000", "94120", "94200", "94270", "94370", "94400", "94420", "94700", "95000", "95100", "95130", "95200", "95230", "95400", "95520", "95600"],
    "Ville Moyenne": ["02100", "06130", "06600", "11000", "11100", "13200", "13400", "14200", "15000", "16100", "19100", "20200", "21000", "26000", "26200", "30900", "31140", "31150", "31800", "31830", "34200", "37000", "37170", "38090", "38500", "38600", "42000", "42390", "45100", "45140", "45160", "46000", "49000", "49100", "49240", "51100", "54510", "54520", "59320", "59400", "60000", "60200", "60400", "62100", "62300", "62400", "63000", "63110", "63170", "64140", "64320", "65000", "66000", "68920", "69400", "71000", "72650", "73300", "74600", "76200", "76290", "76620", "77240", "78100", "78150", "78190", "78200", "78800", "80480", "80800", "81100", "82000", "83160", "83200", "83400", "83500", "83600", "83700", "84000", "84130", "84300", "86100", "86360", "88000", "89000", "90160"],
    "Petite Ville": ["01090", "02300", "02500", "03410", "04100", "04160", "04300", "05000", "06140", "06150", "06160", "06200", "06210", "06340", "06370", "07500", "10600", "13150", "13230", "13500", "13530", "13560", "13740", "13800", "14123", "14880", "16400", "16430", "18000", "20100", "20110", "20137", "20167", "20220", "20230", "20250", "20260", "20600", "24120", "24650", "26120", "26400", "26800", "27140", "27600", "27670", "30129", "33240", "33290", "33370", "33380", "34470", "34500", "34790", "36330", "37250", "37540", "38190", "38420", "38510", "41350", "42330", "43700", "44570", "45143", "45150", "45500", "47300", "50470", "54350", "57280", "59115", "59134", "59155", "59223", "59310", "59380", "59450", "59494", "59520", "59720", "59760", "59880", "60110", "60180", "60220", "62161", "62210", "62280", "62575", "62610", "62950", "62980", "63118", "63730", "66200", "67190", "67210", "67520", "67590", "69170", "69570", "69580", "69630", "70300", "71700", "73500", "74120", "74330", "76330", "76380", "77124", "77310", "77700", "78250", "78480", "80350", "83110", "83170", "83220", "83230", "83250", "83330", "86240", "88190", "91230", "91250"],
    "Campagne": ["04120", "11590", "20243", "24700", "28700", "30126", "31390", "33970", "37380", "38440", "43110", "45270", "47150", "60500", "63150", "63160", "63610", "74250", "76220", "76810", "77810", "78350", "78610", "78910", "78940", "80120", "80190", "83560", "83580", "83690", "86140", "95380"],
}

# Create a reverse lookup map (postal_code -> category)
POSTAL_CODE_TO_CATEGORY_MAP = {
    code: category for category, codes in POSTAL_CODE_CATEGORIES.items() for code in codes
}

# Create the flat list of codes to iterate over for scraping
POSTAL_CODES_TO_TEST = list(POSTAL_CODE_TO_CATEGORY_MAP.keys())

# --- Output CSV file name ---
CSV_FILENAME = "auchan_prix_principal_multi_cp_zones_PARALLEL.csv" # Changed filename

# --- Parallelism Configuration ---
# Ajustez ce nombre en fonction des ressources de votre Mac (CPU/RAM)
# Un bon point de départ est os.cpu_count() ou os.cpu_count() - 1
# Attention: trop de workers peuvent saturer la machine!
try:
    # os.cpu_count() donne le nombre de coeurs logiques
    # Sur un Mac M1/M2/M3, cela inclut les coeurs performance et efficacité
    # Sur un Mac Intel avec HyperThreading, cela donne le nombre de threads
    default_workers = max(1, os.cpu_count() - 1 if os.cpu_count() > 1 else 1)
except NotImplementedError:
    default_workers = 1 # Fallback si cpu_count() n'est pas dispo
MAX_WORKERS = default_workers # Vous pouvez forcer une valeur ici, ex: MAX_WORKERS = 4

# --- Scraping Function (OPTIMIZED with WebDriverWait) ---
# Cette fonction est conçue pour être exécutée dans un processus séparé
# Elle crée et ferme son propre driver.
def scrape_auchan_price(url, postal_code, timeout_duration=30): # Overall timeout
    """
    Scrape le PRIX PRINCIPAL d'un produit Auchan pour un code postal donné.
    OPTIMISÉ pour réduire les temps d'attente fixes en utilisant WebDriverWait.
    Returns a dictionary with the main product price.
    CONÇUE POUR ÊTRE APPELÉE EN PARALLÈLE.
    """
    process_id = os.getpid() # Pour identifier le worker dans les logs
    url_part_safe = re.sub(r'[^\w\-]+', '_', url.split('/')[-1])[:50]
    log_prefix = f"[Worker {process_id} | CP {postal_code} | {url_part_safe}]"
    print(f"{log_prefix} Démarrage scraping...")

    options = Options()
    # options.add_argument("--headless") # Activez si besoin, mais attention aux détections anti-bot
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument('--log-level=3') # Only show fatal errors
    options.add_argument('--disable-gpu') # Often needed in headless or CI environments
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36") # Example Mac User Agent
    options.add_argument('--lang=fr-FR')
    # options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2}) # Peut accélérer mais casser certains sites

    driver = None
    screenshot_suffix = f"url_{url_part_safe}_cp_{postal_code}_worker_{process_id}"

    # --- Define main XPaths/Selectors used repeatedly ---
    # (Gardés identiques à la version précédente)
    show_price_button_xpath = "//button[contains(., 'Afficher le prix') or contains(., 'Choisir mon magasin') or contains(., 'Retrait') or contains(., 'Livraison') or contains(@data-testid, 'delivery-method') or contains(@class, 'context-button')]"
    postal_input_selectors = ["input#search-input", "input[placeholder*='postal']", "input[name*='postal']", "input[id*='postal']", "input[data-testid*='postal']", "input[aria-label*='postal']", "input.journeySearchInput"]
    suggestion_list_xpath = "//ul[contains(@class, 'journey__search-suggests-list') and not(contains(@class, 'hidden'))]"
    first_suggestion_xpath_template = f"({suggestion_list_xpath}//li[contains(.,'{{postal_code}}')])[1]"
    store_container_base_xpath = "//div[contains(@class, 'journeyPosItem') or contains(@class, 'journey-service-context__wrapper') or contains(@class, 'store-card__wrapper')]"
    price_container_xpath = "//div[contains(@class,'product-price--main') or contains(@class,'default-price') or contains(@data-testid, 'product-price') or contains(@class, 'offer-selector__price-wrapper')]"
    main_price_xpath = ".//div[contains(@class,'product-price--large')] | .//div[contains(@class, 'product-price') and not(contains(@class, 'smaller')) and normalize-space(text())]"

    try:
        print(f"{log_prefix} Initialisation WebDriver...")
        # Chaque worker installe/utilise le driver indépendamment si nécessaire
        try:
             # Utilisation de webdriver-manager dans chaque processus
             # Il gère la mise en cache, donc ne re-télécharge pas à chaque fois
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except ValueError as e:
            # Erreur spécifique si ChromeDriverManager échoue (ex: offline)
            error_msg = f"ERREUR WebDriver Manager: {e}. Vérifiez connexion internet/cache."
            print(f"{log_prefix} {error_msg}")
            # Retourner un dictionnaire d'erreur spécifique
            return {
                "success": False, "url": url, "postal_code_used": postal_code,
                "selected_store": "Erreur Setup", "main_price": "Erreur Setup",
                "product_name_debug": "Erreur Setup", "error": error_msg
            }
        except Exception as wd_e:
            # Autres erreurs potentielles à l'init du WebDriver
            error_msg = f"ERREUR Init WebDriver: {type(wd_e).__name__} - {wd_e}"
            print(f"{log_prefix} {error_msg}")
            return {
                "success": False, "url": url, "postal_code_used": postal_code,
                "selected_store": "Erreur Setup", "main_price": "Erreur Setup",
                "product_name_debug": "Erreur Setup", "error": error_msg
            }


        # --- Define Waits ---
        wait = WebDriverWait(driver, timeout_duration)
        short_wait = WebDriverWait(driver, 5) # Légèrement augmenté pour robustesse
        modal_wait = WebDriverWait(driver, 10) # Légèrement augmenté
        suggestion_wait = WebDriverWait(driver, 5) # Légèrement augmenté
        store_list_wait = WebDriverWait(driver, 10) # Légèrement augmenté

        print(f"{log_prefix} WebDriver initialisé.")
        print(f"{log_prefix} Chargement URL...")
        driver.get(url)

        # Attente bouton localisation initial
        print(f"{log_prefix} Attente bouton localisation initial...")
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, show_price_button_xpath)))
            print(f"{log_prefix} Bouton localisation initial présent.")
        except TimeoutException:
            error_msg = "ERREUR: Bouton localisation initial non trouvé."
            print(f"{log_prefix} {error_msg}")
            # Sauvegarde d'écran peut échouer si le driver est déjà KO
            try: driver.save_screenshot(f"error_initial_button_missing_{screenshot_suffix}.png")
            except Exception: pass
            raise TimeoutException(error_msg) # Propage l'erreur pour être capturée par le bloc principal

        # Accept cookies (using short_wait)
        try:
            cookie_button = short_wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
            # Utilisation de JS click pour plus de fiabilité, surtout en parallèle
            driver.execute_script("arguments[0].click();", cookie_button)
            print(f"{log_prefix} Cookies acceptés (via JS).")
            time.sleep(0.5) # Petite pause après acceptation cookies si nécessaire
        except TimeoutException:
            print(f"{log_prefix} Pas de popup cookies trouvé/cliquable.")
        except Exception as e:
            print(f"{log_prefix} Erreur (non bloquante) acceptation cookies: {e}")

        # --- Main Scraping Logic (OPTIMIZED) ---
        selected_store_name = "Non défini (avant sélection)"
        try:
            # 1. Click button to open location modal
            print(f"{log_prefix} Recherche bouton localisation cliquable...")
            show_price_button = wait.until(EC.element_to_be_clickable((By.XPATH, show_price_button_xpath)))
            print(f"{log_prefix} Bouton trouvé: '{show_price_button.text}'. Clic (via JS)...")
            driver.execute_script("arguments[0].click();", show_price_button)
            print(f"{log_prefix} Bouton cliqué.")

            # 2. Wait for the postal code input field
            print(f"{log_prefix} Attente champ code postal dans le modal...")
            postal_input = None
            # Recherche plus robuste du champ postal
            for attempt in range(2): # Essayer 2 fois si le modal met du temps
                for selector in postal_input_selectors:
                    try:
                        postal_input = modal_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                        print(f"{log_prefix} Champ code postal trouvé via: '{selector}'.")
                        break
                    except TimeoutException:
                        continue
                if postal_input:
                    break
                elif attempt == 0:
                    print(f"{log_prefix} Champ postal non trouvé (essai 1), attente supplémentaire...")
                    time.sleep(1) # Pause avant de réessayer
            if not postal_input:
                error_msg = "ERREUR: Champ code postal introuvable après clic."
                print(f"{log_prefix} {error_msg}")
                try: driver.save_screenshot(f"error_postal_input_not_found_{screenshot_suffix}.png")
                except Exception: pass
                raise TimeoutException(error_msg)

            # 3. Enter postal code
            print(f"{log_prefix} Saisie CP '{postal_code}'...")
            postal_input.clear()
            time.sleep(0.3) # Pause avant saisie
            postal_input.send_keys(postal_code)
            print(f"{log_prefix} CP saisi.")
            time.sleep(0.5) # Pause après saisie pour laisser apparaitre suggestions

            # 4. Wait for suggestions OR press Enter, then wait for store list
            suggestion_found_and_clicked = False
            first_suggestion_xpath = first_suggestion_xpath_template.format(postal_code=postal_code)
            try:
                 print(f"{log_prefix} Attente suggestion correspondante (max {suggestion_wait._timeout}s)...")
                 suggestion_wait.until(EC.visibility_of_element_located((By.XPATH, suggestion_list_xpath)))
                 first_suggestion = suggestion_wait.until(EC.element_to_be_clickable((By.XPATH, first_suggestion_xpath)))
                 suggestion_text = first_suggestion.text.strip().replace('\n', ' ')
                 print(f"{log_prefix} Suggestion trouvée: '{suggestion_text}'. Clic (via JS)...")
                 driver.execute_script("arguments[0].click();", first_suggestion)
                 suggestion_found_and_clicked = True
                 print(f"{log_prefix} Suggestion cliquée via JS.")
                 time.sleep(0.5) # Pause pour laisser la liste des magasins charger

                 print(f"{log_prefix} Attente liste magasins après clic suggestion (max {store_list_wait._timeout}s)...")
                 store_list_wait.until(EC.presence_of_element_located((By.XPATH, store_container_base_xpath)))
                 print(f"{log_prefix} Début de liste magasins détecté après clic suggestion.")

            except TimeoutException:
                 print(f"{log_prefix} INFO: Suggestion non trouvée/cliquable ou liste magasins non apparue après clic. Tentative avec Entrée.")
                 if not suggestion_found_and_clicked:
                    try:
                        print(f"{log_prefix} Envoi de la touche Entrée...")
                        postal_input.send_keys(Keys.ENTER)
                        print(f"{log_prefix} Touche Entrée envoyée.")
                        time.sleep(0.5) # Pause pour laisser la liste des magasins charger

                        print(f"{log_prefix} Attente liste magasins après Entrée (max {store_list_wait._timeout}s)...")
                        store_list_wait.until(EC.presence_of_element_located((By.XPATH, store_container_base_xpath)))
                        print(f"{log_prefix} Début de liste magasins détecté après Entrée.")

                    except (ElementNotInteractableException, TimeoutException) as e_enter:
                        error_msg = f"ERREUR: Échec envoi Entrée ou attente liste magasins: {type(e_enter).__name__}"
                        print(f"{log_prefix} {error_msg}")
                        try: driver.save_screenshot(f"error_enter_or_store_list_failed_{screenshot_suffix}.png")
                        except Exception: pass
                        raise TimeoutException(error_msg) # Propage l'erreur

            # 5. Select Store/Point Relais
            store_selected = False
            selected_store_name = "Non sélectionné (erreur liste?)"
            print(f"{log_prefix} Recherche et sélection magasin disponible...")

            try:
                # Attendre que les conteneurs soient présents (ré-attente courte pour être sûr)
                store_containers = short_wait.until(EC.presence_of_all_elements_located((By.XPATH, store_container_base_xpath)))
                print(f"{log_prefix} Liste magasins trouvée ({len(store_containers)} éléments potentiels).")

                if not store_containers:
                    # Check for known 'no results' messages
                    try:
                        no_result_msg_xpath = "//*[contains(text(), 'Aucun magasin ne correspond') or contains(text(), 'Aucun point de retrait disponible') or contains(text(),'Aucun résultat')]"
                        no_result_msg = short_wait.until(EC.visibility_of_element_located((By.XPATH, no_result_msg_xpath)))
                        error_message = f"Aucun magasin trouvé pour {postal_code} (Message: '{no_result_msg.text.strip()}')"
                        raise NoSuchElementException(error_message) # Traiter comme échec
                    except TimeoutException:
                        raise NoSuchElementException("Aucun conteneur magasin trouvé et pas de message d'erreur clair.")

                # Iterate through potential stores/pickup points
                for i, container in enumerate(store_containers):
                    store_name_current = f"Item #{i+1}"
                    is_available = True
                    choose_button = None

                    # Get store name (best effort)
                    try:
                        name_el_xpath = ".//span[contains(@class, 'place-pos__name')] | .//h3[contains(@class,'store-card__name')] | .//div[contains(@class,'shop-name')] | .//span[contains(@data-testid,'store-name')]"
                        name_el = container.find_element(By.XPATH, name_el_xpath)
                        store_name_current = name_el.text.strip().replace('\n', ' ')
                    except NoSuchElementException:
                         pass # Nom non trouvé, on continue

                    # Check for unavailability
                    try:
                        unavailable_xpath = ".//*[contains(text(), 'Pas de créneau') or contains(text(), 'Indisponible') or contains(@class,'no-slot') or contains(@class,'unavailable')]"
                        container.find_element(By.XPATH, unavailable_xpath)
                        is_available = False
                    except NoSuchElementException:
                        # Check button status if no unavailable message
                        try:
                            choose_button_xpath = ".//button[contains(normalize-space(), 'Choisir') or contains(@data-testid,'choose-store') or contains(text(), 'Sélectionner')]"
                            choose_button = container.find_element(By.XPATH, choose_button_xpath)
                            if not choose_button.is_enabled(): is_available = False
                        except NoSuchElementException:
                            # Check for selected state if no 'choose' button
                            try:
                                selected_indicator_xpath = ".//div[contains(@class,'selected')] | .//button[contains(normalize-space(), 'Sélectionné')]"
                                container.find_element(By.XPATH, selected_indicator_xpath)
                                store_selected = True # Already selected
                                selected_store_name = store_name_current
                                print(f"{log_prefix} -> '{store_name_current}' déjà sélectionné.")
                                break # Exit loop
                            except NoSuchElementException:
                                is_available = False # No button, not selected -> unavailable

                    # If available and button found, try to click it
                    if is_available and choose_button:
                        print(f"{log_prefix} Tentative de sélection de '{store_name_current}' (disponible)...")
                        try:
                            # Scroll et Clic JS
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", choose_button)
                            time.sleep(0.3) # Pause après scroll
                            driver.execute_script("arguments[0].click();", choose_button)
                            store_selected = True
                            selected_store_name = store_name_current
                            print(f"{log_prefix} Magasin '{selected_store_name}' sélectionné via clic JS.")
                            time.sleep(1.0) # Pause après sélection pour laisser la page se mettre à jour
                            break # Exit loop
                        except (StaleElementReferenceException, ElementClickInterceptedException, TimeoutException, ElementNotInteractableException) as e_click:
                            print(f"{log_prefix} WARN: Clic échoué sur '{store_name_current}': {type(e_click).__name__}. Essai suivant.")
                        except Exception as e_click_other:
                            print(f"{log_prefix} WARN: Clic échoué (autre) sur '{store_name_current}': {type(e_click_other).__name__}. Essai suivant.")
                    elif not is_available and not store_selected:
                         print(f"{log_prefix} -> '{store_name_current}' ignoré (indisponible).")

            except (NoSuchElementException, TimeoutException) as e_store:
                error_msg = f"ERREUR: Liste magasins non trouvée ou problème sélection: {e_store}"
                print(f"{log_prefix} {error_msg}")
                try: driver.save_screenshot(f"error_store_list_selection_{screenshot_suffix}.png")
                except Exception: pass
                raise TimeoutException(error_msg) # Propage
            except Exception as e_list:
                error_msg = f"ERREUR inattendue traitement liste magasins: {type(e_list).__name__} - {e_list}"
                print(f"{log_prefix} {error_msg}")
                try: driver.save_screenshot(f"error_store_list_processing_{screenshot_suffix}.png")
                except Exception: pass
                raise RuntimeError(error_msg) # Propage comme erreur critique

            # Verify if a store was selected
            if not store_selected:
                error_msg = f"ERREUR: Aucun magasin disponible et sélectionnable trouvé pour CP {postal_code}."
                print(f"{log_prefix} {error_msg}")
                try: driver.save_screenshot(f"error_no_store_selected_{screenshot_suffix}.png")
                except Exception: pass
                raise TimeoutException(error_msg)

            # --- 6. Get MAIN PRICE ---
            print(f"{log_prefix} Sélection magasin réussie ('{selected_store_name}'). Attente MàJ prix principal...")
            main_price = "Non trouvé (après sélection)"
            try:
                # Attendre la visibilité du conteneur prix
                price_container_visible = wait.until(EC.visibility_of_element_located((By.XPATH, price_container_xpath)))
                print(f"{log_prefix} Conteneur prix principal visible.")

                # Essayer de trouver le prix spécifique dedans
                try:
                    main_price_element = price_container_visible.find_element(By.XPATH, main_price_xpath)
                    main_price_raw = main_price_element.text.strip().replace('\n', ' ')
                    if main_price_raw and any(char.isdigit() for char in main_price_raw):
                         main_price = re.sub(r'\s+', ' ', main_price_raw).replace(' €', '€').strip()
                         print(f"{log_prefix} Prix principal trouvé: {main_price}")
                    else:
                        # Fallback si texte vide/invalide
                        container_text = price_container_visible.text.strip().replace('\n', ' ')
                        print(f"{log_prefix} WARN: Élément prix vide/invalide ('{main_price_raw}'). Texte conteneur: '{container_text}'")
                        price_match = re.search(r'(\d+[\.,]\d{2})\s*€', container_text)
                        if price_match:
                            main_price = price_match.group(1).replace(',', '.') + '€'
                            print(f"{log_prefix} Prix principal extrait du conteneur: {main_price}")
                        else:
                            main_price = "Non trouvé (vide/invalide)"
                except NoSuchElementException:
                    print(f"{log_prefix} WARN: Prix principal spécifique non trouvé DANS le conteneur visible.")
                    # Essayer de lire le texte du conteneur directement comme fallback
                    container_text = price_container_visible.text.strip().replace('\n', ' ')
                    price_match = re.search(r'(\d+[\.,]\d{2})\s*€', container_text)
                    if price_match:
                        main_price = price_match.group(1).replace(',', '.') + '€'
                        print(f"{log_prefix} Prix principal extrait du conteneur (fallback): {main_price}")
                    else:
                        main_price = "Non trouvé (manquant dans conteneur)"

            except TimeoutException:
                print(f"{log_prefix} ERREUR: Timeout - Conteneur prix principal non visible après sélection magasin.")
                try: driver.save_screenshot(f"error_price_container_not_visible_{screenshot_suffix}.png")
                except Exception: pass
                main_price = "Non trouvé (conteneur invisible)"
            except Exception as e_price:
                 print(f"{log_prefix} ERREUR recherche/lecture prix : {type(e_price).__name__} - {e_price}")
                 main_price = "Erreur lecture Prix"

            # 7. Get Product Name (best effort)
            product_name_fallback = "Nom Inconnu"
            try:
                 h1 = short_wait.until(EC.visibility_of_element_located((By.TAG_NAME, "h1")))
                 product_name_fallback = h1.text.strip()
            except Exception as e_h1:
                 print(f"{log_prefix} WARN: Erreur récupération H1: {e_h1}")

            # --- 8. Return Results ---
            print(f"{log_prefix} Scrapping terminé avec succès.")
            return {
                "success": True,
                "url": url,
                "postal_code_used": postal_code,
                "selected_store": selected_store_name,
                "main_price": main_price,
                "product_name_debug": product_name_fallback,
                "error": None
            }

        # --- Error Handling within the main scraping logic ---
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException, RuntimeError) as e:
            # RuntimeError est ajouté pour les erreurs critiques propagées
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"{log_prefix} ERREUR processus principal: {error_msg}")
            error_screenshot_path = f"error_process_{type(e).__name__}_{screenshot_suffix}.png"
            try:
                if driver: driver.save_screenshot(error_screenshot_path)
                print(f"{log_prefix} Screenshot d'erreur: {error_screenshot_path}")
            except Exception as ss_err:
                print(f"{log_prefix} Erreur lors de la prise du screenshot d'erreur: {ss_err}")

            product_name_fallback = "Nom non récupéré (Erreur)"
            try:
                 if driver:
                     h1_elements = driver.find_elements(By.TAG_NAME, "h1")
                     if h1_elements: product_name_fallback = h1_elements[0].text.strip()
            except Exception: pass

            return {
                "success": False,
                "url": url,
                "postal_code_used": postal_code,
                "selected_store": selected_store_name, # Peut contenir le nom si l'erreur est après la sélection
                "main_price": "Erreur",
                "product_name_debug": product_name_fallback,
                "error": error_msg
            }
    # --- General Error Handling (Catches errors outside the main try-except like WebDriver init issues handled above) ---
    except Exception as e:
        # Ce bloc est moins susceptible d'être atteint car les erreurs d'init sont retournées plus tôt
        error_msg = f"Erreur générale non interceptée: {type(e).__name__} - {e}"
        print(f"{log_prefix} {error_msg}")
        if driver:
            try: driver.save_screenshot(f"general_error_screenshot_{screenshot_suffix}.png")
            except Exception: pass
        return {
            "success": False, "url": url, "postal_code_used": postal_code,
            "selected_store": "Erreur Générale", "main_price": "Erreur",
            "product_name_debug": "Erreur Générale", "error": error_msg
        }
    # --- Finally Block (Ensures WebDriver quits for this worker) ---
    finally:
        if driver:
            print(f"{log_prefix} Fermeture WebDriver...")
            try:
                driver.quit()
                print(f"{log_prefix} WebDriver fermé.")
            except Exception as quit_err:
                print(f"{log_prefix} Erreur lors de la fermeture de WebDriver: {quit_err}")
        print(f"{log_prefix} Fin worker.")


# --- Main Script Execution Logic (Parallelized) ---
if __name__ == "__main__":
    # Mettre le code d'exécution ici est CRUCIAL pour multiprocessing

    all_results = []
    start_time_total = time.time()

    # 1. Créer la liste complète des tâches (url, code_postal)
    tasks_to_run = []
    for product_url in PRODUCT_URLS:
        for cp in POSTAL_CODES_TO_TEST:
            tasks_to_run.append((product_url, cp))

    num_tasks = len(tasks_to_run)
    print(f"Lancement du scraping PARALLÈLE pour {len(PRODUCT_URLS)} produits et {len(POSTAL_CODES_TO_TEST)} codes postaux.")
    print(f"Nombre total de tâches: {num_tasks}")
    print(f"Utilisation de MAX {MAX_WORKERS} workers (processus parallèles).")
    print(f"Fichier CSV de sortie : {CSV_FILENAME}")
    print("-" * 30)

    completed_tasks = 0
    # 2. Utiliser ProcessPoolExecutor pour exécuter les tâches en parallèle
    # Le 'with' s'assure que le pool est correctement fermé à la fin
    with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Soumettre toutes les tâches et garder une trace des objets Future
        # Mappe future -> (url, cp) pour pouvoir retrouver la tâche originale
        future_to_task = {
            executor.submit(scrape_auchan_price, url, cp): (url, cp)
            for url, cp in tasks_to_run
        }

        # 3. Récupérer les résultats au fur et à mesure qu'ils arrivent
        for future in concurrent.futures.as_completed(future_to_task):
            task_url, task_cp = future_to_task[future]
            zone_type = POSTAL_CODE_TO_CATEGORY_MAP.get(task_cp, "Inconnue")
            try:
                # future.result() récupère le retour de la fonction OU lève l'exception si elle a eu lieu dans le worker
                result = future.result()
                # Ajouter le type de zone au résultat collecté
                result['zone_type'] = zone_type
                all_results.append(result)
                status = "SUCCÈS" if result.get('success') else "ÉCHEC"
                price_info = f"| Prix: {result.get('main_price', 'N/A')}" if result.get('success') else f"| Erreur: {result.get('error', 'Inconnue')}"
                print(f"Tâche terminée ({status}): CP {task_cp} @ {task_url.split('/')[-1][:30]}... {price_info}")

            except Exception as exc:
                # Gérer les exceptions qui n'ont pas été attrapées DANS scrape_auchan_price
                # ou des erreurs liées à l'exécution du future lui-même
                print(f"ERREUR Récupération Résultat: CP {task_cp} @ {task_url.split('/')[-1][:30]}... -> {type(exc).__name__}: {exc}")
                # Créer un enregistrement d'échec pour cette tâche
                error_result = {
                    "success": False,
                    "url": task_url,
                    "postal_code_used": task_cp,
                    "zone_type": zone_type,
                    "selected_store": "Erreur Exécution",
                    "main_price": "Erreur",
                    "product_name_debug": "Erreur Exécution",
                    "error": f"Erreur récupération Future: {type(exc).__name__}: {exc}"
                }
                all_results.append(error_result)

            finally:
                # Suivi de progression
                completed_tasks += 1
                print(f"Progression: {completed_tasks}/{num_tasks} tâches complétées.")
                # Optionnel : Afficher une estimation du temps restant toutes les N tâches
                if completed_tasks % 20 == 0 and completed_tasks > 0: # Toutes les 20 tâches par exemple
                     elapsed_time = time.time() - start_time_total
                     time_per_task = elapsed_time / completed_tasks
                     remaining_tasks = num_tasks - completed_tasks
                     estimated_remaining_time = remaining_tasks * time_per_task
                     print(f" -> Temps écoulé: {elapsed_time/60:.1f} min. Temps restant estimé: {estimated_remaining_time/60:.1f} min.")


    end_time_total = time.time()
    total_duration_minutes = (end_time_total - start_time_total) / 60
    print(f"\n\n>>>>>> Scraping PARALLÈLE terminé. Durée totale: {total_duration_minutes:.2f} minutes <<<<<<")

    # 4. Écrire tous les résultats collectés dans le CSV (une seule fois à la fin)
    if not all_results:
        print("Aucun résultat n'a été collecté. Le fichier CSV ne sera pas créé.")
    else:
        # Trier les résultats si nécessaire (par ex., par URL puis CP) - Optionnel
        # all_results.sort(key=lambda x: (x['url'], x['postal_code_used']))

        fieldnames = [
            "success", "url", "postal_code_used", "zone_type",
            "selected_store", "main_price", "product_name_debug", "error"
        ]
        file_exists = os.path.isfile(CSV_FILENAME)
        print(f"\nÉcriture des {len(all_results)} résultats dans {CSV_FILENAME}...")
        try:
            with open(CSV_FILENAME, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL, extrasaction='ignore')
                if not file_exists or os.path.getsize(CSV_FILENAME) == 0:
                    writer.writeheader()
                    print("En-tête CSV écrit.")

                successful_writes = 0
                for row_data in all_results:
                    try:
                        # Nettoyer les messages d'erreur potentiels pour le CSV
                        if row_data.get('error'):
                            row_data['error'] = str(row_data['error']).replace('\n', ' ').replace('\r', '')
                        writer.writerow(row_data)
                        successful_writes += 1
                    except Exception as write_err:
                        print(f"ERREUR: Échec écriture ligne CSV pour {row_data.get('url')}/{row_data.get('postal_code_used')}: {write_err}")

            print(f"Écriture terminée. {successful_writes}/{len(all_results)} lignes ajoutées/écrites dans {CSV_FILENAME}")

        except IOError as e:
            print(f"ERREUR: Impossible d'ouvrir ou d'écrire dans le fichier CSV {CSV_FILENAME}. Erreur: {e}")
        except Exception as e:
            print(f"ERREUR inattendue lors de l'écriture CSV: {type(e).__name__} - {e}")

    print("\nScript parallèle terminé.")