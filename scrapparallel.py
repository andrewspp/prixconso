import time
import re # Importer re pour une éventuelle manipulation de texte plus tard
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys # <--- Importer Keys
from selenium.common.exceptions import ( # <--- Importer plus d'exceptions
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    ElementNotInteractableException
)
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
url_to_visit = "https://www.auchan.fr"
postal_code_to_use = "75015" # <--- Code postal à utiliser

# --- Selectors (inspirés de ton script) ---
cookie_accept_button_id = "onetrust-accept-btn-handler"
# XPath flexible pour le bouton initial (Afficher prix / Choisir magasin etc.)
initial_context_button_xpath = "//button[contains(., 'Afficher le prix') or contains(., 'Choisir mon magasin') or contains(., 'Retrait') or contains(., 'Livraison') or contains(@data-testid, 'delivery-method') or contains(@class, 'context-button')]"
# Sélecteurs possibles pour le champ code postal
postal_input_selectors = ["input#search-input", "input[placeholder*='postal']", "input[name*='postal']", "input[id*='postal']", "input[data-testid*='postal']", "input[aria-label*='postal']", "input.journeySearchInput"]
# XPath pour la liste des magasins qui apparaît
store_list_container_xpath = "//div[contains(@class, 'journeyPosItem') or contains(@class, 'journey-service-context__wrapper') or contains(@class, 'store-card__wrapper')]"
# XPath pour le bouton de sélection DANS un container de magasin
select_store_button_xpath = ".//button[contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'choisir') or contains(translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sélectionner') or contains(@data-testid,'choose-store') or contains(@class, 'selectButton')]"
# XPath pour obtenir le nom du magasin (pour info)
store_name_xpath = ".//span[contains(@class, 'place-pos__name')] | .//h3[contains(@class,'store-card__name')] | .//div[contains(@class,'shop-name')] | .//span[contains(@data-testid,'store-name')] | .//p[contains(@class,'name')]"


# --- Initialisation du WebDriver ---
print("Initialisation du WebDriver Chrome...")
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
# Pour éviter les popups de notifications Chrome qui peuvent gêner
chrome_options.add_argument("--disable-notifications")
# Autres options utiles de ton script
# chrome_options.add_argument("--headless")
chrome_options.add_argument('--log-level=3') # Moins de logs Selenium dans la console
# chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
chrome_options.add_argument('--lang=fr-FR')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Définir les waits après l'initialisation du driver
    wait = WebDriverWait(driver, 15) # Attente générale plus longue
    short_wait = WebDriverWait(driver, 7) # Attente plus courte
    print("WebDriver initialisé avec succès.")
except Exception as e:
    print(f"Erreur lors de l'initialisation du WebDriver : {e}")
    print("Assurez-vous que Google Chrome est installé et à jour.")
    exit()

# --- Début des actions ---
try:
    # --- Étape 1 : Aller sur le site ---
    print(f"Navigation vers : {url_to_visit}")
    driver.get(url_to_visit)
    print("Page chargée.")

    # --- Étape 2 : Accepter les cookies ---
    print("Tentative d'acceptation des cookies...")
    try:
        accept_button = short_wait.until(EC.element_to_be_clickable((By.ID, cookie_accept_button_id)))
        # Utiliser execute_script pour cliquer, parfois plus fiable
        driver.execute_script("arguments[0].click();", accept_button)
        print("Cookies acceptés.")
        time.sleep(1) # Petite pause pour que la bannière disparaisse visuellement
    except TimeoutException:
        print("Bannière cookies non trouvée ou déjà acceptée.")
    except Exception as e:
        print(f"Erreur (non bloquante) lors de l'acceptation des cookies : {e}")


    # --- Étape 3 : Cliquer sur le bouton "Choisir vos courses" / "Afficher le prix" ---
    print("Recherche du bouton initial de sélection de contexte (magasin/livraison)...")
    try:
        initial_button = wait.until(EC.element_to_be_clickable((By.XPATH, initial_context_button_xpath)))
        print("Bouton initial trouvé. Clic...")
        # Scroll vers le bouton et clic JS pour plus de robustesse
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", initial_button)
        time.sleep(0.5) # Laisse le temps au scroll de finir
        driver.execute_script("arguments[0].click();", initial_button)
        print("Clic sur le bouton initial effectué.")
        time.sleep(1) # Pause pour laisser la modale/le champ apparaître
    except TimeoutException:
        print(f"ERREUR: Le bouton initial ({initial_context_button_xpath}) n'a pas été trouvé ou cliquable.")
        raise # Propage l'erreur pour arrêter le script si cette étape échoue
    except ElementClickInterceptedException:
        print("ERREUR: Le clic sur le bouton initial a été intercepté (peut-être par un overlay).")
        # On pourrait essayer de recliquer ou attendre un peu plus ici si nécessaire
        raise
    except Exception as e:
        print(f"ERREUR inattendue lors du clic sur le bouton initial: {e}")
        raise

    # --- Étape 4 : Saisir le code postal ---
    print(f"Recherche du champ de saisie pour le code postal ({postal_code_to_use})...")
    postal_input_element = None
    try:
        # Essayer les différents sélecteurs pour trouver le champ
        for i, selector in enumerate(postal_input_selectors):
            try:
                print(f"  Essai avec le sélecteur: {selector}")
                # Attendre que l'élément soit visible
                postal_input_element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"Champ code postal trouvé avec '{selector}'.")
                break # Sortir de la boucle si trouvé
            except TimeoutException:
                if i == len(postal_input_selectors) - 1: # Si c'était le dernier essai
                     print("ERREUR: Aucun sélecteur n'a permis de trouver le champ code postal visible.")
                     raise # Propage l'erreur
                else:
                    print(f"  Sélecteur '{selector}' n'a pas fonctionné ou champ non visible.")
                    continue # Essayer le sélecteur suivant

        # Saisir le code postal
        postal_input_element.clear()
        time.sleep(0.3)
        postal_input_element.send_keys(postal_code_to_use)
        print(f"Code postal '{postal_code_to_use}' saisi.")
        time.sleep(1) # Laisse le temps aux suggestions/résultats de charger

    except TimeoutException:
        print(f"ERREUR: Impossible de trouver un champ de saisie de code postal visible après le clic initial.")
        raise
    except ElementNotInteractableException:
         print(f"ERREUR: Le champ code postal a été trouvé mais n'est pas interactif (peut-être caché ou désactivé).")
         raise
    except Exception as e:
        print(f"ERREUR inattendue lors de la saisie du code postal: {e}")
        raise

    # --- Étape 5 : Sélectionner le premier magasin/point relais ---
    print("Attente de la liste des magasins/points relais...")
    try:
        # Attendre qu'au moins un container de magasin soit présent
        store_list_wait = WebDriverWait(driver, 20) # Attente un peu plus longue ici si besoin
        store_containers = store_list_wait.until(
            EC.presence_of_all_elements_located((By.XPATH, store_list_container_xpath))
        )
        print(f"Liste de magasins trouvée ({len(store_containers)} élément(s)).")

        if not store_containers:
            print("ERREUR: La liste des magasins est vide après la saisie du code postal.")
            raise NoSuchElementException("Aucun container de magasin trouvé.")

        # Sélectionner le premier container
        first_store_container = store_containers[0]
        print("Sélection du premier élément de la liste.")

        # Essayer d'extraire le nom (pour information)
        first_store_name = "Nom non trouvé"
        try:
            name_element = first_store_container.find_element(By.XPATH, store_name_xpath)
            first_store_name = name_element.text.strip().replace('\n', ' ')
            print(f"Nom du premier élément: '{first_store_name}'")
        except NoSuchElementException:
            print("Impossible de récupérer le nom exact du premier élément.")

        # Trouver et cliquer sur le bouton "Choisir" / "Sélectionner" dans ce premier container
        print(f"Recherche du bouton de sélection dans le premier élément ('{first_store_name}')...")
        select_button = WebDriverWait(first_store_container, 10).until(
            EC.element_to_be_clickable((By.XPATH, select_store_button_xpath))
        )
        print("Bouton de sélection trouvé. Clic...")
        # Utiliser un clic JS pour plus de fiabilité
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", select_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", select_button)
        print(f"Premier magasin/point relais ('{first_store_name}') sélectionné.")
        time.sleep(2) # Pause pour voir le résultat de la sélection

    except TimeoutException:
        print("ERREUR: Timeout en attendant la liste des magasins ou le bouton de sélection.")
        # Vérifier si un message "aucun magasin" est apparu
        try:
            no_result_msg_xpath = "//*[contains(text(), 'Aucun magasin ne correspond') or contains(text(), 'Aucun point de retrait disponible') or contains(text(),'Aucun résultat')]"
            no_result_element = short_wait.until(EC.visibility_of_element_located((By.XPATH, no_result_msg_xpath)))
            print(f"Message trouvé indiquant l'absence de magasin: '{no_result_element.text.strip()}'")
        except TimeoutException:
            print("Aucun message spécifique 'aucun magasin' détecté non plus.")
        raise # Propage l'erreur de timeout initiale
    except NoSuchElementException as e:
        print(f"ERREUR: Impossible de trouver un élément nécessaire pour la sélection du magasin: {e}")
        raise
    except ElementClickInterceptedException:
        print(f"ERREUR: Le clic sur le bouton de sélection du magasin ('{first_store_name}') a été intercepté.")
        raise
    except Exception as e:
        print(f"ERREUR inattendue lors de la sélection du magasin: {e}")
        raise


except Exception as e:
    print(f"\n--- ERREUR FATALE DANS LE SCRIPT ---")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {e}")
    # Prendre une capture d'écran peut aider au débogage
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_file = f"erreur_auchan_{timestamp}.png"
        driver.save_screenshot(screenshot_file)
        print(f"Capture d'écran de l'erreur sauvegardée: {screenshot_file}")
    except Exception as screen_e:
        print(f"Impossible de prendre une capture d'écran: {screen_e}")


# --- Garde le navigateur ouvert pour les prochaines étapes ---
print("\nNavigateur ouvert. Sélection du magasin terminée (si succès). Prêt pour la prochaine étape.")
# Pour fermer manuellement plus tard :
input("Appuyez sur Entrée pour fermer le navigateur...")
print("Fermeture du navigateur...")
if 'driver' in locals() and driver:
    driver.quit()
print("Script terminé.")