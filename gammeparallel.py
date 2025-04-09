# -*- coding: utf-8 -*- # Ajout pour assurer l'encodage UTF-8

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    ElementNotInteractableException, StaleElementReferenceException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager
import traceback # Pour un meilleur affichage des erreurs
import csv       # Pour le CSV
import os        # Pour gérer le chemin du fichier CSV
import multiprocessing # Pour la parallélisation

# --- Configuration ---
NUM_WORKERS = 8  # Nombre de processus parallèles (agents)
url_to_visit = "https://www.auchan.fr"

# Dictionnaire des codes postaux par catégorie (inchangé)
POSTAL_CODE_CATEGORIES = {
    "Grande Ville": ["13003", "13008", "13009", "13010", "13011", "13012", "13013", "13090", "31000", "31170", "31200", "31400", "33000", "33130", "33140", "33170", "33200", "33270", "33300", "33400", "33600", "33700", "34070", "44230", "44600", "44800", "54000", "57000", "57050", "57070", "59000", "59139", "59300", "59650", "59790", "59810", "67000", "67200", "67300", "67400", "69003", "69005", "69006", "69007", "69300", "69800", "75002", "75005", "75011", "75012", "75013", "75014", "75015", "75017", "75019", "75020", "77000", "78140", "78310", "78370", "78500", "78700", "91140", "91220", "91300", "91400", "92100", "92120", "92130", "92160", "92250", "92260", "92320", "92330", "92500", "92600", "92800", "93130", "93160", "93170", "93230", "93290", "93300", "93370", "93420", "93800", "94000", "94120", "94200", "94270", "94370", "94400", "94420", "94700", "95000", "95100", "95130", "95200", "95230", "95400", "95520", "95600"],
    "Ville Moyenne": ["02100", "06130", "06600", "11000", "11100", "13200", "13400", "14200", "15000", "16100", "19100", "20200", "21000", "26000", "26200", "30900", "31140", "31150", "31800", "31830", "34200", "37000", "37170", "38090", "38500", "38600", "42000", "42390", "45100", "45140", "45160", "46000", "49000", "49100", "49240", "51100", "54510", "54520", "59320", "59400", "60000", "60200", "60400", "62100", "62300", "62400", "63000", "63110", "63170", "64140", "64320", "65000", "66000", "68920", "69400", "71000", "72650", "73300", "74600", "76200", "76290", "76620", "77240", "78100", "78150", "78190", "78200", "78800", "80480", "80800", "81100", "82000", "83160", "83200", "83400", "83500", "83600", "83700", "84000", "84130", "84300", "86100", "86360", "88000", "89000", "90160"],
    "Petite Ville": ["01090", "02300", "02500", "03410", "04100", "04160", "04300", "05000", "06140", "06150", "06160", "06200", "06210", "06340", "06370", "07500", "10600", "13150", "13230", "13500", "13530", "13560", "13740", "13800", "14123", "14880", "16400", "16430", "18000", "20100", "20110", "20137", "20167", "20220", "20230", "20250", "20260", "20600", "24120", "24650", "26120", "26400", "26800", "27140", "27600", "27670", "30129", "33240", "33290", "33370", "33380", "34470", "34500", "34790", "36330", "37250", "37540", "38190", "38420", "38510", "41350", "42330", "43700", "44570", "45143", "45150", "45500", "47300", "50470", "54350", "57280", "59115", "59134", "59155", "59223", "59310", "59380", "59450", "59494", "59520", "59720", "59760", "59880", "60110", "60180", "60220", "62161", "62210", "62280", "62575", "62610", "62950", "62980", "63118", "63730", "66200", "67190", "67210", "67520", "67590", "69170", "69570", "69580", "69630", "70300", "71700", "73500", "74120", "74330", "76330", "76380", "77124", "77310", "77700", "78250", "78480", "80350", "83110", "83170", "83220", "83230", "83250", "83330", "86240", "88190", "91230", "91250"],
    "Campagne": ["04120", "11590", "20243", "24700", "28700", "30126", "31390", "33970", "37380", "38440", "43110", "45270", "47150", "60500", "63150", "63160", "63610", "74250", "76220", "76810", "77810", "78350", "78610", "78910", "78940", "80120", "80190", "83560", "83580", "83690", "86140", "95380"],
}

# Liste des produits à rechercher (version généraliste et précise)
product_list = [
    "Lait demi-écrémé",
    "Oeufs de poules élevées",
    "Yaourts nature",
    "Camembert",
    "Beurre doux",
    "Pain complet aux céréales",
    "Baguettes traditionnelles",
    "Special K",
    "Farine de blé",
    "Sucre de canne poudre",
    "Capsule café Nespresso",
    "Thé noir Twinings",
    "Confiture",
    "Miel naturel",
    "Jus d'orange",
    "Eau gazeuse Badoit",
    "Riz basmati",
    "Spaghetti",
    "Pommes de terre",
    "Lentilles vertes",
    "Conserves de tomates pelées",
    "Bouillon cube bio",
    "Pommes Golden",
    "Bananes",
    "Oranges à jus",
    "Citrons",
    "Raisins sans pépins",
    "Tomates",
    "Carottes",
    "Oignons jaunes",
    "Salade verte",
    "Concombres",
    "Poivrons",
    "Courgettes",
    "Aubergine",
    "Filet Blanc de poulet",
    "Steak haché",
    "Knackis",
    "Filets de poisson blanc",
    "Huile d’olive extra vierge",
    "Vinaigre balsamique",
    "Sel marin",
    "Poivre noir",
    "Ducros basilic",
    "Granola",
    "Chocolat noir",
    "Papier toilette",
    "Sacs poubelles biodégradables",
    "Liquide vaisselle",
    "Lessive hypoallergénique",
    "Nettoyant multi-usage",
    "Éponges de cuisine",
    "Shampooing",
    "Gel douche",
    "Dentifrice",
    "Savon mains",
    "Mouchoirs en papier",
    "Papier aluminium",
    "Sacs de congélation"
]



# Nom du fichier CSV de sortie
csv_filename = f"prix_produits_auchan_parallel_{NUM_WORKERS}_workers.csv"

# --- Sélecteurs (inchangés) ---
cookie_accept_button_id = "onetrust-accept-btn-handler"
initial_context_button_xpath = "//button[normalize-space()='Choisir vos courses'] | //a[normalize-space()='Choisir vos courses']"
initial_context_button_xpath_alternative = "//button[contains(., 'Choisir un drive ou la livraison')]"
postal_input_selectors = ["input#search-input", "input[placeholder*='postal']", "input[name*='postal']", "input[id*='postal']", "input[data-testid*='postal']", "input[aria-label*='postal']", "input.journeySearchInput"]
suggestion_list_xpath = "//ul[contains(@class, 'journey__search-suggests-list') and not(contains(@class, 'hidden'))]"
first_suggestion_xpath_template = f"({suggestion_list_xpath}//li[contains(.,'{{postal_code}}')])[1]"
store_list_container_xpath = "//div[contains(@class, 'journeyPosItem') or contains(@class, 'journey-service-context__wrapper') or contains(@class, 'store-card__wrapper')]"
select_store_button_xpath = ".//button[contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'choisir') or contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sélectionner') or contains(@data-testid,'choose-store') or contains(@class, 'selectButton')]"
store_name_xpath = ".//span[contains(@class, 'place-pos__name')] | .//h3[contains(@class,'store-card__name')] | .//div[contains(@class,'shop-name')] | .//span[contains(@data-testid,'store-name')] | .//p[contains(@class,'name')]"
search_input_selectors = [
    "input#header-search", "input[name='text']", "input[placeholder='Rechercher un produit...']",
    "input[data-testid='search-input']", "input[aria-label*='Rechercher']"
]
search_button_selectors = [
    "button[type='submit'][aria-label*='Rechercher']", "button[data-testid='search-button']",
    "button[class*='search']", "form[role='search'] button[type='submit']"
]
product_list_container_xpath = (
    "//div[contains(@class,'list-products')] | //ul[contains(@class,'list-products')] | "
    "//div[contains(@class,'result-list__list')] | //div[contains(@class,'search-results__list')] | "
    "//div[contains(@data-testid,'product-list')] | //ul[contains(@class,'product-grid')] | "
    "//div[contains(@class,'product-grid')] | //div[contains(@class,'shelfPage__list')] | "
    "//div[@class='list__container']"
)
product_article_xpath = "//article[contains(@class, 'product-thumbnail') and contains(@class, 'list__item')]"
product_name_relative_xpath = ".//p[contains(@class, 'product-thumbnail__description')]"
product_price_per_unit_relative_xpath = ".//div[contains(@class, 'product-thumbnail__attributes')]/span[last()]"
search_form_selectors = [
    "form[role='search']", "form#header-search-form", "form[action*='/recherche/']"
]
sort_select_element_id = "sort"
best_seller_option_value = "asc_item_quantity_7_days_pos"

# --- Options Chrome (regroupées pour clarté) ---
def get_chrome_options():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument('--log-level=3')
    # chrome_options.add_argument("--headless") # Keep headless commented out for easier debugging initially
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Use a common user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    chrome_options.add_argument('--lang=fr-FR')
    # Suppress webdriver manager logs and selenium logs
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    os.environ['WDM_LOG_LEVEL'] = '0' # Suppress webdriver-manager logs specifically
    return chrome_options

# --- Fonction utilitaire pour cliquer (inchangée) ---
def safe_click(driver, element_or_locator, wait_obj=None, scroll=True, scroll_tries=2):
    element = None
    if wait_obj is None: wait_obj = WebDriverWait(driver, 5) # Délai par défaut un peu plus long
    locator_str = str(element_or_locator)
    try:
        if isinstance(element_or_locator, tuple):
            element = wait_obj.until(EC.element_to_be_clickable(element_or_locator))
        else: # WebElement
            try:
                element_or_locator.is_displayed() # Basic check
                element = wait_obj.until(EC.element_to_be_clickable(element_or_locator))
            except StaleElementReferenceException:
                print(f"  WARN: safe_click: WebElement {locator_str} stale avant wait.")
                return False
        if not element:
            print(f"  ERREUR: safe_click: Élément non trouvé/cliquable via wait pour {locator_str}.")
            return False
        if scroll:
            current_try = 0
            while current_try < scroll_tries:
                 try:
                    # Essayer un scroll plus doux
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'});", element)
                    time.sleep(0.5) # Attendre un peu plus après scroll
                    element = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(element)) # Attendre plus longtemps après scroll
                    break
                 except StaleElementReferenceException:
                    print(f"  WARN: safe_click: Élément {locator_str} stale pendant/après scroll (essai {current_try + 1}).")
                    return False # Can't click a stale element
                 except TimeoutException:
                    if current_try == scroll_tries - 1: print(f"  WARN: safe_click: Élément {locator_str} non cliquable après {scroll_tries} scrolls. Tentative JS."); pass
                    else: time.sleep(0.6) # Attendre avant de réessayer le scroll
                 except Exception as scroll_err: print(f"  WARN: safe_click: Erreur scroll/vérif {locator_str} (essai {current_try + 1}): {scroll_err}")
                 current_try += 1
        # Tentative de clic standard
        try:
            element.click()
            time.sleep(0.5); return True # Pause après clic réussi
        except ElementClickInterceptedException:
            print(f"  safe_click: Clic standard intercepté pour {locator_str}. Tentative JS...")
            try: driver.execute_script("arguments[0].click();", element); print(f"  Clic JS réussi sur {locator_str}."); time.sleep(0.5); return True
            except Exception as e_js: print(f"  ERREUR: safe_click: Échec clic JS post-interception {locator_str}. Erreur: {e_js}"); return False
        except StaleElementReferenceException: print(f"  WARN: safe_click: Élément {locator_str} stale juste avant/pendant clic std."); return False
        except ElementNotInteractableException:
             print(f"  safe_click: ElementNotInteractable {locator_str}. Tentative JS...")
             try: driver.execute_script("arguments[0].click();", element); print(f"  Clic JS réussi sur {locator_str}."); time.sleep(0.5); return True
             except Exception as e_js_eni: print(f"  ERREUR: safe_click: Échec clic JS post-ENI {locator_str}. Erreur: {e_js_eni}"); return False
        except WebDriverException as e_wd_click: # Attrape les erreurs plus génériques du webdriver
             print(f"  ERREUR: safe_click: WebDriverException pendant clic standard {locator_str}. Erreur: {e_wd_click}. Tentative JS...")
             try: driver.execute_script("arguments[0].click();", element); print(f"  Clic JS réussi sur {locator_str}."); time.sleep(0.5); return True
             except Exception as e_js_wd: print(f"  ERREUR: safe_click: Échec clic JS post-WebDriverException {locator_str}. Erreur: {e_js_wd}"); return False
        except Exception as e_std: print(f"  ERREUR: safe_click: Erreur inattendue clic standard {locator_str}. Erreur: {e_std}"); return False
    except TimeoutException: print(f"  ERREUR: safe_click: Timeout localisation/cliquabilité {locator_str}."); return False
    except StaleElementReferenceException: print(f"  WARN: safe_click: L'élément {locator_str} était stale lors localisation initiale."); return False
    except Exception as e: print(f"  ERREUR: safe_click: Erreur majeure inattendue pour {locator_str}. Erreur: {e}"); return False

# --- Fonction pour prendre une capture d'écran (modifiée pour inclure CP) ---
def take_screenshot(driver, postal_code, filename_prefix="erreur"):
     if driver:
        try:
            screenshot_dir = "screenshots"
            if not os.path.exists(screenshot_dir):
                try:
                    os.makedirs(screenshot_dir)
                except FileExistsError:
                    pass # Ok if another process created it between check and creation
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_prefix = re.sub(r'[\\/*?:"<>|]', '_', filename_prefix)
            # Include postal code in filename for uniqueness
            screenshot_file = os.path.join(screenshot_dir, f"{safe_prefix}_auchan_{postal_code}_{timestamp}.png")
            # S'assurer que le driver est encore utilisable
            if driver.service.is_connectable():
                driver.save_screenshot(screenshot_file)
                print(f"[{postal_code}] Capture d'écran sauvegardée: {screenshot_file}")
            else:
                print(f"[{postal_code}] WARN: Impossible de prendre une capture d'écran, le driver n'est plus connecté ({filename_prefix}).")
        except WebDriverException as screen_e_wd:
             print(f"[{postal_code}] WARN: WebDriverException lors de la capture d'écran ({filename_prefix}): {screen_e_wd}")
        except Exception as screen_e:
            print(f"[{postal_code}] ERREUR: Impossible de prendre une capture d'écran ({filename_prefix}): {screen_e}")

# --- Fonction Worker pour un code postal ---
def scrape_postal_code(category, postal_code_to_use):
    """
    Scrape product data for a single postal code.
    Handles its own WebDriver instance and exceptions.
    Returns a list of product data rows for this postal code, or [] on failure.
    """
    # *** Chaque processus a sa propre instance WebDriver ***
    driver = None
    service = None
    local_product_data = [] # Données pour CE code postal uniquement
    store_selected_for_cp = False
    selected_store_name_for_cp = "Magasin non spécifié"

    print(f"[STARTING CP {postal_code_to_use}] Catégorie: {category}")

    try:
        # *** 1. Initialiser WebDriver pour ce processus ***
        print(f"--- Étape 0 [{postal_code_to_use}] : Initialisation WebDriver ---")
        try:
            chrome_options = get_chrome_options()
            # Ensure webdriver-manager downloads drivers to a unique location per process
            # or handles concurrency correctly (it usually does). If issues arise,
            # consider pre-downloading or specifying explicit driver paths.
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            # Waits are local to this driver instance
            long_wait = WebDriverWait(driver, 15) # Slightly longer waits might be needed
            medium_wait = WebDriverWait(driver, 10)
            short_wait = WebDriverWait(driver, 5)
            print(f"[{postal_code_to_use}] WebDriver initialisé.")
            time.sleep(0.5) # Pause after init
        except WebDriverException as e_init:
            print(f"[{postal_code_to_use}] ERREUR FATALE Initialisation WebDriver: {e_init}")
            print(traceback.format_exc())
            # Cannot proceed without a driver
            raise # Propagate to the outer try/except of this function

        # --- Étape 1 : Aller sur le site ---
        print(f"--- Étape 1 [{postal_code_to_use}] : Navigation vers {url_to_visit} ---")
        driver.get(url_to_visit)
        long_wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
        print(f"[{postal_code_to_use}] Page chargée.")
        time.sleep(1.0) # Increased pause

        # --- Étape 2 : Accepter les cookies ---
        print(f"--- Étape 2 [{postal_code_to_use}] : Acceptation cookies ---")
        try:
            # Use a longer wait specifically for the cookie button
            cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, cookie_accept_button_id)))
            if safe_click(driver, cookie_button, wait_obj=short_wait, scroll=False):
                print(f"[{postal_code_to_use}] Cookies acceptés.")
                time.sleep(1.0) # Pause after interaction
            else:
                print(f"WARN [{postal_code_to_use}]: Cookie button found but safe_click failed.")
        except TimeoutException:
            print(f"INFO [{postal_code_to_use}]: Cookie banner not found/timed out.")
        except Exception as e_cookie:
            print(f"WARN (non-blocking) cookies {postal_code_to_use} : {e_cookie}")

        # --- Étape 3 : Cliquer sur le bouton initial ---
        print(f"--- Étape 3 [{postal_code_to_use}] : Clic bouton contexte ---")
        initial_button_clicked = False
        initial_button_wait = WebDriverWait(driver, 20) # Longer wait for this critical button
        try:
            initial_button_locator = (By.XPATH, f"{initial_context_button_xpath} | {initial_context_button_xpath_alternative}")
            print(f"[{postal_code_to_use}] Attente bouton initial...")
            initial_button = initial_button_wait.until(EC.presence_of_element_located(initial_button_locator))
            try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", initial_button); time.sleep(0.5)
            except: pass
            initial_button = initial_button_wait.until(EC.element_to_be_clickable(initial_button_locator))
            button_text = initial_button.text.strip()[:30]
            print(f"[{postal_code_to_use}] Bouton initial trouvé ('{button_text}...'). Clic via safe_click...")

            if safe_click(driver, initial_button, wait_obj=medium_wait):
                initial_button_clicked = True
                print(f"[{postal_code_to_use}] Clic bouton initial réussi.")
                time.sleep(1.5) # Longer pause after this crucial click
            else:
                print(f"ERREUR [{postal_code_to_use}]: safe_click a échoué bouton initial.")
                # Error raised below

        except TimeoutException:
            print(f"ERREUR [{postal_code_to_use}]: Timeout - Aucun bouton initial cliquable trouvé.")
            # Error raised below

        if not initial_button_clicked:
            take_screenshot(driver, postal_code_to_use, "erreur_bouton_initial")
            raise ElementNotInteractableException(f"Échec final clic bouton contexte initial pour {postal_code_to_use}.")

        # --- Étape 4 : Saisir CP et clic suggestion ---
        print(f"--- Étape 4 [{postal_code_to_use}] : Saisie CP et clic suggestion ---")
        postal_input_element = None
        postal_input_located = False
        try:
            print(f"[{postal_code_to_use}] Localisation champ CP...")
            for i, selector in enumerate(postal_input_selectors):
                try:
                    postal_input_element = medium_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                    print(f"[{postal_code_to_use}] Champ CP trouvé avec '{selector}'.")
                    postal_input_located = True; break
                except TimeoutException:
                    if i == len(postal_input_selectors) - 1: print(f"Aucun sélecteur CP trouvé pour {postal_code_to_use}.")
                    continue
            if not postal_input_located: raise NoSuchElementException(f"Champ CP non localisé pour {postal_code_to_use}.")

            postal_input_element.clear(); time.sleep(0.2)
            postal_input_element.send_keys(postal_code_to_use)
            print(f"[{postal_code_to_use}] CP '{postal_code_to_use}' saisi.")
            time.sleep(1.5) # Wait longer for suggestions

            print(f"[{postal_code_to_use}] Attente et clic suggestion...")
            suggestion_clicked = False
            try:
                 # Wait for the list itself to be visible first
                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, suggestion_list_xpath)))
                # Then wait for at least one list item
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"{suggestion_list_xpath}//li")))

                first_suggestion_xpath = first_suggestion_xpath_template.format(postal_code=postal_code_to_use)
                # Be more lenient with finding the specific suggestion
                suggestion_element = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, first_suggestion_xpath)))

                if safe_click(driver, suggestion_element, wait_obj=short_wait, scroll=False):
                    print(f"[{postal_code_to_use}] Clic suggestion effectué.")
                    suggestion_clicked = True; time.sleep(2.0) # Longer pause after suggestion click
                else:
                    print(f"WARN [{postal_code_to_use}]: Clic suggestion échoué via safe_click.")

            except TimeoutException:
                print(f"WARN [{postal_code_to_use}]: Timeout attente suggestions/suggestion spécifique. Fallback ENTRÉE.")
            except Exception as e_sugg_click:
                print(f"ERREUR clic suggestion {postal_code_to_use}: {e_sugg_click}. Fallback ENTRÉE.")

            if not suggestion_clicked:
                print(f"[{postal_code_to_use}] Tentative fallback ENTRÉE...")
                try:
                    input_found_for_enter = False
                    for sel in postal_input_selectors:
                         try:
                              postal_input_element_refind = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                              # Check if the value still matches (important!)
                              if postal_input_element_refind.get_attribute('value') == postal_code_to_use:
                                  postal_input_element_refind.send_keys(Keys.RETURN)
                                  print(f"[{postal_code_to_use}] Touche ENTRÉE envoyée."); input_found_for_enter = True; time.sleep(2.0); break
                         except: continue
                    if not input_found_for_enter:
                        raise NoSuchElementException(f"Échec relocalisation input ou valeur incorrecte pour fallback ENTRÉE - CP {postal_code_to_use}")
                except Exception as e_enter_fallback:
                     print(f"ERREUR [{postal_code_to_use}]: Échec fallback ENTRÉE: {e_enter_fallback}")
                     raise # Propagate if fallback fails

        except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
            print(f"ERREUR Critique (Étape 4 - {postal_code_to_use}): {e}"); raise
        except Exception as e:
            print(f"ERREUR inattendue (Étape 4 - {postal_code_to_use}): {e}"); print(traceback.format_exc()); raise

        # --- Étape 5 : Sélection premier magasin ---
        print(f"--- Étape 5 [{postal_code_to_use}] : Sélection premier magasin ---")
        try:
            print(f"[{postal_code_to_use}] Attente liste magasins...")
            # Wait specifically for the button inside the container, longer timeout
            WebDriverWait(driver, 25).until(
                EC.presence_of_element_located((By.XPATH, f"{store_list_container_xpath}//button[contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'choisir')]"))
            )
            store_containers = driver.find_elements(By.XPATH, store_list_container_xpath)
            print(f"[{postal_code_to_use}] Liste magasins trouvée ({len(store_containers)} élément(s)).")

            if not store_containers:
                no_result_msg_xpath = "//*[contains(text(), 'Aucun magasin ne correspond') or contains(text(), 'Aucun point de retrait disponible') or contains(text(),'Aucun résultat') or contains(@class,'journeyEmptyResult')]"
                try:
                    message_element = WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, no_result_msg_xpath)))
                    message = message_element.text.strip()
                    print(f"INFO [{postal_code_to_use}]: Aucun magasin trouvé. Message: '{message}'")
                    store_selected_for_cp = False # Keep false
                except TimeoutException:
                     print(f"ERREUR [{postal_code_to_use}]: Liste magasins vide et pas de message 'aucun'.");
                     raise NoSuchElementException(f"Aucun container magasin trouvé et pas de message clair pour {postal_code_to_use}.")
            else:
                first_store_container = store_containers[0]
                print(f"[{postal_code_to_use}] Sélection premier élément.")
                try:
                    name_element = first_store_container.find_element(By.XPATH, store_name_xpath); first_store_name = name_element.text.strip().replace('\n', ' ')
                    print(f"[{postal_code_to_use}] Nom: '{first_store_name}'")
                    selected_store_name_for_cp = first_store_name # Store name for logging/CSV
                except NoSuchElementException: print(f"WARN [{postal_code_to_use}]: Nom premier magasin non trouvé.")

                print(f"[{postal_code_to_use}] Recherche/clic bouton sélection...")
                select_button_locator = (By.XPATH, select_store_button_xpath)
                try:
                    # Wait for the button within the *specific container*
                    select_button_element = WebDriverWait(first_store_container, medium_wait._timeout).until(EC.element_to_be_clickable(select_button_locator))
                    if safe_click(driver, select_button_element, wait_obj=short_wait, scroll=True): # Use scroll=True here just in case
                        print(f"[{postal_code_to_use}] Magasin '{selected_store_name_for_cp}' sélectionné.");
                        store_selected_for_cp = True; time.sleep(2.5) # Longer pause after store selection
                    else:
                        raise ElementClickInterceptedException(f"safe_click échec bouton sélection magasin {postal_code_to_use}.")
                except TimeoutException: print(f"ERREUR [{postal_code_to_use}]: Bouton sélection non trouvé/cliquable DANS magasin."); raise
                except Exception as e_sel_btn: print(f"ERREUR [{postal_code_to_use}] clic bouton sélection : {e_sel_btn}"); raise

        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e: print(f"ERREUR (Étape 5 - {postal_code_to_use}): {e}"); raise
        except Exception as e: print(f"ERREUR inattendue (Étape 5 - {postal_code_to_use}): {e}"); print(traceback.format_exc()); raise

        # --- Boucle Produits (si magasin sélectionné) ---
        if store_selected_for_cp:
            print(f"\n--- [{postal_code_to_use}] Début boucle produits ({selected_store_name_for_cp}) ---")
            for product_index, search_term in enumerate(product_list):
                print(f"\n-----------------------------------------------------")
                print(f"--- [{postal_code_to_use} - Prod {product_index + 1}/{len(product_list)}] : Recherche '{search_term}' ---")
                print(f"-----------------------------------------------------")
                try:
                    # --- ÉTAPE 6 : RECHERCHE PRODUIT ---
                    print(f"\n--- [{postal_code_to_use}] Étape 6 : Recherche '{search_term}' ---")
                    search_submitted_successfully = False
                    print(f"[{postal_code_to_use}] Localisation barre recherche...")
                    input_located = False; search_input_element = None
                    # Longer wait for search bar as page might still be settling
                    search_wait = WebDriverWait(driver, 15)
                    for i, selector in enumerate(search_input_selectors):
                        try:
                            search_input_element = search_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                            print(f"[{postal_code_to_use}] Barre recherche trouvée avec '{selector}'.")
                            input_located = True; break
                        except TimeoutException:
                            if i == len(search_input_selectors) - 1:
                                 print(f"WARN [{postal_code_to_use}/{search_term}]: Input recherche non trouvé. Tentative refresh.")
                                 driver.refresh(); time.sleep(3) # Longer sleep after refresh
                                 # Retry finding after refresh
                                 search_wait_retry = WebDriverWait(driver, 15)
                                 for j, sel_retry in enumerate(search_input_selectors):
                                     try:
                                          search_input_element = search_wait_retry.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel_retry)))
                                          print(f"[{postal_code_to_use}] Barre recherche trouvée post-refresh avec '{sel_retry}'.")
                                          input_located = True; break
                                     except TimeoutException:
                                          if j == len(search_input_selectors) - 1: raise TimeoutException(f"Input recherche non trouvé même post-refresh ('{search_term}' / {postal_code_to_use}).")
                                          else: continue
                                 if input_located: break # Break outer loop if found after refresh
                            else: continue
                    if not input_located: raise NoSuchElementException(f"Barre recherche non localisée ('{search_term}' / {postal_code_to_use}).")

                    # Sometimes clearing fails if element is stale right after finding it
                    try:
                        search_input_element.clear(); time.sleep(0.5)
                        search_input_element.send_keys(search_term)
                        print(f"[{postal_code_to_use}] Terme '{search_term}' saisi."); time.sleep(0.7)
                    except StaleElementReferenceException:
                        print(f"WARN [{postal_code_to_use}/{search_term}]: Input recherche stale post-localisation. Relocalisation...")
                        # Relocalize before sending keys again
                        input_located = False
                        for i, selector in enumerate(search_input_selectors):
                           try:
                               search_input_element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                               print(f"[{postal_code_to_use}] Barre recherche relocalisée avec '{selector}'.")
                               input_located = True; break
                           except: continue
                        if not input_located: raise StaleElementReferenceException(f"Impossible de relocaliser l'input search pour '{search_term}' / {postal_code_to_use}")
                        search_input_element.clear(); time.sleep(0.5)
                        search_input_element.send_keys(search_term)
                        print(f"[{postal_code_to_use}] Terme '{search_term}' saisi (après relocalisation)."); time.sleep(0.7)


                    print(f"[{postal_code_to_use}] Tentative prioritaire: ENTRÉE...")
                    try:
                        # Find element again to ensure it's fresh before sending Keys.RETURN
                        input_found_for_enter = False
                        for selector_refind in search_input_selectors:
                              try:
                                  search_input_element_refind = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_refind)))
                                  if search_input_element_refind.is_displayed() and search_input_element_refind.get_attribute('value') == search_term:
                                      search_input_element_refind.send_keys(Keys.RETURN); print(f"[{postal_code_to_use}] Touche ENTRÉE envoyée."); search_submitted_successfully = True; input_found_for_enter = True; time.sleep(2.5); break # Longer pause after search submit
                              except: continue # Ignore errors like StaleElement etc. here, just try next selector
                        if not input_found_for_enter: print(f"WARN [{postal_code_to_use}/{search_term}]: Input non retrouvé/correspondant pour Entrée. Fallback."); search_submitted_successfully = False
                    except Exception as e_enter_search: print(f"  WARN [{postal_code_to_use}/{search_term}]: Échec envoi ENTRÉE: {e_enter_search}"); search_submitted_successfully = False

                    # Fallback strategies (Button click, JS submit) - Code largely unchanged
                    if not search_submitted_successfully:
                        print(f"[{postal_code_to_use}/{search_term}] Fallback 1: Clic bouton recherche...")
                        for i, selector in enumerate(search_button_selectors):
                             if safe_click(driver, (By.CSS_SELECTOR if not selector.startswith('/') else By.XPATH, selector), wait_obj=short_wait, scroll=False):
                                 print(f"[{postal_code_to_use}/{search_term}] Bouton recherche cliqué ('{selector}')"); search_submitted_successfully = True; time.sleep(2.5); break
                             elif i == len(search_button_selectors) - 1: print(f"  INFO [{postal_code_to_use}/{search_term}]: Aucun bouton recherche cliquable.")

                    if not search_submitted_successfully:
                         print(f"[{postal_code_to_use}/{search_term}] Fallback 2: Soumission formulaire JS...")
                         submitted_via_js = False
                         for i, selector in enumerate(search_form_selectors):
                             try:
                                  search_form = driver.find_element(By.CSS_SELECTOR if not selector.startswith('/') else By.XPATH, selector)
                                  try:
                                      # Try finding the specific input within this form again
                                      form_input = WebDriverWait(search_form, 2).until(
                                          EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search'], input[name='text'], input[id*='search']"))
                                      )
                                      if form_input.get_attribute('value') == search_term:
                                          driver.execute_script("arguments[0].submit();", search_form); print(f"[{postal_code_to_use}/{search_term}] Formulaire ({selector}) soumis via JS."); search_submitted_successfully = True; submitted_via_js = True; time.sleep(2.5); break
                                      else: print(f"  INFO [{postal_code_to_use}/{search_term}]: Input value mismatch in form {selector}. Skipping JS submit.")
                                  except (NoSuchElementException, TimeoutException): print(f"  INFO [{postal_code_to_use}/{search_term}]: No matching input found in form {selector} for JS submit.")
                             except NoSuchElementException:
                                  if i == len(search_form_selectors) - 1: print(f"  ERREUR [{postal_code_to_use}/{search_term}]: Aucun formulaire recherche trouvé pour JS submit.")
                             except Exception as e_js_submit: print(f"  ERREUR [{postal_code_to_use}/{search_term}]: Échec JS submit form ({selector}): {e_js_submit}")
                         if not submitted_via_js and not search_submitted_successfully:
                            raise Exception(f"Impossible soumettre recherche pour '{search_term}' (CP: {postal_code_to_use}).")

                    # VALIDATION POST-RECHERCHE
                    if search_submitted_successfully:
                        print(f"[{postal_code_to_use}/{search_term}] Attente chargement résultats...")
                        try:
                            results_header_xpath = f"//*[normalize-space()='Votre recherche :'] | //h1[contains(.,'{search_term}')] | //*[contains(@class,'searchResults__title')] | //h1[contains(@class,'site-breadcrumb__title')]"
                            # Longer wait for results validation
                            results_wait = WebDriverWait(driver, 20)
                            results_wait.until( EC.any_of(
                                   EC.visibility_of_element_located((By.XPATH, results_header_xpath)),
                                   EC.presence_of_element_located((By.XPATH, product_list_container_xpath)),
                                   # Check if URL contains part of the search term (less reliable)
                                   # EC.url_contains(search_term.split(' ')[0].lower().replace("'", ""))
                               ) )
                            print(f"[{postal_code_to_use}/{search_term}] Page résultats chargée. Vérification conteneur produits...")
                            # Also wait explicitly for the product container
                            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, product_list_container_xpath)))
                            print(f"[{postal_code_to_use}/{search_term}] Conteneur produits présent."); time.sleep(1.0) # Pause after results load
                        except TimeoutException:
                            # Check for "no results" message only if the primary validation failed
                            no_results_xpath = "//*[contains(text(), 'aucun produit ne correspond') or contains(text(), 'aucun résultat') or contains(@class,'searchEmptyResult') or contains(@class,'no-result')]"
                            try:
                                WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, no_results_xpath)))
                                print(f"INFO [{postal_code_to_use}/{search_term}]: Aucun résultat trouvé. Skip produit."); time.sleep(0.5); continue # Go to next product
                            except TimeoutException:
                                print(f"ERREUR [{postal_code_to_use}/{search_term}]: Validation résultats échouée (ni titre/produits/msg 'aucun').");
                                take_screenshot(driver, postal_code_to_use, f"erreur_validation_{search_term[:10]}")
                                # Decide whether to continue to sort (might work) or skip product (safer)
                                # Let's skip the product if validation fails hard
                                continue
                    else:
                        # This case should technically be caught by the raise Exception above
                        raise Exception(f"Recherche non soumise avec succès ('{search_term}' / {postal_code_to_use}).")


                    # --- ÉTAPE 7 : TRI ---
                    # (Code unchanged, but benefits from waits/driver specific to this process)
                    print(f"\n--- [{postal_code_to_use}] Étape 7 : Tri 'Meilleures ventes' pour '{search_term}' ---")
                    try:
                        print(f"[{postal_code_to_use}/{search_term}] Localisation <select> tri...");
                        sort_select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, sort_select_element_id)))
                        try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_select_element); time.sleep(0.5)
                        except: pass
                        sort_select_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, sort_select_element_id)))
                        print(f"[{postal_code_to_use}/{search_term}] <select> tri trouvé.")
                        select_object = Select(sort_select_element);
                        print(f"[{postal_code_to_use}/{search_term}] Sélection valeur '{best_seller_option_value}'...");
                        select_object.select_by_value(best_seller_option_value);
                        print(f"[{postal_code_to_use}/{search_term}] Option sélectionnée.")
                        print(f"[{postal_code_to_use}/{search_term}] Attente MàJ post-tri...");
                        time.sleep(1.0) # Pause before waiting for update
                        try:
                            update_wait = WebDriverWait(driver, 15) # Longer wait for update
                            # Wait for staleness of an old element OR presence of new list/item
                            # This is tricky; waiting for presence of container is often sufficient
                            update_wait.until(EC.presence_of_element_located((By.XPATH, f"{product_list_container_xpath} | {product_article_xpath}")))
                            print(f"[{postal_code_to_use}/{search_term}] MàJ post-tri détectée.");
                            time.sleep(2.0) # Longer pause post-sort
                        except TimeoutException:
                            print(f"WARN [{postal_code_to_use}/{search_term}]: Timeout attente MàJ post-tri.")
                        print(f"[{postal_code_to_use}/{search_term}] Tri terminé.")
                    except (TimeoutException, NoSuchElementException) as e:
                         print(f"AVERTISSEMENT (Étape 7 - Tri {search_term}/{postal_code_to_use}): Échec. {type(e).__name__}: {e}.");
                         take_screenshot(driver, postal_code_to_use, f"erreur_etape7_tri_{search_term[:10]}")
                    except Exception as e:
                         print(f"ERREUR inattendue (Étape 7 - Tri {search_term}/{postal_code_to_use}) : {e}");
                         take_screenshot(driver, postal_code_to_use, f"erreur_etape7_tri_inattendue_{search_term[:10]}")

                    # --- ÉTAPE 8 : EXTRACTION ---
                    # (Code unchanged, operates on the current state of the driver)
                    print(f"\n--- [{postal_code_to_use}] Étape 8 : Extraction données '{search_term}' ---")
                    try:
                        print(f"[{postal_code_to_use}/{search_term}] Localisation articles produits...");
                        # Wait for articles to be present after potential sort/reload
                        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, product_article_xpath)))
                        product_articles = driver.find_elements(By.XPATH, product_article_xpath);
                        print(f"[{postal_code_to_use}/{search_term}] Trouvé {len(product_articles)} articles.")
                        if not product_articles:
                            print(f"[{postal_code_to_use}/{search_term}] Aucun produit trouvé sur la page.")
                        else:
                            num_products_to_extract = min(2, len(product_articles));
                            print(f"[{postal_code_to_use}/{search_term}] Extraction {num_products_to_extract} premiers...")
                            for i in range(num_products_to_extract):
                                product = product_articles[i]; product_name = "Nom non trouvé"; price_per_unit = "Prix/Unité non trouvé"
                                try:
                                    # More robust name finding
                                    name_element = WebDriverWait(product, 3).until(EC.presence_of_element_located((By.XPATH, product_name_relative_xpath)))
                                    product_name = " ".join(name_element.text.split()).strip()
                                except (NoSuchElementException, TimeoutException, StaleElementReferenceException): pass # Ignore if name not found/stale
                                try:
                                    # More robust price finding
                                    price_element = WebDriverWait(product, 3).until(EC.presence_of_element_located((By.XPATH, product_price_per_unit_relative_xpath)))
                                    price_per_unit = re.sub(r'\s+', ' ', price_element.text.strip()).replace(' l ', '/l ').replace(' kg ', '/kg ')
                                except (NoSuchElementException, TimeoutException, StaleElementReferenceException): pass # Ignore if price not found/stale

                                print(f"  [{postal_code_to_use}/{search_term}] Prod {i+1}: Nom='{product_name[:50]}...', Prix/Unité='{price_per_unit}'")
                                # Append to the list local to this function/process
                                local_product_data.append([category, postal_code_to_use, selected_store_name_for_cp, search_term, product_name, price_per_unit])
                    except TimeoutException:
                        print(f"ERREUR (Étape 8 - '{search_term}'/{postal_code_to_use}): Timeout attente articles.");
                        take_screenshot(driver, postal_code_to_use, f"erreur_etape8_timeout_{search_term[:10]}")
                    except Exception as e_extract:
                        print(f"ERREUR extraction (Étape 8 - '{search_term}'/{postal_code_to_use}) : {e_extract}");
                        take_screenshot(driver, postal_code_to_use, f"erreur_etape8_extract_{search_term[:10]}")

                # Gestion erreur PAR PRODUIT (within the product loop)
                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, StaleElementReferenceException, Exception) as e_product:
                    print(f"\n!!! [{postal_code_to_use}] ERREUR produit '{search_term}'. Skip produit. !!!");
                    print(f"Type: {type(e_product).__name__}, Msg: {e_product}");
                    print(f"{traceback.format_exc(limit=3)}");
                    take_screenshot(driver, postal_code_to_use, f"erreur_produit_{search_term[:10]}")
                    print("!!!\n")
                finally:
                     print(f"[{postal_code_to_use}] Fin traitement '{search_term}'. Pause..."); time.sleep(1.0) # Pause between products

            print(f"\n--- [{postal_code_to_use}] Fin boucle produits ---")
        else:
            print(f"\nINFO [{postal_code_to_use}]: Magasin non sélectionné/trouvé. Skip recherche produits.")

        # Si tout s'est bien passé pour ce CP, retourner les données collectées
        print(f"[SUCCESS CP {postal_code_to_use}] Traitement terminé. {len(local_product_data)} résultats trouvés.")
        return local_product_data

    # *** Gestion erreur POUR CE CODE POSTAL (attrape les erreurs des étapes 0 à 5 ou des erreurs imprévues) ***
    except (WebDriverException, TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, Exception) as e_cp:
         print(f"\n#######################################################")
         print(f"ERREUR MAJEURE traitement CP {postal_code_to_use} (Cat: {category}).")
         print(f"Type: {type(e_cp).__name__}"); print(f"Message: {e_cp}")
         print(f"Traceback:\n{traceback.format_exc()}")
         # Essayer de prendre une capture même si le driver est potentiellement KO
         take_screenshot(driver, postal_code_to_use, "erreur_config_CP")
         print(f"Ce code postal sera ignoré.")
         print(f"#######################################################\n")
         # Retourner une liste vide en cas d'échec majeur pour ce CP
         return [] # Important pour que le processus parent ne plante pas

    # *** FINALLY POUR CE CODE POSTAL : FERMER LE NAVIGATEUR DE CE PROCESSUS ***
    finally:
        if driver:
            print(f"[{postal_code_to_use}] Fermeture instance WebDriver...")
            try:
                driver.quit()
                print(f"[{postal_code_to_use}] WebDriver fermé.")
            except WebDriverException as e_quit:
                print(f"WARN [{postal_code_to_use}]: Erreur fermeture WebDriver: {e_quit}")
            except Exception as e_quit_generic:
                 print(f"WARN [{postal_code_to_use}]: Erreur générique fermeture WebDriver: {e_quit_generic}")
        else:
            print(f"[{postal_code_to_use}] Aucune instance WebDriver à fermer (erreur initiale?).")
        # Ne pas mettre de longue pause ici, la pool gère le lancement des suivants


# --- Programme Principal (Exécuté par le processus maître) ---
if __name__ == "__main__":
    # Protéger l'exécution principale

    print("--- Début du script de scraping parallèle ---")
    print(f"Nombre de workers configurés : {NUM_WORKERS}")
    start_time = time.time()

    # Créer la liste des tâches (tuples d'arguments pour scrape_postal_code)
    tasks = []
    for category, postal_codes in POSTAL_CODE_CATEGORIES.items():
        for code in postal_codes:
            tasks.append((category, code))

    total_tasks = len(tasks)
    print(f"Nombre total de codes postaux à traiter : {total_tasks}")

    all_product_data = [] # Liste pour agréger TOUS les résultats

    # Créer et gérer le pool de processus
    # Using 'spawn' start method might be more stable across platforms than 'fork' (default on Linux)
    # multiprocessing.set_start_method('spawn', force=True) # Uncomment if needed, requires testing
    try:
        with multiprocessing.Pool(processes=NUM_WORKERS) as pool:
            print(f"\n--- Lancement du pool de {NUM_WORKERS} workers ---")
            # starmap distribue les tâches et bloque jusqu'à ce que toutes soient terminées
            # results_list sera une liste de listes (chaque sous-liste est le résultat de scrape_postal_code)
            results_list = pool.starmap(scrape_postal_code, tasks)
            print("\n--- Tous les workers ont terminé ---")

        # Aplatir la liste de listes en une seule liste de résultats
        print("Agrégation des résultats...")
        all_product_data = [item for sublist in results_list for item in sublist if sublist] # Ensure item is added only if sublist is not None/empty
        print(f"Nombre total de lignes de données collectées : {len(all_product_data)}")

    except Exception as e_pool:
        print(f"\n--- ERREUR FATALE pendant l'exécution du Pool ---")
        print(f"Type: {type(e_pool).__name__}"); print(f"Message: {e_pool}")
        print(traceback.format_exc())
    finally:
        print("Fermeture du pool (si ouvert).") # Handled by 'with' statement

    # --- ÉTAPE 9 : Écriture CSV FINALE (inchangée, faite par le processus principal) ---
    print(f"\n--- Étape 9 : Écriture résultats CSV ---")
    if all_product_data:
        try:
            # Assurer que le chemin est absolu ou relatif au script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, csv_filename)
            print(f"Écriture {len(all_product_data)} lignes dans : {csv_path}")
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                # Updated header to include store name
                csvwriter.writerow(['Categorie Ville', 'Code Postal', 'Nom Magasin Sélectionné', 'Terme Recherche', 'Nom Produit Extrait', 'Prix par Kilo/Unité'])
                csvwriter.writerows(all_product_data)
            print(f"Données écrites avec succès dans '{csv_filename}'.")
        except IOError as e: print(f"ERREUR écriture CSV '{csv_filename}': {e}")
        except Exception as e_csv: print(f"ERREUR inattendue écriture CSV: {e_csv}\n{traceback.format_exc()}")
    else:
        print("Aucune donnée produit collectée ou toutes les tentatives ont échoué. Fichier CSV non créé/modifié.")

    end_time = time.time()
    print("\n--- Fin programme ---")
    print(f"Temps d'exécution total : {end_time - start_time:.2f} secondes")
    print("Script terminé.")