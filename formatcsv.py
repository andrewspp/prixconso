import pandas as pd

def transform_auchan_prices(input_csv_path, output_csv_path):
    """
    Transforme les données de prix Auchan d'un format long (une ligne par produit/magasin)
    à un format large (une ligne par magasin, colonnes pour chaque prix de produit).

    Args:
        input_csv_path (str): Chemin vers le fichier CSV d'entrée.
        output_csv_path (str): Chemin pour sauvegarder le fichier CSV transformé.
    """
    try:
        # 1. Charger le fichier CSV en spécifiant l'encodage (souvent utf-8 ou latin-1 pour les caractères français)
        print(f"Chargement du fichier : {input_csv_path}")
        try:
            df = pd.read_csv(input_csv_path, encoding='utf-8')
        except UnicodeDecodeError:
            print("Encodage UTF-8 échoué, essai avec latin-1...")
            df = pd.read_csv(input_csv_path, encoding='latin-1')

        print(f"Fichier chargé. {len(df)} lignes initiales.")

        # 2. Filtrer les lignes où l'extraction a réussi et où un prix valide a été trouvé
        #    On ne garde que les lignes où success == True et main_price contient '€'
        #    Convertir main_price en string pour être sûr de pouvoir utiliser .str
        df_success = df[df['success'] == True].copy() # .copy() pour éviter SettingWithCopyWarning
        df_success['main_price'] = df_success['main_price'].astype(str)
        df_filtered = df_success[df_success['main_price'].str.contains('€', na=False)].copy()

        print(f"{len(df_filtered)} lignes valides trouvées après filtrage.")

        # Vérifier s'il reste des données valides
        if df_filtered.empty:
            print("Aucune donnée valide trouvée après filtrage. Le fichier de sortie sera vide.")
            # Créer un fichier vide ou simplement ne rien faire
            pd.DataFrame().to_csv(output_csv_path, index=False, encoding='utf-8')
            return

        # 3. Définir les colonnes d'identification uniques pour chaque magasin
        #    Ici, 'postal_code_used', 'selected_store', et 'zone_type' semblent appropriés.
        store_identifiers = ['postal_code_used', 'zone_type', 'selected_store']

        # 4. Utiliser pivot_table pour transformer les données
        #    - index : les colonnes qui identifieront chaque ligne (les magasins)
        #    - columns : la colonne dont les valeurs deviendront les nouvelles colonnes (les noms de produits)
        #    - values : la colonne dont les valeurs rempliront les nouvelles cellules (les prix)
        #    - aggfunc='first' : si jamais il y a des doublons (même produit/même magasin), on prend la première valeur rencontrée.
        print("Pivotage de la table...")
        df_pivoted = df_filtered.pivot_table(
            index=store_identifiers,
            columns='product_name_debug',
            values='main_price',
            aggfunc='first'  # ou 'last', 'mean' si pertinent, mais 'first' est sûr ici
        )

        # 5. Nettoyer le résultat
        #    - Réinitialiser l'index pour que les identifiants de magasin redeviennent des colonnes normales.
        df_pivoted = df_pivoted.reset_index()
        #    - Remplacer les valeurs NaN (produit non trouvé dans ce magasin) par une chaîne vide ou un autre marqueur si vous préférez.
        df_pivoted = df_pivoted.fillna('') # Remplacer NaN par ''

        #    - (Optionnel) Renommer l'axe des colonnes si 'product_name_debug' est resté comme nom
        df_pivoted.columns.name = None

        print(f"Transformation terminée. {len(df_pivoted)} lignes (magasins) dans le résultat.")
        print(f"Colonnes du résultat : {list(df_pivoted.columns)}")

        # 6. Sauvegarder le DataFrame transformé dans un nouveau fichier CSV
        print(f"Sauvegarde du résultat dans : {output_csv_path}")
        df_pivoted.to_csv(output_csv_path, index=False, encoding='utf-8') # index=False pour ne pas écrire l'index pandas dans le fichier

        print("Script terminé avec succès.")

    except FileNotFoundError:
        print(f"ERREUR : Le fichier d'entrée '{input_csv_path}' n'a pas été trouvé.")
    except KeyError as e:
        print(f"ERREUR : Colonne manquante dans le fichier CSV : {e}. Vérifiez les noms des colonnes.")
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")

# --- Définir les chemins des fichiers ---
# Assurez-vous que le chemin d'entrée est correct
input_file = '/Users/pierreandrews/Desktop/Prix conso/auchan_prix_principal_multi_cp_zones_PARALLEL_v4_no_retry_hors_gamme.csv'

# Choisissez un nom pour votre fichier de sortie
output_file = '/Users/pierreandrews/Desktop/Prix conso/auchan_prix_par_magasin_produits_en_colonne.csv'

# --- Exécuter la fonction ---
transform_auchan_prices(input_file, output_file)