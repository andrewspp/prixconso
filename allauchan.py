import requests
from bs4 import BeautifulSoup
import re
import time

# URL de la page Auchan Drive
url = "https://www.auchan.fr/nos-magasins?types=LOCKERS"

# Nom du fichier de sortie
output_filename = "codes_postaux_auchan_lockers.txt"

# Utiliser un User-Agent commun pour éviter d'être bloqué
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Expression régulière pour trouver un code postal français (5 chiffres)
# \b assure qu'on ne prend pas une partie d'un nombre plus grand
postal_code_regex = re.compile(r'\b(\d{5})\b')

print(f"Tentative de récupération de la page : {url}")

try:
    # Effectuer la requête GET pour obtenir le contenu HTML
    response = requests.get(url, headers=headers, timeout=20) # Ajout d'un timeout
    response.raise_for_status()  # Lève une exception pour les codes d'erreur HTTP (4xx ou 5xx)
    print("Page récupérée avec succès.")

    # Analyser le HTML avec BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Trouver tous les éléments li avec la classe 'store-list__store-wrapper'
    # Ces éléments semblent contenir les informations de chaque magasin
    store_elements = soup.find_all('li', class_='store-list__store-wrapper')
    print(f"Nombre d'éléments de magasin trouvés : {len(store_elements)}")

    if not store_elements:
        print("Aucun élément 'store-list__store-wrapper' trouvé. La structure de la page a peut-être changé.")
        print("Vérifiez le code source de la page ou essayez d'ajuster les sélecteurs CSS.")
        exit() # Quitter si aucun magasin n'est trouvé

    # Utiliser un set pour stocker les codes postaux uniques
    postal_codes_found = set()

    # Parcourir chaque élément de magasin trouvé
    for store in store_elements:
        # Chercher la div contenant l'adresse à l'intérieur de l'élément magasin
        address_div = store.find('div', class_='place-pos__address')
        if address_div:
            # Récupérer tout le texte de la div d'adresse
            address_text = address_div.get_text(separator=' ', strip=True)
            # Chercher le motif du code postal dans le texte de l'adresse
            match = postal_code_regex.search(address_text)
            if match:
                # Ajouter le code postal trouvé (le premier groupe capturé par le regex) à notre set
                postal_code = match.group(1)
                postal_codes_found.add(postal_code)
                # print(f"Code postal trouvé : {postal_code} dans l'adresse : '{address_text}'") # Décommenter pour le débogage
        else:
             print(f"Avertissement : Pas de div 'place-pos__address' trouvée dans un élément 'store-list__store-wrapper'.")


    # Vérifier si des codes postaux ont été trouvés
    if not postal_codes_found:
        print("Aucun code postal n'a pu être extrait.")
        print("Cela peut être dû à un changement de structure de la page ou au ciblage incorrect des éléments.")
    else:
        print(f"\n{len(postal_codes_found)} codes postaux uniques trouvés.")

        # Convertir le set en liste et trier les codes postaux
        sorted_codes = sorted(list(postal_codes_found))

        # Écrire les codes postaux triés dans le fichier texte
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                for code in sorted_codes:
                    f.write(code + '\n')
            print(f"Les codes postaux ont été sauvegardés dans le fichier : '{output_filename}'")
        except IOError as e:
            print(f"Erreur lors de l'écriture dans le fichier {output_filename}: {e}")

except requests.exceptions.RequestException as e:
    print(f"Erreur lors de la requête HTTP vers {url}: {e}")
except Exception as e:
    print(f"Une erreur inattendue est survenue : {e}")