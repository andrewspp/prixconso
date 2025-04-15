import pandas as pd
import os

# --- Configuration ---
# Définir les chemins vers les fichiers
path_data_dur = "/Users/pierreandrews/Desktop/Prix conso/CSV DUR/dataDUR.csv"
path_data_relatif = "/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/dataRELATIF.csv"
path_correspondance = "/Users/pierreandrews/Desktop/Prix conso/correspondanceCPINSEE.csv"

# Définir les noms des fichiers de sortie
output_data_dur = "/Users/pierreandrews/Desktop/Prix conso/CSV DUR/dataDUR_avec_insee.csv"
output_data_relatif = "/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/dataRELATIF_avec_insee.csv"

# Noms des colonnes clés (attention à la casse)
colonne_cp_dur = "postal_code_used"
colonne_cp_relatif = "Code Postal"
colonne_cp_corr = "Code Postal"
colonne_insee_corr = "Code INSEE"

# --- Traitement ---

print("Début du script...")

try:
    # 1. Charger et préparer la table de correspondance
    print(f"Chargement du fichier de correspondance: {path_correspondance}")
    df_correspondance_raw = pd.read_csv(
        path_correspondance,
        sep=';',
        usecols=[colonne_cp_corr, colonne_insee_corr],
        dtype={colonne_cp_corr: str, colonne_insee_corr: str} # Lire comme texte
    )
    print(f"  -> {len(df_correspondance_raw)} lignes brutes chargées depuis la correspondance.")

    # --- Adaptation pour les codes postaux multiples ---
    print("Traitement des codes postaux multiples (séparés par '/') dans la correspondance...")
    # 1. Séparer les codes postaux dans une liste
    #    - .str.split('/') crée une liste de codes pour chaque ligne
    #    - .fillna('') remplace les NaN (s'il y en a) par une liste vide pour éviter les erreurs
    #    - On crée une nouvelle colonne temporaire pour ne pas modifier l'originale pendant l'itération implicite
    df_correspondance_raw['CP_List'] = df_correspondance_raw[colonne_cp_corr].str.split('/')

    # 2. "Exploser" le DataFrame : crée une nouvelle ligne pour chaque élément de la liste
    #    - Les autres colonnes (Code INSEE) sont dupliquées pour chaque nouveau code postal
    df_correspondance_exploded = df_correspondance_raw.explode('CP_List')
    print(f"  -> {len(df_correspondance_exploded)} lignes après dépliage des codes postaux multiples.")

    # 3. Nettoyer les codes postaux individuels (enlever les espaces avant/après)
    df_correspondance_exploded['CP_Individual'] = df_correspondance_exploded['CP_List'].str.strip()

    # 4. Garder seulement les colonnes utiles et renommer
    df_correspondance_prepared = df_correspondance_exploded[[colonne_insee_corr, 'CP_Individual']].copy()
    df_correspondance_prepared.rename(columns={'CP_Individual': colonne_cp_corr}, inplace=True)

    # 5. Supprimer les lignes où le code postal serait vide après le split/strip
    df_correspondance_prepared = df_correspondance_prepared[df_correspondance_prepared[colonne_cp_corr].str.len() > 0]

    # 6. Gérer les doublons potentiels : après l'explosion, un CP individuel peut toujours
    #    pointer vers plusieurs INSEE (moins probable mais possible), ou plusieurs lignes
    #    originales pouvaient donner le même (CP, INSEE) après explosion.
    #    On garde la première correspondance INSEE trouvée pour chaque CP individuel.
    df_correspondance = df_correspondance_prepared.drop_duplicates(subset=[colonne_cp_corr], keep='first')
    print(f"  -> {len(df_correspondance)} correspondances uniques CP individuel -> INSEE conservées après traitement.")
    # --- Fin de l'adaptation ---


    # 2. Traiter le premier fichier (dataDUR.csv)
    print("-" * 30)
    print(f"Traitement du fichier: {path_data_dur}")
    if os.path.exists(path_data_dur):
        try:
            df_dur = pd.read_csv(
                path_data_dur,
                sep=',', # Assumer virgule
                dtype={colonne_cp_dur: str}
            )
            print(f"  -> {len(df_dur)} lignes chargées.")

            # La jointure utilise maintenant df_correspondance qui a été préparé
            df_dur_merged = pd.merge(
                df_dur,
                df_correspondance, # Utilise la table préparée
                left_on=colonne_cp_dur,
                right_on=colonne_cp_corr,
                how='left'
            )

            # La colonne Code Postal de droite n'est plus utile après la jointure
            if colonne_cp_corr in df_dur_merged.columns and colonne_cp_corr != colonne_cp_dur:
                 df_dur_merged = df_dur_merged.drop(columns=[colonne_cp_corr])

            insee_found_dur = df_dur_merged[colonne_insee_corr].notna().sum()
            print(f"  -> {insee_found_dur} correspondances INSEE trouvées sur {len(df_dur)} lignes.")
            if insee_found_dur < len(df_dur):
                 missing_cp_dur = df_dur_merged[df_dur_merged[colonne_insee_corr].isna()][colonne_cp_dur].unique()
                 print(f"  -> ATTENTION: {len(df_dur) - insee_found_dur} lignes n'ont pas trouvé de code INSEE correspondant.")
                 # print(f"     Codes postaux sans correspondance trouvée : {list(missing_cp_dur)}")

            print(f"Sauvegarde du résultat dans: {output_data_dur}")
            df_dur_merged.to_csv(output_data_dur, index=False, encoding='utf-8', sep=',')
            print("  -> Fichier sauvegardé.")

        except pd.errors.ParserError as pe:
             print(f"ERREUR LORS DE LA LECTURE de {path_data_dur}: {pe}")
             print("Vérifiez le délimiteur (sep=',') et la structure du fichier CSV.")
        except KeyError as e:
            print(f"ERREUR (KeyError) lors du traitement de {path_data_dur}: La colonne '{e}' n'a pas été trouvée.")
            print(f"Vérifiez que la colonne '{colonne_cp_dur}' existe bien dans {path_data_dur} avec exactement ce nom.")
        except Exception as e_inner:
             print(f"Une erreur est survenue lors du traitement de {path_data_dur}: {e_inner}")

    else:
        print(f"ERREUR: Le fichier {path_data_dur} n'a pas été trouvé.")


    # 3. Traiter le deuxième fichier (dataRELATIF.csv)
    print("-" * 30)
    print(f"Traitement du fichier: {path_data_relatif}")
    if os.path.exists(path_data_relatif):
         try:
            df_relatif = pd.read_csv(
                path_data_relatif,
                sep=';', # Utiliser le séparateur correct pour ce fichier
                dtype={colonne_cp_relatif: str}
            )
            print(f"  -> {len(df_relatif)} lignes chargées.")

            # La jointure utilise aussi df_correspondance préparé
            df_relatif_merged = pd.merge(
                df_relatif,
                df_correspondance, # Utilise la table préparée
                left_on=colonne_cp_relatif,
                right_on=colonne_cp_corr,
                how='left'
            )

            if colonne_cp_corr in df_relatif_merged.columns and colonne_cp_corr != colonne_cp_relatif:
                 df_relatif_merged = df_relatif_merged.drop(columns=[colonne_cp_corr])

            insee_found_relatif = df_relatif_merged[colonne_insee_corr].notna().sum()
            print(f"  -> {insee_found_relatif} correspondances INSEE trouvées sur {len(df_relatif)} lignes.")
            if insee_found_relatif < len(df_relatif):
                 missing_cp_relatif = df_relatif_merged[df_relatif_merged[colonne_insee_corr].isna()][colonne_cp_relatif].unique()
                 print(f"  -> ATTENTION: {len(df_relatif) - insee_found_relatif} lignes n'ont pas trouvé de code INSEE correspondant.")
                 # print(f"     Codes postaux sans correspondance trouvée : {list(missing_cp_relatif)}")

            print(f"Sauvegarde du résultat dans: {output_data_relatif}")
            df_relatif_merged.to_csv(output_data_relatif, index=False, encoding='utf-8', sep=',') # Sortie en CSV standard (virgule)
            print("  -> Fichier sauvegardé.")

         except pd.errors.ParserError as pe:
             print(f"ERREUR LORS DE LA LECTURE de {path_data_relatif}: {pe}")
             print("Vérifiez le délimiteur (paramètre 'sep') et la structure du fichier CSV, en particulier autour de la ligne mentionnée dans l'erreur.")
         except KeyError as e:
            print(f"ERREUR (KeyError) lors du traitement de {path_data_relatif}: La colonne '{e}' n'a pas été trouvée.")
            print(f"Vérifiez que la colonne '{colonne_cp_relatif}' existe bien dans {path_data_relatif} avec exactement ce nom.")
         except Exception as e_inner:
            print(f"Une erreur inattendue est survenue lors du traitement de {path_data_relatif}: {e_inner}")

    else:
        print(f"ERREUR: Le fichier {path_data_relatif} n'a pas été trouvé.")


except FileNotFoundError as e:
    print(f"ERREUR: Le fichier suivant n'a pas été trouvé : {e.filename}")
except KeyError as e:
    print(f"ERREUR: La colonne suivante n'a pas été trouvée lors du chargement initial ou de la fusion : {e}")
    print("Vérifiez les noms des colonnes (colonne_cp_dur, colonne_cp_relatif, colonne_cp_corr, colonne_insee_corr) dans le script et dans vos fichiers CSV.")
except Exception as e:
    print(f"Une erreur globale inattendue est survenue: {e}")

print("-" * 30)
print("Script terminé.")