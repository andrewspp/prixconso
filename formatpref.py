import pandas as pd
import re

# Chemin du fichier source
input_file = "/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/prix_produits_auchan_parallel_8_workers.csv"
# Chemin pour le fichier de sortie
output_file = "/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/dataRELATIF.csv"

# --- MODIFICATION ICI ---
# Lire le fichier CSV en spécifiant le type de la colonne 'Code Postal' comme chaîne (str)
# Cela garantit que les zéros non significatifs sont conservés
df = pd.read_csv(input_file, sep=';', dtype={'Code Postal': str})
# --- FIN DE LA MODIFICATION ---

# S'assurer que les codes postaux sont bien des chaînes (double vérification, peut être utile si des NaN existent)
df['Code Postal'] = df['Code Postal'].astype(str)

# Collecter tous les termes de recherche uniques
termes_uniques = df['Terme Recherche'].unique()

# Fonction pour extraire la valeur numérique du prix
def extraire_prix(prix_texte):
    if pd.isna(prix_texte) or prix_texte == "Prix/Unité non trouvé":
        return None
    # Extraire la partie numérique (avant € ou / et remplacer , par .)
    match = re.search(r'(\d+[,]\d+)', str(prix_texte)) # Convertir en str pour éviter les erreurs si non-string
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

# Fonction pour extraire l'unité (kg, l, pce)
def extraire_unite(prix_texte):
    if pd.isna(prix_texte) or prix_texte == "Prix/Unité non trouvé":
        return None
    match = re.search(r'/ (\w+)', str(prix_texte)) # Convertir en str pour éviter les erreurs si non-string
    if match:
        return match.group(1)
    # Ajout pour gérer les cas comme "Prix/Unité" sans unité spécifiée après /
    if isinstance(prix_texte, str) and '/' in prix_texte and len(prix_texte.split('/')) > 1 and prix_texte.split('/')[1].strip() == '':
         return 'unité' # Ou une autre valeur par défaut si pertinent
    return None # Retourner None si aucune unité n'est trouvée

# Prétraiter le DataFrame pour extraire les prix numériques et les unités
df['Prix_Numerique'] = df['Prix par Kilo/Unité'].apply(extraire_prix)
df['Unite'] = df['Prix par Kilo/Unité'].apply(extraire_unite)

# Créer une liste pour stocker les données réorganisées
# Créer une liste pour stocker les données réorganisées
reorganised_data = []

# Grouper par Code Postal et Nom Magasin
# Comme 'Code Postal' est maintenant une chaîne, le groupement conservera les zéros
grouped = df.groupby(['Code Postal', 'Nom Magasin Sélectionné'])

for (code_postal, magasin), group in grouped:
    # --- CORRECTION ICI ---
    # Récupérer la Catégorie Ville pour ce groupe en utilisant iloc[0]
    # car .first() nécessite un argument 'offset' et n'est pas approprié ici.
    categorie_ville = group['Categorie Ville'].iloc[0]
    # --- FIN DE LA CORRECTION ---

    # Créer deux lignes pour ce magasin
    row1 = {
        'Categorie Ville': categorie_ville,
        'Code Postal': code_postal, # code_postal est maintenant une chaîne avec le zéro potentiel
        'Nom Magasin': magasin,
        'Ligne': 1
    }

    row2 = {
        'Categorie Ville': categorie_ville,
        'Code Postal': code_postal, # code_postal est maintenant une chaîne avec le zéro potentiel
        'Nom Magasin': magasin,
        'Ligne': 2
    }

    # Pour chaque terme, ajouter les produits et prix correspondants
    for terme in termes_uniques:
        # Filtrer le groupe actuel pour le terme spécifique
        produits_terme = group[group['Terme Recherche'] == terme]

        # Trier par un critère si nécessaire (par exemple, par index original ou prix)
        # produits_terme = produits_terme.sort_values(by='Nom Produit Extrait') # Exemple

        if len(produits_terme) >= 2:
            # Premier produit dans la première ligne
            produit1 = produits_terme.iloc[0]
            row1[f"{terme}_Produit"] = produit1['Nom Produit Extrait']
            row1[f"{terme}_Prix"] = produit1['Prix_Numerique']
            row1[f"{terme}_Unite"] = produit1['Unite']

            # Deuxième produit dans la deuxième ligne
            produit2 = produits_terme.iloc[1]
            row2[f"{terme}_Produit"] = produit2['Nom Produit Extrait']
            row2[f"{terme}_Prix"] = produit2['Prix_Numerique']
            row2[f"{terme}_Unite"] = produit2['Unite']

        elif len(produits_terme) == 1:
            # S'il n'y a qu'un seul produit, le mettre dans la première ligne
            produit1 = produits_terme.iloc[0]
            row1[f"{terme}_Produit"] = produit1['Nom Produit Extrait']
            row1[f"{terme}_Prix"] = produit1['Prix_Numerique']
            row1[f"{terme}_Unite"] = produit1['Unite']

            # Cellules vides pour la deuxième ligne
            row2[f"{terme}_Produit"] = None
            row2[f"{terme}_Prix"] = None
            row2[f"{terme}_Unite"] = None
        else:
            # Pas de produit pour ce terme dans ce magasin
            row1[f"{terme}_Produit"] = None
            row1[f"{terme}_Prix"] = None
            row1[f"{terme}_Unite"] = None

            row2[f"{terme}_Produit"] = None
            row2[f"{terme}_Prix"] = None
            row2[f"{terme}_Unite"] = None

    # Ajouter les deux lignes aux données réorganisées
    reorganised_data.append(row1)
    reorganised_data.append(row2)

# Créer un dataframe avec les données réorganisées
df_reorganised = pd.DataFrame(reorganised_data)

# Organiser l'ordre des colonnes
colonnes_base = ['Categorie Ville', 'Code Postal', 'Nom Magasin', 'Ligne']
colonnes_termes = []
for terme in termes_uniques:
    colonnes_termes.extend([f"{terme}_Produit", f"{terme}_Prix", f"{terme}_Unite"])

# S'assurer que l'ordre des termes est cohérent si nécessaire
# termes_uniques_tries = sorted(list(termes_uniques)) # Optionnel: trier les termes alphabétiquement
# colonnes_termes = []
# for terme in termes_uniques_tries:
#    colonnes_termes.extend([f"{terme}_Produit", f"{terme}_Prix", f"{terme}_Unite"])


df_reorganised = df_reorganised[colonnes_base + colonnes_termes]

# Écrire le dataframe réorganisé dans un nouveau fichier CSV
# L'écriture CSV de pandas gère correctement les chaînes (y compris celles commençant par zéro)
df_reorganised.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig') # Ajout de l'encoding utf-8-sig pour meilleure compatibilité Excel

print(f"Fichier réorganisé enregistré sous : {output_file}")