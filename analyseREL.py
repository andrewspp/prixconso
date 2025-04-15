import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings

# Ignorer certains avertissements fréquents mais souvent bénins avec geopandas/matplotlib
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning) # Pour les warnings de matplotlib sur les polices

# --- Configuration des Chemins ---
cleaned_csv_path = '/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/dataRELATIF_nettoye.csv'
geojson_path = '/Users/pierreandrews/Desktop/Prix conso/departements.geojson'
output_directory = '/Users/pierreandrews/Desktop/Prix conso/resultats_analyse_prix'

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(output_directory, exist_ok=True)
print(f"Les résultats seront enregistrés dans : {output_directory}")

# --- 1. Chargement et Préparation des Données ---
print("Chargement et préparation des données...")
try:
    # Charger en sautant la ligne de compte (maintenant à l'index 0 après l'en-tête)
    # Il faut dire à pandas que la ligne 0 est l'en-tête, et skipper la ligne 1 (index 0 des données)
    df = pd.read_csv(cleaned_csv_path, delimiter=';', skiprows=[1], low_memory=False, dtype=str)
    print(f"Chargement initial: {df.shape[0]} lignes.")

    # Remplacer les cellules vides ou contenant seulement des espaces par NaN (au cas où)
    df = df.replace(r'^\s*$', np.nan, regex=True)

    # Identifier les colonnes de prix
    price_cols = [col for col in df.columns if col.endswith('_Prix')]

    # Convertir les colonnes de prix en numérique
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            print(f"Avertissement: Colonne prix {col} non trouvée lors de la conversion.")

    print("Conversion des prix en numérique terminée.")

    # Gérer les doublons par Code Postal en moyennant les prix
    # Colonnes à agréger avec la moyenne
    agg_funcs_mean = {price_col: 'mean' for price_col in price_cols if price_col in df.columns}
    # Colonnes à conserver (prendre la première occurrence)
    # Utiliser les colonnes réellement présentes dans le df
    first_cols_to_keep = ['Categorie Ville', 'Code Postal', 'Nom Magasin']
    present_first_cols = [col for col in first_cols_to_keep if col in df.columns]
    agg_funcs_first = {col: 'first' for col in present_first_cols}

    # Combiner les fonctions d'agrégation
    agg_funcs = {**agg_funcs_mean, **agg_funcs_first}

    if 'Code Postal' in df.columns:
        print("Agrégation des données par Code Postal (calcul de la moyenne des prix)...")
        df_agg = df.groupby('Code Postal', as_index=False).agg(agg_funcs)
        print(f"Données agrégées: {df_agg.shape[0]} lignes uniques par Code Postal.")
    else:
        print("Erreur: Colonne 'Code Postal' non trouvée. Impossible d'agréger.")
        exit() # Arrêter si le code postal manque

    # Extraire le code département (en s'assurant que 'Code Postal' est une chaîne)
    df_agg['Code Postal'] = df_agg['Code Postal'].astype(str).str.zfill(5) # Assurer 5 chiffres avec zéro devant si besoin
    df_agg['Departement'] = df_agg['Code Postal'].str[:2]

    # Traitement spécifique Corse (si nécessaire, ajuste selon le format de ton GeoJSON)
    df_agg['Departement'] = df_agg['Departement'].replace({'20': '2A'}, regex=False) # Hypothèse: 20 devient 2A/2B basé sur la suite? Simplification pour le moment.
    # Si le GeoJSON utilise '2A' et '2B', il faudra une logique plus fine pour distinguer les codes postaux corses.
    # Pour l'instant, on part du principe que le GeoJSON utilise les codes numériques ou que '2A'/'2B' sont gérés correctement.

    print("Codes Département extraits.")
    print("Distribution des catégories de ville après agrégation:")
    if 'Categorie Ville' in df_agg.columns:
        print(df_agg['Categorie Ville'].value_counts())
    else:
        print("Colonne 'Categorie Ville' non trouvée après agrégation.")


except FileNotFoundError:
    print(f"Erreur : Le fichier '{cleaned_csv_path}' n'a pas été trouvé.")
    exit()
except pd.errors.EmptyDataError:
     print(f"Erreur : Le fichier '{cleaned_csv_path}' est vide ou ne contient pas de données après skip.")
     exit()
except Exception as e:
    print(f"Une erreur est survenue lors du chargement/préparation : {e}")
    import traceback
    traceback.print_exc()
    exit()

# --- 2. Chargement des Données Géographiques ---
print("\nChargement des données géographiques...")
try:
    gdf_departements = gpd.read_file(geojson_path)
    # Vérifier le nom de la colonne code département et la renommer si besoin
    if 'code' in gdf_departements.columns:
         gdf_departements = gdf_departements.rename(columns={'code': 'Departement'})
    elif 'CODE_DEPT' in gdf_departements.columns:
         gdf_departements = gdf_departements.rename(columns={'CODE_DEPT': 'Departement'})
    # Ajouter d'autres vérifications si nécessaire
    if 'Departement' not in gdf_departements.columns:
        print("Erreur: Colonne de code département non trouvée dans le GeoJSON ('code' ou 'CODE_DEPT' attendu).")
        print("Colonnes disponibles:", gdf_departements.columns)
        exit()
    print("GeoJSON chargé.")
    print("CRS initial:", gdf_departements.crs) # Afficher le système de coordonnées
    # Reprojeter si nécessaire (WGS84 est courant pour la visualisation web, Lambert93 pour la France métropolitaine)
    # gdf_departements = gdf_departements.to_crs(epsg=4326) # Exemple pour WGS84
    # print("CRS après reprojection:", gdf_departements.crs)

except FileNotFoundError:
    print(f"Erreur : Le fichier '{geojson_path}' n'a pas été trouvé.")
    exit()
except Exception as e:
    print(f"Une erreur est survenue lors du chargement du GeoJSON : {e}")
    exit()

# --- 3. Fusion des Données ---
print("\nFusion des données de prix avec les données géographiques...")
# S'assurer que la colonne de jointure a le même type
gdf_departements['Departement'] = gdf_departements['Departement'].astype(str)
df_agg['Departement'] = df_agg['Departement'].astype(str)

# Effectuer la fusion
gdf_merged = gdf_departements.merge(df_agg, on='Departement', how='left')
print("Fusion terminée.")

# --- 4. Analyses et Visualisations ---
print("\nDébut des analyses et visualisations...")

# Sélectionner quelques produits clés pour les visualisations détaillées
produits_cles = [
    "Lait demi-écrémé",
    "Oeufs de poules élevées",
    "Yaourts nature",
    "Camembert",
    "Beurre doux",
    "Spaghetti",
    "Pommes Golden",
    "Filet Blanc de poulet"
]
# Filtrer pour garder seulement les colonnes prix des produits clés pour certaines analyses
prix_cols_cles = [f"{p}_Prix" for p in produits_cles if f"{p}_Prix" in df_agg.columns]

# a) Statistiques Descriptives
print("  - Calcul des statistiques descriptives...")
stats_desc = df_agg[price_cols].describe()
stats_desc_path = os.path.join(output_directory, 'statistiques_descriptives_prix.csv')
stats_desc.to_csv(stats_desc_path, sep=';', decimal=',')
print(f"  - Statistiques enregistrées dans {stats_desc_path}")

# b) Distribution des Prix (Histogrammes)
print("  - Génération des histogrammes de distribution des prix...")
for col in prix_cols_cles:
    if col in df_agg.columns and not df_agg[col].isna().all():
        plt.figure(figsize=(10, 6))
        sns.histplot(df_agg[col].dropna(), kde=True)
        plt.title(f'Distribution des prix pour {col.replace("_Prix", "")}')
        plt.xlabel('Prix')
        plt.ylabel('Nombre de magasins')
        plt.tight_layout()
        hist_path = os.path.join(output_directory, f'hist_distrib_{col}.png')
        plt.savefig(hist_path)
        plt.close()
    else:
         print(f"    * Pas de données valides pour l'histogramme de {col}")
print("  - Histogrammes enregistrés.")

# c) Comparaison par Catégorie de Ville
print("  - Génération des comparaisons par catégorie de ville...")
if 'Categorie Ville' in df_agg.columns:
    categories_ville = df_agg['Categorie Ville'].unique()
    print(f"    Catégories de ville trouvées: {categories_ville}")

    # Boxplots
    for col in prix_cols_cles:
         if col in df_agg.columns and not df_agg[col].isna().all():
            plt.figure(figsize=(12, 7))
            sns.boxplot(x='Categorie Ville', y=col, data=df_agg, order=sorted(categories_ville)) # Trier pour la cohérence
            plt.title(f'Comparaison des prix de {col.replace("_Prix", "")} par Catégorie de Ville')
            plt.xlabel('Catégorie de Ville')
            plt.ylabel('Prix')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            boxplot_path = os.path.join(output_directory, f'boxplot_catville_{col}.png')
            plt.savefig(boxplot_path)
            plt.close()
         else:
             print(f"    * Pas de données valides pour le boxplot de {col} par catégorie ville")

    # Barplots des moyennes
    try:
        df_mean_cat = df_agg.groupby('Categorie Ville')[prix_cols_cles].mean().reset_index()
        df_mean_cat_melt = df_mean_cat.melt(id_vars='Categorie Ville', var_name='Produit', value_name='Prix Moyen')
        df_mean_cat_melt['Produit'] = df_mean_cat_melt['Produit'].str.replace('_Prix', '')

        plt.figure(figsize=(15, 8))
        sns.barplot(x='Produit', y='Prix Moyen', hue='Categorie Ville', data=df_mean_cat_melt)
        plt.title('Prix Moyen des Produits Clés par Catégorie de Ville')
        plt.xlabel('Produit')
        plt.ylabel('Prix Moyen')
        plt.xticks(rotation=45, ha='right')
        plt.legend(title='Catégorie Ville')
        plt.tight_layout()
        barplot_path = os.path.join(output_directory, 'barplot_avg_catville.png')
        plt.savefig(barplot_path)
        plt.close()
        print("  - Graphiques par catégorie de ville enregistrés.")
    except Exception as e:
        print(f"  - Erreur lors de la création du barplot moyen par catégorie: {e}")

else:
    print("  - Colonne 'Categorie Ville' non trouvée, impossible de générer les comparaisons.")


# d) Cartes Choroplèthes par Département
print("  - Génération des cartes choroplèthes par département...")
for col in prix_cols_cles:
     if col in gdf_merged.columns and not gdf_merged[col].isna().all():
        fig, ax = plt.subplots(1, 1, figsize=(12, 12))
        gdf_merged.plot(column=col,
                        ax=ax,
                        legend=True,
                        legend_kwds={'label': f"Prix Moyen de {col.replace('_Prix', '')}",
                                     'orientation': "horizontal"},
                        missing_kwds={'color': 'lightgrey', "hatch": "///", "label": "Données manquantes"}, # Style pour les départements sans données
                        cmap='OrRd') # Choisir une palette de couleurs
        ax.set_title(f'Prix Moyen de {col.replace("_Prix", "")} par Département')
        ax.set_axis_off() # Masquer les axes x/y
        map_path = os.path.join(output_directory, f'map_departement_{col}.png')
        plt.savefig(map_path, bbox_inches='tight')
        plt.close()
     else:
         print(f"    * Pas de données valides pour la carte de {col}")
print("  - Cartes enregistrées.")

# e) Classement par Département (Barplots)
print("  - Génération des classements par département...")
for col in prix_cols_cles:
    if col in df_agg.columns and not df_agg[col].isna().all():
        # Calculer la moyenne par département
        mean_by_dept = df_agg.groupby('Departement')[col].mean().dropna()
        # Top 10 moins chers
        bottom_10 = mean_by_dept.nsmallest(10)
        # Top 10 plus chers
        top_10 = mean_by_dept.nlargest(10)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

        sns.barplot(x=bottom_10.index, y=bottom_10.values, ax=ax1, palette="viridis")
        ax1.set_title(f'Top 10 Départements les Moins Chers pour {col.replace("_Prix", "")}')
        ax1.set_ylabel('Prix Moyen')
        ax1.set_xlabel('Département')
        ax1.tick_params(axis='x', rotation=45)

        sns.barplot(x=top_10.index, y=top_10.values, ax=ax2, palette="viridis")
        ax2.set_title(f'Top 10 Départements les Plus Chers pour {col.replace("_Prix", "")}')
        ax2.set_ylabel('Prix Moyen')
        ax2.set_xlabel('Département')
        ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        barplot_dept_path = os.path.join(output_directory, f'barplot_classement_dept_{col}.png')
        plt.savefig(barplot_dept_path)
        plt.close()
    else:
        print(f"    * Pas de données valides pour le classement département de {col}")
print("  - Classements enregistrés.")


print("\nAnalyse terminée. Vérifiez le dossier:", output_directory)