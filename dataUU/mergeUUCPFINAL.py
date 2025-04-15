import pandas as pd
import os
import numpy as np
import traceback # Pour un meilleur débogage des erreurs

def enrichir_donnees_complet():
    print("="*60)
    print("Démarrage de l'enrichissement complet (UU + Revenu)")
    print("="*60)

    # --- Configuration des Chemins ---
    # Références
    uu_file = "/Users/pierreandrews/Desktop/Prix conso/dataUU/UU.csv"
    uucp_file = "/Users/pierreandrews/Desktop/Prix conso/dataUU/UUCP.csv"
    revenu_file = "/Users/pierreandrews/Desktop/Prix conso/cc_filosofi_2021_COM.csv"

    # Données d'entrée (avec Code INSEE ajouté précédemment)
    data_dur_input_file = "/Users/pierreandrews/Desktop/Prix conso/CSV DUR/dataDUR_avec_insee.csv"
    data_relatif_input_file = "/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/dataRELATIF_avec_insee.csv"

    # Données de sortie (finales, avec UU et Revenu)
    output_dir_dur = os.path.dirname(data_dur_input_file)
    output_dur_final_file = os.path.join(output_dir_dur, "dataDUR_final.csv") # Nom explicite

    output_dir_relatif = os.path.dirname(data_relatif_input_file)
    output_relatif_final_file = os.path.join(output_dir_relatif, "dataRELATIF_final.csv") # Nom explicite

    # --- Configuration des Colonnes ---
    # Pour les données d'entrée
    colonne_insee_data = "Code INSEE" # Colonne INSEE dans les fichiers d'entrée

    # Pour UUCP et UU
    colonne_insee_uucp = "CODGEO" # Colonne INSEE dans UUCP
    colonne_uu2020 = "UU2020"
    colonnes_uu_details = ['TUU2017', 'TDUU2017', 'TYPE_UU2020']

    # Pour Revenu
    colonne_insee_revenu = "CODGEO" # Colonne INSEE dans le fichier revenu
    colonnes_revenu_details = ['MED21', 'RD21'] # Revenu médian, Ratio inter-décile

    print("--- Configuration ---")
    print(f"Fichier UU: {uu_file}")
    print(f"Fichier UUCP: {uucp_file}")
    print(f"Fichier Revenu: {revenu_file}")
    print(f"Fichier d'entrée DUR: {data_dur_input_file}")
    print(f"Fichier d'entrée RELATIF: {data_relatif_input_file}")
    print(f"Fichier de sortie DUR: {output_dur_final_file}")
    print(f"Fichier de sortie RELATIF: {output_relatif_final_file}")
    print(f"Colonne INSEE données: '{colonne_insee_data}'")
    print(f"Colonne INSEE UUCP: '{colonne_insee_uucp}'")
    print(f"Colonne INSEE Revenu: '{colonne_insee_revenu}'")
    print("-" * 30)

    # --- 1. Chargement et Préparation des Données de Référence ---

    # 1.a) Chargement UU (Détails des Unités Urbaines)
    print("1.a) Chargement du fichier UU...")
    try:
        uu_df = pd.read_csv(uu_file, sep=";", header=1, dtype=str)
        uu_selected = uu_df[[colonne_uu2020] + colonnes_uu_details].drop_duplicates(subset=[colonne_uu2020]).copy()
        uu_selected[colonne_uu2020] = uu_selected[colonne_uu2020].astype(str)
        print(f"  -> OK: {len(uu_selected)} infos UU uniques chargées.")
    except FileNotFoundError:
        print(f"  -> ERREUR: Fichier non trouvé: {uu_file}")
        return
    except Exception as e:
        print(f"  -> ERREUR lors de la lecture de {uu_file}: {e}")
        return

    # 1.b) Chargement UUCP (Correspondance INSEE <-> UU) + Gestion Arrondissements
    print("\n1.b) Chargement du fichier UUCP et préparation map INSEE <-> UU...")
    try:
        uucp_df = pd.read_csv(uucp_file, sep=";", header=1, dtype=str)
        if colonne_insee_uucp not in uucp_df.columns or colonne_uu2020 not in uucp_df.columns:
             print(f"  -> ERREUR: Colonnes '{colonne_insee_uucp}' ou '{colonne_uu2020}' non trouvées dans {uucp_file}")
             return

        insee_uu_map = uucp_df[[colonne_insee_uucp, colonne_uu2020]].copy()
        insee_uu_map = insee_uu_map.drop_duplicates(subset=[colonne_insee_uucp])
        print(f"  -> Map initiale INSEE->UU: {len(insee_uu_map)} entrées.")

        # --- Correction Arrondissements ---
        print("     Ajout correspondances arrondissements PLM...")
        arrondissements_a_ajouter = []
        communes_plm = {
            '75056': ('Paris', range(75101, 75121)),
            '69123': ('Lyon', range(69381, 69390)),
            '13055': ('Marseille', range(13201, 13217))
        }
        count_arr_added = 0
        for code_commune, (nom_ville, plage_arr) in communes_plm.items():
            commune_info = insee_uu_map[insee_uu_map[colonne_insee_uucp] == code_commune]
            if not commune_info.empty:
                uu_commune = commune_info[colonne_uu2020].iloc[0]
                # print(f"       -> Trouvé {nom_ville} ({code_commune}), UU: {uu_commune}")
                for code_arr in plage_arr:
                    arrondissements_a_ajouter.append({colonne_insee_uucp: str(code_arr), colonne_uu2020: uu_commune})
                    count_arr_added += 1
            # else:
                # print(f"       -> ATTENTION: {nom_ville} ({code_commune}) non trouvé dans UUCP.")

        if arrondissements_a_ajouter:
            df_arrondissements = pd.DataFrame(arrondissements_a_ajouter)
            insee_uu_map_final = pd.concat([insee_uu_map, df_arrondissements], ignore_index=True)
            insee_uu_map_final = insee_uu_map_final.drop_duplicates(subset=[colonne_insee_uucp], keep='first')
            print(f"     -> OK: {count_arr_added} lignes arrondissements ajoutées.")
            print(f"     -> Map finale INSEE->UU: {len(insee_uu_map_final)} entrées.")
        else:
            print("     -> Aucun arrondissement ajouté.")
            insee_uu_map_final = insee_uu_map
        # --- Fin Correction Arrondissements ---

    except FileNotFoundError:
        print(f"  -> ERREUR: Fichier non trouvé: {uucp_file}")
        return
    except Exception as e:
        print(f"  -> ERREUR lors de la préparation de la map INSEE <-> UU: {e}")
        traceback.print_exc()
        return

    # 1.c) Chargement Revenu (INSEE <-> Revenu)
    print("\n1.c) Chargement du fichier Revenu...")
    try:
        df_revenu = pd.read_csv(
            revenu_file,
            sep=';',
            usecols=[colonne_insee_revenu] + colonnes_revenu_details,
            na_values='s', # 's' signifie secret statistique, traité comme manquant
            dtype={colonne_insee_revenu: str}, # Code INSEE en texte
            decimal=',' # Séparateur décimal dans le fichier source
        )
        # Convertir les colonnes de revenu en numérique (après lecture)
        # errors='coerce' met NaN si la conversion échoue
        for col in colonnes_revenu_details:
             if col in df_revenu.columns:
                  df_revenu[col] = pd.to_numeric(df_revenu[col], errors='coerce')

        # Garder uniquement les lignes avec un code INSEE valide et dédoublonner
        df_revenu = df_revenu.dropna(subset=[colonne_insee_revenu])
        df_revenu = df_revenu.drop_duplicates(subset=[colonne_insee_revenu], keep='first')

        print(f"  -> OK: {len(df_revenu)} infos Revenu uniques chargées.")
        # print("     Types de données Revenu après conversion:")
        # print(df_revenu.dtypes)

    except FileNotFoundError:
        print(f"  -> ERREUR: Fichier non trouvé: {revenu_file}")
        return
    except ValueError as e:
         print(f"  -> ERREUR: Problème de conversion de données dans {revenu_file}. Détails: {e}")
         return
    except Exception as e:
        print(f"  -> ERREUR inattendue lors de la lecture de {revenu_file}: {e}")
        traceback.print_exc()
        return

    print("-" * 30)

    # --- 2. Traitement des Fichiers de Données ---

    fichiers_a_traiter = [
        {"input": data_dur_input_file, "output": output_dur_final_file, "input_sep": ','},
        {"input": data_relatif_input_file, "output": output_relatif_final_file, "input_sep": ','} # Assumer virgule aussi
    ]

    for config in fichiers_a_traiter:
        input_path = config["input"]
        output_path = config["output"]
        input_sep = config["input_sep"]
        print(f"\nTraitement du fichier : {os.path.basename(input_path)}")

        if not os.path.exists(input_path):
            print(f"  -> ERREUR: Fichier d'entrée non trouvé: {input_path}")
            continue # Passe au fichier suivant

        try:
            # 2.a) Charger le fichier de données d'entrée
            print(f"  2.a) Chargement...")
            df_data = pd.read_csv(input_path, sep=input_sep, dtype=str) # Lire tout en str initialement
            print(f"      -> {len(df_data)} lignes chargées.")

            if colonne_insee_data not in df_data.columns:
                print(f"      -> ERREUR: Colonne INSEE '{colonne_insee_data}' non trouvée.")
                continue
            # S'assurer que la colonne INSEE est bien string
            df_data[colonne_insee_data] = df_data[colonne_insee_data].astype(str).str.strip()


            # 2.b) Fusion avec les données UU
            print(f"  2.b) Fusion avec les données Unité Urbaine (via '{colonne_insee_data}' <-> '{colonne_insee_uucp}')...")
            df_merged_uu = pd.merge(
                df_data,
                insee_uu_map_final,
                left_on=colonne_insee_data,
                right_on=colonne_insee_uucp,
                how='left'
            )
            # Ajouter les détails UU
            df_merged_uu = pd.merge(
                df_merged_uu,
                uu_selected,
                on=colonne_uu2020,
                how='left'
            )
            match_count_uu = df_merged_uu[colonne_uu2020].notna().sum()
            print(f"      -> Correspondances UU trouvées: {match_count_uu} / {len(df_data)}")
            # Nettoyage colonne INSEE redondante si nécessaire
            if colonne_insee_uucp != colonne_insee_data and colonne_insee_uucp in df_merged_uu.columns:
                df_merged_uu = df_merged_uu.drop(columns=[colonne_insee_uucp])


            # 2.c) Fusion avec les données Revenu
            print(f"  2.c) Fusion avec les données Revenu (via '{colonne_insee_data}' <-> '{colonne_insee_revenu}')...")
            df_merged_final = pd.merge(
                df_merged_uu, # Partir du résultat précédent
                df_revenu,
                left_on=colonne_insee_data,
                right_on=colonne_insee_revenu,
                how='left'
            )
            match_count_revenu = df_merged_final['MED21'].notna().sum() # Utilise MED21 comme indicateur
            print(f"      -> Correspondances Revenu trouvées: {match_count_revenu} / {len(df_data)}")
            # Nettoyage colonne INSEE redondante si nécessaire
            if colonne_insee_revenu != colonne_insee_data and colonne_insee_revenu in df_merged_final.columns:
                df_merged_final = df_merged_final.drop(columns=[colonne_insee_revenu])


            # 2.d) Sauvegarde du fichier final enrichi
            print(f"  2.d) Sauvegarde du résultat final vers {output_path}...")
            # Utiliser la virgule comme séparateur et le point comme décimal par défaut pour la sortie
            df_merged_final.to_csv(output_path, sep=',', decimal='.', index=False, encoding='utf-8')
            print(f"      -> OK: Fichier sauvegardé.")


        except KeyError as e:
             print(f"  -> ERREUR (Clé Manquante): Vérifiez le nom de la colonne: {e}")
        except Exception as e:
            print(f"  -> ERREUR inattendue lors du traitement de {os.path.basename(input_path)}: {e}")
            traceback.print_exc()

    print("-" * 30)
    print("Opération d'enrichissement complet terminée.")

# --- Point d'entrée du script ---
if __name__ == "__main__":
    enrichir_donnees_complet()