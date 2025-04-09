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
    WebDriverException # Importer pour gérer les erreurs de WebDriver
)
from webdriver_manager.chrome import ChromeDriverManager
import traceback # Pour un meilleur affichage des erreurs
import csv       # Pour le CSV
import os        # Pour gérer le chemin du fichier CSV

# --- Configuration ---
url_to_visit = "https://www.auchan.fr"

# Dictionnaire des codes postaux par catégorie (inchangé)
POSTAL_CODE_CATEGORIES = {
#    "Grande Ville": ["13003", "13008", "13009", "13010", "13011", "13012", "13013", "13090", "31000", "31170", "31200", "31400", "33000", "33130", "33140", "33170", "33200", "33270", "33300", "33400", "33600", "33700", "34070", "44230", "44600", "44800", "54000", "57000", "57050", "57070", "59000", "59139", "59300", "59650", "59790", "59810", "67000", "67200", "67300", "67400", "69003", "69005", "69006", "69007", "69300", "69800", "75002", "75005", "75011", "75012", "75013", "75014", "75015", "75017", "75019", "75020", "77000", "78140", "78310", "78370", "78500", "78700", "91140", "91220", "91300", "91400", "92100", "92120", "92130", "92160", "92250", "92260", "92320", "92330", "92500", "92600", "92800", "93130", "93160", "93170", "93230", "93290", "93300", "93370", "93420", "93800", "94000", "94120", "94200", "94270", "94370", "94400", "94420", "94700", "95000", "95100", "95130", "95200", "95230", "95400", "95520", "95600"],
    "Grande Ville": ["95000", "76240"],
#    "Ville Moyenne": ["02100", "06130", "06600", "11000", "11100", "13200", "13400", "14200", "15000", "16100", "19100", "20200", "21000", "26000", "26200", "30900", "31140", "31150", "31800", "31830", "34200", "37000", "37170", "38090", "38500", "38600", "42000", "42390", "45100", "45140", "45160", "46000", "49000", "49100", "49240", "51100", "54510", "54520", "59320", "59400", "60000", "60200", "60400", "62100", "62300", "62400", "63000", "63110", "63170", "64140", "64320", "65000", "66000", "68920", "69400", "71000", "72650", "73300", "74600", "76200", "76290", "76620", "77240", "78100", "78150", "78190", "78200", "78800", "80480", "80800", "81100", "82000", "83160", "83200", "83400", "83500", "83600", "83700", "84000", "84130", "84300", "86100", "86360", "88000", "89000", "90160"],
#    "Petite Ville": ["01090", "02300", "02500", "03410", "04100", "04160", "04300", "05000", "06140", "06150", "06160", "06200", "06210", "06340", "06370", "07500", "10600", "13150", "13230", "13500", "13530", "13560", "13740", "13800", "14123", "14880", "16400", "16430", "18000", "20100", "20110", "20137", "20167", "20220", "20230", "20250", "20260", "20600", "24120", "24650", "26120", "26400", "26800", "27140", "27600", "27670", "30129", "33240", "33290", "33370", "33380", "34470", "34500", "34790", "36330", "37250", "37540", "38190", "38420", "38510", "41350", "42330", "43700", "44570", "45143", "45150", "45500", "47300", "50470", "54350", "57280", "59115", "59134", "59155", "59223", "59310", "59380", "59450", "59494", "59520", "59720", "59760", "59880", "60110", "60180", "60220", "62161", "62210", "62280", "62575", "62610", "62950", "62980", "63118", "63730", "66200", "67190", "67210", "67520", "67590", "69170", "69570", "69580", "69630", "70300", "71700", "73500", "74120", "74330", "76330", "76380", "77124", "77310", "77700", "78250", "78480", "80350", "83110", "83170", "83220", "83230", "83250", "83330", "86240", "88190", "91230", "91250"],
#    "Campagne": ["04120", "11590", "20243", "24700", "28700", "30126", "31390", "33970", "37380", "38440", "43110", "45270", "47150", "60500", "63150", "63160", "63610", "74250", "76220", "76810", "77810", "78350", "78610", "78910", "78940", "80120", "80190", "83560", "83580", "83690", "86140", "95380"],
}

# Liste des produits à rechercher (inchangée)
product_list = [
#    "Lait", "Oeufs", "Yaourts nature", "Fromage", "Beurre", "Pain complet", "Baguettes",
#    "Céréales pour petit-déjeuner", "Farine", "Sucre", "Café moulu", "Thé", "Confiture",
#    "Miel", "Jus de fruits", "Eau minérale", "Riz", "Pâtes", "Pommes de terre", "Lentilles",
#    "Conserves de tomates", "Bouillon cube", "Pommes", "Bananes", "Oranges", "Citrons",
    "Raisins", "Tomates", "Carottes", "Oignons", "Salade", "Concombres", "Poivrons",
#    "Courgettes", "Aubergine", "Blanc de poulet", "Bœuf", "Saucisses", "Filets de poisson",
#    "Huile d’olive", "Vinaigre balsamique", "Sel", "Poivre", "Herbes de Provence",
#    "Biscuits", "Tablette de chocolat", "Papier toilette", "Sacs poubelles", "Liquide vaisselle",
#    "Détergent lessive", "Nettoyant multi-usage", "Éponges", "Shampooing", "Gel douche",
#    "Dentifrice", "Savon pour les mains", "Mouchoirs en papier", "Papier aluminium",
#    "Sacs de congélation"
]

# Nom du fichier CSV de sortie (inchangé)
csv_filename = "prix_produits_auchan_par_cp.csv"

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
    # chrome_options.add_argument("--headless") # Décommentez pour exécution sans interface graphique
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
    chrome_options.add_argument('--lang=fr-FR')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    return chrome_options

# --- Fonctions Utilitaires (safe_click, take_screenshot) ---
# (Le code de safe_click et take_screenshot reste identique à la version précédente)
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
                element_or_locator.is_displayed()
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
                    return False
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

# --- Fonction pour prendre une capture d'écran (inchangée) ---
def take_screenshot(driver, filename_prefix="erreur"):
     if driver:
        try:
            screenshot_dir = "screenshots"
            if not os.path.exists(screenshot_dir): os.makedirs(screenshot_dir)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            safe_prefix = re.sub(r'[\\/*?:"<>|]', '_', filename_prefix)
            screenshot_file = os.path.join(screenshot_dir, f"{safe_prefix}_auchan_{timestamp}.png")
            # S'assurer que le driver est encore utilisable
            if driver.service.is_connectable():
                driver.save_screenshot(screenshot_file)
                print(f"Capture d'écran sauvegardée: {screenshot_file}")
            else:
                print(f"WARN: Impossible de prendre une capture d'écran, le driver n'est plus connecté ({filename_prefix}).")
        except WebDriverException as screen_e_wd:
             print(f"WARN: WebDriverException lors de la capture d'écran ({filename_prefix}): {screen_e_wd}")
        except Exception as screen_e:
            print(f"ERREUR: Impossible de prendre une capture d'écran ({filename_prefix}): {screen_e}")

# --- Initialisation ---
all_product_data = [] # Liste pour stocker TOUS les résultats
total_cp_count = sum(len(codes) for codes in POSTAL_CODE_CATEGORIES.values())
processed_cp_count = 0
driver = None # *** Initialiser driver à None en dehors de la boucle ***

# --- Boucle Principale ---
try: # Bloc try global minimal, la gestion se fait surtout dans les boucles
    for category, postal_codes in POSTAL_CODE_CATEGORIES.items():
        print(f"\n=======================================================")
        print(f"=== DÉBUT CATÉGORIE : {category} ({len(postal_codes)} codes postaux) ===")
        print(f"=======================================================")

        for postal_code_to_use in postal_codes:
            processed_cp_count += 1
            print(f"\n+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print(f"+++ TRAITEMENT CP {processed_cp_count}/{total_cp_count} : {postal_code_to_use} (Catégorie: {category}) +++")
            print(f"+++++++++++++++++++++++++++++++++++++++++++++++++++++++")

            # *** RÉINITIALISATION POUR CHAQUE CODE POSTAL ***
            driver = None # Assurer que driver est None avant de commencer
            service = None
            store_selected_for_cp = False
            selected_store_name_for_cp = "Magasin non spécifié"

            try:
                # *** 1. Initialiser un NOUVEAU WebDriver pour ce CP ***
                print(f"--- Étape 0 [{postal_code_to_use}] : Initialisation nouvelle instance WebDriver ---")
                try:
                    chrome_options = get_chrome_options()
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    # Réinitialiser les waits pour la nouvelle instance
                    long_wait = WebDriverWait(driver, 1) # Donner un peu plus de temps globalement
                    medium_wait = WebDriverWait(driver, 1)
                    short_wait = WebDriverWait(driver, 1)
                    print("Nouvelle instance WebDriver initialisée avec succès.")
                    time.sleep(0.1) # Petite pause après initialisation
                except WebDriverException as e_init:
                    print(f"ERREUR FATALE lors de l'initialisation WebDriver pour {postal_code_to_use}: {e_init}")
                    print(traceback.format_exc())
                    # Si l'init échoue, on ne peut rien faire pour ce CP, on passe au suivant
                    raise # Propage l'erreur pour être attrapée par le bloc except externe du CP

                # --- Étape 1 : Aller sur le site ---
                print(f"--- Étape 1 [{postal_code_to_use}] : Navigation vers {url_to_visit} ---")
                driver.get(url_to_visit)
                long_wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                print("Page chargée (readyState complete).")
                time.sleep(0.1) # Pause accrue après chargement

                # --- Étape 2 : Accepter les cookies ---
                print(f"--- Étape 2 [{postal_code_to_use}] : Acceptation des cookies ---")
                try:
                    cookie_button = WebDriverWait(driver, 7).until(EC.element_to_be_clickable((By.ID, cookie_accept_button_id)))
                    if safe_click(driver, cookie_button, wait_obj=short_wait, scroll=False):
                        print("Cookies acceptés.")
                        time.sleep(0.1)
                    else:
                        print(f"WARN [{postal_code_to_use}]: Bannière cookies trouvée mais safe_click a échoué.")
                except TimeoutException:
                    print(f"INFO [{postal_code_to_use}]: Bannière cookies non trouvée (probablement déjà acceptée ou absente).")
                except Exception as e_cookie:
                    print(f"AVERTISSEMENT (non bloquant) cookies {postal_code_to_use} : {e_cookie}")

                # --- Étape 3 : Cliquer sur le bouton initial ---
                print(f"--- Étape 3 [{postal_code_to_use}] : Clic sur bouton contexte initial ---")
                initial_button_clicked = False
                # Donner plus de temps spécifiquement pour ce bouton critique
                initial_button_wait = WebDriverWait(driver, 15)
                try:
                    # Essayer de localiser le bouton
                    initial_button_locator = (By.XPATH, f"{initial_context_button_xpath} | {initial_context_button_xpath_alternative}")
                    print("Attente du bouton initial...")
                    initial_button = initial_button_wait.until(EC.presence_of_element_located(initial_button_locator))
                    # Essayer de scroller vers lui au cas où
                    try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", initial_button); time.sleep(0.5)
                    except: pass
                    # Attendre qu'il soit cliquable
                    initial_button = initial_button_wait.until(EC.element_to_be_clickable(initial_button_locator))

                    button_text = initial_button.text.strip()[:30]
                    print(f"Bouton initial trouvé et cliquable ('{button_text}...'). Tentative de clic via safe_click...")

                    # Utiliser safe_click pour la robustesse
                    if safe_click(driver, initial_button, wait_obj=medium_wait): # safe_click a déjà ses waits internes
                        initial_button_clicked = True
                        print("Clic sur bouton initial réussi.")
                        time.sleep(0.1) # Pause après clic réussi
                    else:
                         # Si safe_click retourne False
                        print(f"ERREUR [{postal_code_to_use}]: safe_click a échoué pour le bouton initial (même si trouvé cliquable initialement).")
                        # L'erreur sera levée par la condition 'if not initial_button_clicked'

                except TimeoutException:
                    print(f"ERREUR [{postal_code_to_use}]: Timeout - Aucun bouton initial cliquable trouvé dans le délai imparti.")
                    # L'erreur sera levée ci-dessous

                # Vérifier si le clic a réussi
                if not initial_button_clicked:
                    take_screenshot(driver, f"erreur_bouton_initial_{postal_code_to_use}")
                    # Lever une exception claire pour indiquer l'échec de cette étape cruciale
                    raise ElementNotInteractableException(f"Échec final du clic sur le bouton contexte initial pour {postal_code_to_use}.")

                # --- Étape 4 : Saisir CP et clic suggestion ---
                print(f"--- Étape 4 [{postal_code_to_use}] : Saisie CP et clic suggestion ---")
                # (Le code interne de l'étape 4 reste très similaire, mais bénéficie de la nouvelle instance driver)
                postal_input_element = None
                postal_input_located = False
                try:
                    print("Localisation champ code postal...")
                    for i, selector in enumerate(postal_input_selectors):
                        try:
                            postal_input_element = medium_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                            print(f"Champ CP trouvé avec '{selector}'.")
                            postal_input_located = True; break
                        except TimeoutException:
                            if i == len(postal_input_selectors) - 1: print(f"Aucun sélecteur CP trouvé pour {postal_code_to_use}.")
                            continue
                    if not postal_input_located: raise NoSuchElementException(f"Champ CP non localisé pour {postal_code_to_use}.")

                    postal_input_element.clear(); time.sleep(0.1)
                    postal_input_element.send_keys(postal_code_to_use)
                    print(f"CP '{postal_code_to_use}' saisi.")
                    time.sleep(0.1) # Attendre suggestions

                    print("Attente et clic suggestion...")
                    suggestion_clicked = False
                    try:
                        WebDriverWait(driver, 8).until(EC.visibility_of_element_located((By.XPATH, suggestion_list_xpath)))
                        WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, f"{suggestion_list_xpath}//li")))

                        first_suggestion_xpath = first_suggestion_xpath_template.format(postal_code=postal_code_to_use)
                        suggestion_element = WebDriverWait(driver, 6).until(EC.element_to_be_clickable((By.XPATH, first_suggestion_xpath)))

                        if safe_click(driver, suggestion_element, wait_obj=short_wait, scroll=False):
                            print("Clic suggestion effectué.")
                            suggestion_clicked = True; time.sleep(0.1) # Pause accrue après clic suggestion
                        else:
                            print(f"WARN [{postal_code_to_use}]: Clic suggestion échoué via safe_click.")

                    except TimeoutException:
                        print(f"WARN [{postal_code_to_use}]: Timeout attente suggestions/suggestion spécifique. Fallback ENTRÉE.")
                    except Exception as e_sugg_click:
                        print(f"ERREUR clic suggestion {postal_code_to_use}: {e_sugg_click}. Fallback ENTRÉE.")

                    if not suggestion_clicked:
                        print(f"Tentative fallback ENTRÉE pour {postal_code_to_use}...")
                        try:
                            input_found_for_enter = False
                            for sel in postal_input_selectors:
                                 try:
                                      postal_input_element_refind = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                                      if postal_input_element_refind.get_attribute('value') == postal_code_to_use:
                                          postal_input_element_refind.send_keys(Keys.RETURN)
                                          print("Touche ENTRÉE envoyée."); input_found_for_enter = True; time.sleep(0.1); break
                                 except: continue
                            if not input_found_for_enter:
                                raise NoSuchElementException(f"Échec relocalisation input pour fallback ENTRÉE - CP {postal_code_to_use}")
                        except Exception as e_enter_fallback:
                             print(f"ERREUR [{postal_code_to_use}]: Échec fallback ENTRÉE: {e_enter_fallback}")
                             raise # Propage si fallback échoue

                except (TimeoutException, NoSuchElementException, ElementNotInteractableException) as e:
                    print(f"ERREUR Critique (Étape 4 - {postal_code_to_use}): {e}"); raise
                except Exception as e:
                    print(f"ERREUR inattendue (Étape 4 - {postal_code_to_use}): {e}"); print(traceback.format_exc()); raise

                # --- Étape 5 : Sélection premier magasin ---
                print(f"--- Étape 5 [{postal_code_to_use}] : Sélection premier magasin ---")
                # (Code interne de l'étape 5 similaire)
                try:
                    print("Attente liste magasins...")
                    WebDriverWait(driver, 18).until( # Attendre plus longtemps la liste des magasins
                        EC.presence_of_element_located((By.XPATH, f"{store_list_container_xpath}//button[contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'choisir')]"))
                    )
                    store_containers = driver.find_elements(By.XPATH, store_list_container_xpath)
                    print(f"Liste magasins trouvée ({len(store_containers)} élément(s)) pour {postal_code_to_use}.")

                    if not store_containers:
                        no_result_msg_xpath = "//*[contains(text(), 'Aucun magasin ne correspond') or contains(text(), 'Aucun point de retrait disponible') or contains(text(),'Aucun résultat') or contains(@class,'journeyEmptyResult')]"
                        try:
                            message_element = WebDriverWait(driver, 4).until(EC.visibility_of_element_located((By.XPATH, no_result_msg_xpath)))
                            message = message_element.text.strip()
                            print(f"INFO [{postal_code_to_use}]: Aucun magasin trouvé. Message: '{message}'")
                            store_selected_for_cp = False
                        except TimeoutException:
                             print(f"ERREUR [{postal_code_to_use}]: Liste magasins vide et pas de message 'aucun'.");
                             raise NoSuchElementException(f"Aucun container magasin trouvé et pas de message clair pour {postal_code_to_use}.")
                    else:
                        first_store_container = store_containers[0]
                        print("Sélection premier élément.")
                        try:
                            name_element = first_store_container.find_element(By.XPATH, store_name_xpath); first_store_name = name_element.text.strip().replace('\n', ' ')
                            print(f"Nom: '{first_store_name}'")
                            selected_store_name_for_cp = first_store_name
                        except NoSuchElementException: print("WARN: Nom premier magasin non trouvé.")

                        print(f"Recherche/clic bouton sélection...")
                        select_button_locator = (By.XPATH, select_store_button_xpath)
                        try:
                            select_button_element = WebDriverWait(first_store_container, medium_wait._timeout).until(EC.element_to_be_clickable(select_button_locator))
                            if safe_click(driver, select_button_element, wait_obj=short_wait, scroll=True):
                                print(f"Magasin '{selected_store_name_for_cp}' sélectionné pour {postal_code_to_use}.");
                                store_selected_for_cp = True; time.sleep(0.1) # Pause après sélection
                            else:
                                raise ElementClickInterceptedException(f"safe_click échec bouton sélection magasin {postal_code_to_use}.")
                        except TimeoutException: print(f"ERREUR [{postal_code_to_use}]: Bouton sélection non trouvé/cliquable DANS magasin."); raise
                        except Exception as e_sel_btn: print(f"ERREUR [{postal_code_to_use}] clic bouton sélection : {e_sel_btn}"); raise

                except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e: print(f"ERREUR (Étape 5 - {postal_code_to_use}): {e}"); raise
                except Exception as e: print(f"ERREUR inattendue (Étape 5 - {postal_code_to_use}): {e}"); print(traceback.format_exc()); raise

                # --- Boucle Produits (si magasin sélectionné) ---
                if store_selected_for_cp:
                    print(f"\n--- Début boucle produits pour CP {postal_code_to_use} ({selected_store_name_for_cp}) ---")
                    # La boucle produit interne (étapes 6, 7, 8) reste identique à la version précédente
                    # Elle utilise le 'driver' et les 'waits' qui ont été initialisés pour ce CP
                    for product_index, search_term in enumerate(product_list):
                        print(f"\n-----------------------------------------------------")
                        print(f"--- [{postal_code_to_use} - Prod {product_index + 1}/{len(product_list)}] : Recherche '{search_term}' ---")
                        print(f"-----------------------------------------------------")
                        try:
                            # --- ÉTAPE 6 : RECHERCHE PRODUIT ---
                            print(f"\n--- Étape 6 : Recherche '{search_term}' ---")
                            search_submitted_successfully = False
                            print("Localisation barre recherche...")
                            input_located = False; search_input_element = None
                            for i, selector in enumerate(search_input_selectors):
                                try:
                                    search_input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))) # Attente un peu plus longue
                                    print(f"Barre recherche trouvée avec '{selector}'.")
                                    input_located = True; break
                                except TimeoutException:
                                    if i == len(search_input_selectors) - 1:
                                         print(f"WARN [{postal_code_to_use}/{search_term}]: Input recherche non trouvé. Tentative refresh.")
                                         driver.refresh(); time.sleep(0.1)
                                         for j, sel_retry in enumerate(search_input_selectors):
                                             try:
                                                  search_input_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel_retry)))
                                                  print(f"Barre recherche trouvée post-refresh avec '{sel_retry}'.")
                                                  input_located = True; break
                                             except TimeoutException:
                                                  if j == len(search_input_selectors) - 1: raise TimeoutException(f"Input recherche non trouvé même post-refresh ('{search_term}' / {postal_code_to_use}).")
                                                  else: continue
                                         if input_located: break
                                    else: continue
                            if not input_located: raise NoSuchElementException(f"Barre recherche non localisée ('{search_term}' / {postal_code_to_use}).")

                            search_input_element.clear(); time.sleep(0.4)
                            search_input_element.send_keys(search_term)
                            print(f"Terme '{search_term}' saisi."); time.sleep(0.5)

                            print("Tentative prioritaire: ENTRÉE...")
                            try:
                                 input_found_for_enter = False
                                 for selector_refind in search_input_selectors:
                                      try:
                                          search_input_element_refind = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_refind)))
                                          if search_input_element_refind.get_attribute('value') == search_term:
                                              search_input_element_refind.send_keys(Keys.RETURN); print("Touche ENTRÉE envoyée."); search_submitted_successfully = True; input_found_for_enter = True; time.sleep(0.1); break
                                      except: continue
                                 if not input_found_for_enter: print("WARN: Input non retrouvé/correspondant pour Entrée. Fallback."); search_submitted_successfully = False
                            except Exception as e_enter_search: print(f"  WARN: Échec envoi ENTRÉE: {e_enter_search}"); search_submitted_successfully = False

                            if not search_submitted_successfully: # Fallback 1: Clic Bouton
                                print("Fallback 1: Clic bouton recherche...")
                                for i, selector in enumerate(search_button_selectors):
                                     if safe_click(driver, (By.CSS_SELECTOR if not selector.startswith('/') else By.XPATH, selector), wait_obj=short_wait, scroll=False):
                                         print(f"Bouton recherche cliqué ('{selector}')"); search_submitted_successfully = True; time.sleep(0.1); break
                                     elif i == len(search_button_selectors) - 1: print("  INFO: Aucun bouton recherche cliquable.")

                            if not search_submitted_successfully: # Fallback 2: JS Submit
                                 print("Fallback 2: Soumission formulaire JS...")
                                 submitted_via_js = False
                                 for i, selector in enumerate(search_form_selectors):
                                     try:
                                          search_form = driver.find_element(By.CSS_SELECTOR if not selector.startswith('/') else By.XPATH, selector)
                                          try:
                                              form_input = search_form.find_element(By.CSS_SELECTOR, "input[type='search'], input[name='text'], input[id*='search']")
                                              if form_input.get_attribute('value') == search_term:
                                                  driver.execute_script("arguments[0].submit();", search_form); print(f"Formulaire ({selector}) soumis via JS."); search_submitted_successfully = True; submitted_via_js = True; time.sleep(0.1); break
                                              else: pass # Skip si input pas bon
                                          except NoSuchElementException: pass # Skip si pas d'input dans ce form
                                     except NoSuchElementException:
                                          if i == len(search_form_selectors) - 1: print("  ERREUR: Aucun formulaire recherche trouvé pour JS submit.")
                                     except Exception as e_js_submit: print(f"  ERREUR: Échec JS submit form ({selector}): {e_js_submit}")
                                 if not submitted_via_js and not search_submitted_successfully:
                                    raise Exception(f"Impossible soumettre recherche pour '{search_term}' (CP: {postal_code_to_use}).")

                            # VALIDATION POST-RECHERCHE
                            if search_submitted_successfully:
                                print(f"Attente chargement résultats '{search_term}'...")
                                try:
                                    results_header_xpath = f"//*[normalize-space()='Votre recherche :'] | //h1[contains(.,'{search_term}')] | //*[contains(@class,'searchResults__title')] | //h1[contains(@class,'site-breadcrumb__title')]"
                                    WebDriverWait(driver, 18).until( EC.any_of( # Attente plus longue validation
                                           EC.visibility_of_element_located((By.XPATH, results_header_xpath)),
                                           EC.presence_of_element_located((By.XPATH, product_list_container_xpath)),
                                           EC.url_contains(search_term.split(' ')[0].lower())
                                       ) )
                                    print(f"Page résultats chargée."); medium_wait.until(EC.presence_of_element_located((By.XPATH, product_list_container_xpath))); print("Conteneur produits présent."); time.sleep(0.1)
                                except TimeoutException:
                                    no_results_xpath = "//*[contains(text(), 'aucun produit ne correspond') or contains(text(), 'aucun résultat') or contains(@class,'searchEmptyResult') or contains(@class,'no-result')]"
                                    try:
                                        WebDriverWait(driver, 3).until(EC.visibility_of_element_located((By.XPATH, no_results_xpath)))
                                        print(f"INFO [{postal_code_to_use}/{search_term}]: Aucun résultat trouvé. Skip produit."); time.sleep(0.1); continue # Passe au produit suivant
                                    except TimeoutException:
                                        print(f"ERREUR [{postal_code_to_use}/{search_term}]: Validation résultats échouée (ni titre/produits/msg 'aucun')."); take_screenshot(driver, f"erreur_validation_{postal_code_to_use}_{search_term[:10]}"); pass # Continue vers tri (suspect)
                            else: raise Exception(f"Recherche non soumise avec succès ('{search_term}' / {postal_code_to_use}).")

                            # --- ÉTAPE 7 : TRI ---
                            print(f"\n--- Étape 7 : Tri 'Meilleures ventes' pour '{search_term}' ---")
                            try:
                                print(f"Localisation <select> tri..."); sort_select_element = medium_wait.until(EC.presence_of_element_located((By.ID, sort_select_element_id)))
                                try: driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sort_select_element); time.sleep(0.4)
                                except: pass
                                sort_select_element = medium_wait.until(EC.element_to_be_clickable((By.ID, sort_select_element_id))); print("<select> tri trouvé.")
                                select_object = Select(sort_select_element); print(f"Sélection valeur '{best_seller_option_value}'..."); select_object.select_by_value(best_seller_option_value); print("Option sélectionnée.")
                                print("Attente MàJ post-tri..."); time.sleep(0.1) # Petite pause avant d'attendre
                                try:
                                    update_wait = WebDriverWait(driver, 12) # Attendre un peu plus la MàJ
                                    # Attendre que le container ou le premier produit soit présent (pourrait devenir stale et réapparaitre)
                                    update_wait.until(EC.presence_of_element_located((By.XPATH, f"{product_list_container_xpath} | {product_article_xpath}")))
                                    print(f"MàJ post-tri détectée."); time.sleep(1.8) # Pause accrue post-tri
                                except TimeoutException: print(f"WARN [{postal_code_to_use}/{search_term}]: Timeout attente MàJ post-tri.")
                                print("Tri terminé.")
                            except (TimeoutException, NoSuchElementException) as e: print(f"AVERTISSEMENT (Étape 7 - Tri {search_term}/{postal_code_to_use}): Échec. {type(e).__name__}: {e}."); take_screenshot(driver, f"erreur_etape7_tri_{postal_code_to_use}_{search_term[:10]}")
                            except Exception as e: print(f"ERREUR inattendue (Étape 7 - Tri {search_term}/{postal_code_to_use}) : {e}"); take_screenshot(driver, f"erreur_etape7_tri_inattendue_{postal_code_to_use}_{search_term[:10]}")

                            # --- ÉTAPE 8 : EXTRACTION ---
                            print(f"\n--- Étape 8 : Extraction données '{search_term}' ---")
                            try:
                                print("Localisation articles produits..."); medium_wait.until(EC.presence_of_element_located((By.XPATH, product_article_xpath))); product_articles = driver.find_elements(By.XPATH, product_article_xpath); print(f"Trouvé {len(product_articles)} articles.")
                                if not product_articles: print(f"Aucun produit trouvé page pour '{search_term}'.")
                                else:
                                    num_products_to_extract = min(2, len(product_articles)); print(f"Extraction {num_products_to_extract} premiers...")
                                    for i in range(num_products_to_extract):
                                        product = product_articles[i]; product_name = "Nom non trouvé"; price_per_unit = "Prix/Unité non trouvé"
                                        try: name_element = product.find_element(By.XPATH, product_name_relative_xpath); product_name = " ".join(name_element.text.split()).strip()
                                        except: pass
                                        try: price_element = product.find_element(By.XPATH, product_price_per_unit_relative_xpath); price_per_unit = re.sub(r'\s+', ' ', price_element.text.strip()).replace(' l ', '/l ').replace(' kg ', '/kg ')
                                        except: pass
                                        print(f"  Prod {i+1}: Nom='{product_name}', Prix/Unité='{price_per_unit}'")
                                        all_product_data.append([category, postal_code_to_use, search_term, search_term, product_name, price_per_unit])
                            except TimeoutException: print(f"ERREUR (Étape 8 - '{search_term}'/{postal_code_to_use}): Timeout attente articles."); take_screenshot(driver, f"erreur_etape8_timeout_{postal_code_to_use}_{search_term[:10]}")
                            except Exception as e_extract: print(f"ERREUR extraction (Étape 8 - '{search_term}'/{postal_code_to_use}) : {e_extract}"); take_screenshot(driver, f"erreur_etape8_extract_{postal_code_to_use}_{search_term[:10]}")

                        # Gestion erreur PAR PRODUIT
                        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, Exception) as e_product:
                            print(f"\n!!! ERREUR produit '{search_term}' / CP {postal_code_to_use}. Skip produit. !!!"); print(f"Type: {type(e_product).__name__}, Msg: {e_product}"); print(f"{traceback.format_exc(limit=3)}"); take_screenshot(driver, f"erreur_produit_{postal_code_to_use}_{search_term[:10]}"); print("!!!\n")
                        finally:
                             print(f"Fin traitement '{search_term}'. Pause..."); time.sleep(0.1) # Pause entre produits

                    print(f"\n--- Fin boucle produits pour CP {postal_code_to_use} ---")
                else:
                    print(f"\nINFO [{postal_code_to_use}]: Magasin non sélectionné/trouvé. Skip recherche produits.")

            # *** Gestion erreur POUR UN CODE POSTAL ***
            except (WebDriverException, TimeoutException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException, Exception) as e_cp:
                 print(f"\n#######################################################")
                 print(f"ERREUR MAJEURE configuration/traitement CP {postal_code_to_use} (Cat: {category}).")
                 print(f"Type: {type(e_cp).__name__}"); print(f"Message: {e_cp}")
                 print(f"Traceback:\n{traceback.format_exc()}")
                 # Essayer de prendre une capture même si le driver est potentiellement KO
                 take_screenshot(driver, f"erreur_config_CP_{postal_code_to_use}")
                 print(f"Passage au code postal suivant.")
                 print(f"#######################################################\n")
                 # Le continue est implicite via la fin du bloc try

            # *** FINALLY POUR CHAQUE CODE POSTAL : FERMER LE NAVIGATEUR ***
            finally:
                print(f"Fin traitement CP {postal_code_to_use}.")
                if driver:
                    print("Fermeture instance WebDriver...")
                    try:
                        driver.quit()
                        print("WebDriver fermé.")
                    except WebDriverException as e_quit:
                        print(f"WARN: Erreur lors de la fermeture du WebDriver pour {postal_code_to_use}: {e_quit}")
                    except Exception as e_quit_generic:
                         print(f"WARN: Erreur générique lors de la fermeture du WebDriver pour {postal_code_to_use}: {e_quit_generic}")
                    finally:
                         driver = None # S'assurer que driver est None pour la prochaine itération
                         service = None # Réinitialiser service aussi
                else:
                    print("Aucune instance WebDriver à fermer (erreur initiale?).")
                print("Pause avant prochain CP...")
                time.sleep(0.1) # Pause plus longue entre les CP à cause du redémarrage

        print(f"\n=======================================================")
        print(f"=== FIN CATÉGORIE : {category} ===")
        print(f"=======================================================")

    print("\n--- Toutes les catégories et codes postaux traités ---")

    # --- ÉTAPE 9 : Écriture CSV FINALE (inchangée) ---
    print(f"\n--- Étape 9 : Écriture résultats CSV ---")
    if all_product_data:
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(script_dir, csv_filename)
            print(f"Écriture {len(all_product_data)} lignes dans : {csv_path}")
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csvwriter.writerow(['Categorie Ville', 'Code Postal', 'Terme Recherche', 'Produit Initial', 'Nom Produit Extrait', 'Prix par Kilo/Unité'])
                csvwriter.writerows(all_product_data)
            print(f"Données écrites avec succès dans '{csv_filename}'.")
        except IOError as e: print(f"ERREUR écriture CSV '{csv_filename}': {e}")
        except Exception as e_csv: print(f"ERREUR inattendue écriture CSV: {e_csv}\n{traceback.format_exc()}")
    else:
        print("Aucune donnée produit collectée. Fichier CSV non créé/modifié.")

# --- Gestion Erreur Globale (si qqch échoue avant/après les boucles) ---
except Exception as e_global:
    print(f"\n--- ERREUR FATALE GLOBALE (hors boucles principales) ---")
    print(f"Type: {type(e_global).__name__}"); print(f"Message: {e_global}")
    print(traceback.format_exc())
    # Essayer de prendre une capture si le driver existe encore (peu probable ici)
    if driver: take_screenshot(driver, "erreur_fatale_globale")

# --- Fin Script ---
finally:
    print("\n--- Fin programme ---")
    # Plus besoin de fermer le driver ici, car il est fermé après chaque CP
    # S'assurer qu'il n'y a pas d'instance résiduelle (ne devrait pas arriver)
    if driver:
        print("WARN: Instance driver détectée à la fin globale, tentative de fermeture...")
        try: driver.quit()
        except: pass
    print("Script terminé.")