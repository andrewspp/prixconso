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
        # 1. Charger le fichier CSV en spécifiant l'encodage ET le type de la colonne du code postal
        print(f"Chargement du fichier : {input_csv_path}")
        dtype_spec = {'postal_code_used': str} # --- AJOUT: Spécifier le type pour le code postal ---
        try:
            # --- MODIFICATION: Ajout de dtype=dtype_spec ---
            df = pd.read_csv(input_csv_path, encoding='utf-8', dtype=dtype_spec)
        except UnicodeDecodeError:
            print("Encodage UTF-8 échoué, essai avec latin-1...")
            # --- MODIFICATION: Ajout de dtype=dtype_spec ---
            df = pd.read_csv(input_csv_path, encoding='latin-1', dtype=dtype_spec)

        print(f"Fichier chargé. {len(df)} lignes initiales.")

        # --- AJOUT Optionnel mais recommandé ---
        # S'assurer que la colonne est bien de type string après lecture (gère les NaN éventuels)
        # Cela garantit la cohérence même si la lecture a rencontré des problèmes.
        if 'postal_code_used' in df.columns:
             df['postal_code_used'] = df['postal_code_used'].astype(str)
             # Vous pouvez décider comment traiter les NaN ici, par exemple les remplacer s'ils existent
             # df['postal_code_used'] = df['postal_code_used'].fillna('CP_MANQUANT') # Exemple
        else:
             print(f"AVERTISSEMENT: La colonne 'postal_code_used' spécifiée dans dtype n'existe pas dans le fichier {input_csv_path}.")
             # Gérer l'erreur ou adapter la suite du script si cette colonne est essentielle


        # 2. Filtrer les lignes où l'extraction a réussi et où un prix valide a été trouvé
        print("Filtrage des lignes valides...")
        df_success = df[df['success'] == True].copy() # .copy() pour éviter SettingWithCopyWarning
        # Vérifier si 'main_price' existe avant de l'utiliser
        if 'main_price' not in df_success.columns:
            print("ERREUR: Colonne 'main_price' non trouvée après le chargement initial.")
            return
        df_success['main_price'] = df_success['main_price'].astype(str)
        df_filtered = df_success[df_success['main_price'].str.contains('€', na=False)].copy()

        print(f"{len(df_filtered)} lignes valides trouvées après filtrage.")

        # Vérifier s'il reste des données valides
        if df_filtered.empty:
            print("Aucune donnée valide trouvée après filtrage. Le fichier de sortie sera vide.")
            pd.DataFrame().to_csv(output_csv_path, index=False, encoding='utf-8-sig') # Utiliser utf-8-sig pour Excel
            return

        # 3. Définir les colonnes d'identification uniques pour chaque magasin
        store_identifiers = ['postal_code_used', 'zone_type', 'selected_store']

        # Vérifier que les colonnes d'identification existent bien dans le DataFrame filtré
        missing_identifiers = [col for col in store_identifiers if col not in df_filtered.columns]
        if missing_identifiers:
            print(f"ERREUR: Colonnes d'identification manquantes dans les données filtrées: {missing_identifiers}. Vérifiez les noms et la présence dans le CSV.")
            # Tenter de continuer sans les colonnes manquantes ou arrêter
            store_identifiers = [col for col in store_identifiers if col in df_filtered.columns]
            if not store_identifiers:
                print("ERREUR: Aucune colonne d'identification valide restante.")
                return
            print(f"Continuation avec les identifiants restants: {store_identifiers}")

        # Vérifier que la colonne pour les nouvelles colonnes existe
        if 'product_name_debug' not in df_filtered.columns:
             print("ERREUR: Colonne 'product_name_debug' non trouvée pour créer les colonnes de produits.")
             return
        # Vérifier que la colonne pour les valeurs existe
        if 'main_price' not in df_filtered.columns:
             print("ERREUR: Colonne 'main_price' non trouvée pour les valeurs du pivot.")
             return


        # 4. Utiliser pivot_table pour transformer les données
        print("Pivotage de la table...")
        try:
            df_pivoted = df_filtered.pivot_table(
                index=store_identifiers,     # 'postal_code_used' sera utilisé comme chaîne ici
                columns='product_name_debug',
                values='main_price',
                aggfunc='first'              # Gestion des doublons éventuels
            )
        except Exception as pivot_error:
            print(f"ERREUR lors du pivotage : {pivot_error}")
            # Afficher des informations de débogage si nécessaire
            print("Vérification des doublons potentiels dans les index et colonnes pour un même magasin...")
            duplicates = df_filtered[df_filtered.duplicated(subset=store_identifiers + ['product_name_debug'], keep=False)]
            if not duplicates.empty:
                print("Doublons trouvés qui pourraient causer des problèmes avec aggfunc='first':")
                print(duplicates.head())
            return # Arrêter en cas d'erreur de pivot

        # 5. Nettoyer le résultat
        print("Nettoyage du résultat du pivot...")
        df_pivoted = df_pivoted.reset_index()
        # Remplacer les valeurs NaN (produit non trouvé dans ce magasin) par une chaîne vide
        df_pivoted = df_pivoted.fillna('') # Remplacer NaN par ''

        # (Optionnel) Renommer l'axe des colonnes
        df_pivoted.columns.name = None

        print(f"Transformation terminée. {len(df_pivoted)} lignes (magasins) dans le résultat.")
        # Afficher seulement quelques colonnes si la liste est très longue
        cols_to_show = list(df_pivoted.columns[:5]) + (['...'] if len(df_pivoted.columns) > 5 else [])
        print(f"Exemple de colonnes du résultat : {cols_to_show}")


        # 6. Sauvegarder le DataFrame transformé dans un nouveau fichier CSV
        print(f"Sauvegarde du résultat dans : {output_csv_path}")
        # Utiliser encoding='utf-8-sig' pour une meilleure compatibilité avec Excel (gère les accents et le BOM)
        df_pivoted.to_csv(output_csv_path, index=False, encoding='utf-8-sig')

        print("Script terminé avec succès.")

    except FileNotFoundError:
        print(f"ERREUR : Le fichier d'entrée '{input_csv_path}' n'a pas été trouvé.")
    except KeyError as e:
        print(f"ERREUR : Colonne manquante critique non gérée : {e}. Vérifiez les noms des colonnes dans le CSV ou dans le script.")
    except Exception as e:
        print(f"Une erreur inattendue est survenue : {e}")
        # Pour un débogage plus poussé, vous pouvez décommenter la ligne suivante
        # import traceback; traceback.print_exc()

# --- Définir les chemins des fichiers ---
input_file = '/Users/pierreandrews/Desktop/Prix conso/CSV DUR/auchan_prix_principal_multi_cp_zones_PARALLEL_v4_no_retry_hors_gamme.csv'
output_file = '/Users/pierreandrews/Desktop/Prix conso/CSV DUR/dataDUR.csv' # Nom de sortie légèrement modifié

# --- Exécuter la fonction ---
transform_auchan_prices(input_file, output_file)