import requests
from bs4 import BeautifulSoup
import re
import time

# Expression régulière pour trouver un code postal français (5 chiffres)
postal_code_regex = re.compile(r'\b(\d{5})\b')

def fetch_postal_codes_from_url(url, headers):
    """
    Récupère les codes postaux depuis l'URL donnée.
    """
    postal_codes = set()
    print(f"Tentative de récupération de la page : {url}")
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()  # Vérifier qu'il n'y a pas d'erreur HTTP
        print("Page récupérée avec succès.")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # On cherche tous les éléments <li> contenant les informations du magasin
        store_elements = soup.find_all('li', class_='store-list__store-wrapper')
        print(f"Nombre d'éléments de magasin trouvés : {len(store_elements)}")
        
        if not store_elements:
            print("Aucun élément 'store-list__store-wrapper' trouvé. La structure de la page a peut-être changé.")
            return postal_codes
        
        # Parcourir chaque magasin et extraire le code postal
        for store in store_elements:
            address_div = store.find('div', class_='place-pos__address')
            if address_div:
                address_text = address_div.get_text(separator=' ', strip=True)
                match = postal_code_regex.search(address_text)
                if match:
                    postal_code = match.group(1)
                    postal_codes.add(postal_code)
            else:
                print("Avertissement : Pas de div 'place-pos__address' trouvée dans un élément 'store-list__store-wrapper'.")
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête HTTP vers {url}: {e}")
    except Exception as e:
        print(f"Une erreur inattendue est survenue lors du traitement de {url}: {e}")
    
    return postal_codes

def process_urls(urls, headers):
    """
    Fonction récursive qui traite la liste des URL et renvoie l'union des codes postaux extraits.
    """
    if not urls:
        return set()
    # Traiter la première URL
    codes_first = fetch_postal_codes_from_url(urls[0], headers)
    # Appel récursif pour le reste de la liste
    codes_rest = process_urls(urls[1:], headers)
    return codes_first.union(codes_rest)

def main():
    # Liste des URL à traiter
    urls = [
        "https://www.auchan.fr/nos-magasins?types=LOCKERS",
        "https://www.auchan.fr/nos-magasins?types=PICKUP_POINT",
        "https://www.auchan.fr/nos-magasins?types=DRIVE"
    ]
    
    # User-Agent pour éviter d'être bloqué
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/91.0.4472.124 Safari/537.36')
    }
    
    # Récupération récursive des codes postaux
    postal_codes_found = process_urls(urls, headers)
    
    if not postal_codes_found:
        print("Aucun code postal n'a pu être extrait de toutes les URLs.")
    else:
        sorted_codes = sorted(postal_codes_found)
        print(f"\n{len(sorted_codes)} codes postaux uniques trouvés :")
        for code in sorted_codes:
            print(code)
        
        # Enregistrer la liste des codes postaux dans un fichier
        output_filename = "codes_postaux_auchan_lockers.txt"
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                for code in sorted_codes:
                    f.write(code + '\n')
            print(f"\nLes codes postaux ont été sauvegardés dans le fichier : '{output_filename}'")
        except IOError as e:
            print(f"Erreur lors de l'écriture dans le fichier {output_filename}: {e}")

if __name__ == "__main__":
    main()
