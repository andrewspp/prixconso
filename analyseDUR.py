import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import warnings
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import matplotlib.patches as mpatches

# --- Configuration Seaborn & Warnings ---
sns.set_theme(style="whitegrid")
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

print("--- Initialisation: Analyse Prix Consommation avec Variables Socio-Économiques ---")

# --- 1. Configuration des Chemins ---
csv_path = '/Users/pierreandrews/Desktop/Prix conso/CSV DUR/dataDUR_final.csv'
output_dir = 'visuDUR_socioeco'

if not os.path.exists(csv_path): 
    raise FileNotFoundError(f"CSV non trouvé: {csv_path}")

print(f"CSV: {csv_path}\nOutput Dir: {output_dir}")
os.makedirs(output_dir, exist_ok=True)
print(f"Répertoire '{output_dir}' prêt.")

# --- 2. Chargement des Données ---
try:
    print("\n--- Chargement des données ---")
    df_prices = pd.read_csv(csv_path)
    print(f"CSV: {df_prices.shape[0]} lignes, {df_prices.shape[1]} colonnes.")
    
    # Vérifier si les colonnes demandées sont présentes
    socio_eco_vars = ['TUU2017', 'TDUU2017', 'MED21']
    missing_cols = [col for col in socio_eco_vars if col not in df_prices.columns]
    if missing_cols:
        print(f"Attention: Colonnes manquantes: {missing_cols}")
    
    # Afficher les informations sur les variables socio-économiques
    existing_socio_vars = [col for col in socio_eco_vars if col in df_prices.columns]
    for col in existing_socio_vars:
        print(f"\nVariable '{col}':")
        print(f"  - Valeurs uniques: {df_prices[col].nunique()}")
        print(f"  - Valeurs manquantes: {df_prices[col].isna().sum()}")
        if df_prices[col].nunique() < 10:  # Si peu de valeurs uniques, les afficher
            print(f"  - Distribution: {df_prices[col].value_counts().to_dict()}")
    
except Exception as e:
    print(f"Erreur chargement: {e}")
    exit()

# --- 3. Nettoyage et Préparation Initiale ---
print("\n--- Nettoyage et Préparation Initiale ---")
df = df_prices.copy()

# Identifier les colonnes produits (en excluant les colonnes de métadonnées)
metadata_cols = ['postal_code_used', 'zone_type', 'selected_store', 
                 'Code INSEE', 'UU2020', 'TUU2017', 'TDUU2017', 
                 'TYPE_UU2020', 'MED21', 'RD21']
product_cols = [col for col in df.columns if col not in metadata_cols]
print(f"{len(product_cols)} colonnes produits identifiées.")

def clean_price(price):
    if pd.isna(price) or price == '': 
        return np.nan
    try:
        price_str = str(price).replace('€', '').replace(',', '.').strip()
        return float(price_str) if price_str else np.nan
    except ValueError: 
        return np.nan

# Nettoyer les prix pour toutes les colonnes produits
for col in product_cols: 
    df[col] = df[col].apply(clean_price)
print("Nettoyage prix terminé.")

# Extraire le département à partir du code postal
df['postal_code_used'] = df['postal_code_used'].astype(str).str.zfill(5)
df['departement'] = df['postal_code_used'].str[:2]
print("Code département extrait.")

# Traiter les valeurs manquantes dans les variables socio-économiques
for col in existing_socio_vars:
    # Convertir en numérique si ce n'est pas déjà le cas
    if df[col].dtype == 'object':
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Imputer les valeurs manquantes avec la médiane
    if df[col].isna().sum() > 0:
        median_value = df[col].median()
        df[col].fillna(median_value, inplace=True)
        print(f"Variable '{col}': {df[col].isna().sum()} valeurs manquantes imputées avec la médiane ({median_value})")

# --- 4. Analyse de Volatilité AVANT Imputation ---
print("\n--- Analyse de Volatilité (Avant Imputation) ---")
means_observed = df[product_cols].mean(skipna=True)
stds_observed = df[product_cols].std(skipna=True)
cv_observed = (stds_observed / means_observed).replace([np.inf, -np.inf], np.nan).dropna()
cv_sorted_observed = cv_observed.sort_values(ascending=False)
print("Top 10 Produits les plus variables (CV):")
print(cv_sorted_observed.head(10))

# Sauvegarder le top N CV dans un fichier texte
cv_filepath = os.path.join(output_dir, 'top_produits_variables_cv.txt')
cv_sorted_observed.head(20).to_csv(cv_filepath, header=['Coefficient_Variation'])
print(f"Top 20 CV sauvegardés dans: {cv_filepath}")

# --- 5. Imputation Hiérarchique ---
print("\n--- Imputation Hiérarchique ---")
df_imputed = df.copy()
n_missing_before = df_imputed[product_cols].isna().sum().sum()
print(f"Valeurs manquantes avant: {n_missing_before}")

imputation_details = [] # Pour stocker les détails de l'imputation par produit

for col in product_cols:
    n_missing_prod_before = df_imputed[col].isna().sum()
    if n_missing_prod_before == 0:
        imputation_details.append({'produit': col, 'manquants_avant': 0, 'imputes_lvl1': 0, 
                                  'imputes_lvl2': 0, 'imputes_lvl3': 0, 'imputes_lvl4': 0, 
                                  'manquants_apres': 0})
        continue

    imputed_lvl1, imputed_lvl2, imputed_lvl3, imputed_lvl4 = 0, 0, 0, 0

    # Lvl 1: Imputation par département et type de zone
    mean_dept_zone = df_imputed.groupby(['departement', 'zone_type'])[col].transform('mean')
    df_imputed[col] = df_imputed[col].fillna(mean_dept_zone)
    n_missing_after_lvl1 = df_imputed[col].isna().sum()
    imputed_lvl1 = n_missing_prod_before - n_missing_after_lvl1

    # Lvl 2: Imputation par département
    if n_missing_after_lvl1 > 0:
        mean_dept = df_imputed.groupby('departement')[col].transform('mean')
        df_imputed[col] = df_imputed[col].fillna(mean_dept)
        n_missing_after_lvl2 = df_imputed[col].isna().sum()
        imputed_lvl2 = n_missing_after_lvl1 - n_missing_after_lvl2
    else: 
        n_missing_after_lvl2 = 0

    # Lvl 3: Imputation par type de zone
    if n_missing_after_lvl2 > 0:
        mean_zone = df_imputed.groupby('zone_type')[col].transform('mean')
        df_imputed[col] = df_imputed[col].fillna(mean_zone)
        n_missing_after_lvl3 = df_imputed[col].isna().sum()
        imputed_lvl3 = n_missing_after_lvl2 - n_missing_after_lvl3
    else: 
        n_missing_after_lvl3 = 0

    # Lvl 4: Imputation par moyenne globale
    if n_missing_after_lvl3 > 0:
        global_mean = df_imputed[col].mean() # Moyenne recalculée sur données partiellement imputées
        df_imputed[col] = df_imputed[col].fillna(global_mean)
        n_missing_prod_after = df_imputed[col].isna().sum()
        imputed_lvl4 = n_missing_after_lvl3 - n_missing_prod_after
    else: 
        n_missing_prod_after = 0

    imputation_details.append({
        'produit': col, 'manquants_avant': n_missing_prod_before,
        'imputes_lvl1': imputed_lvl1, 'imputes_lvl2': imputed_lvl2,
        'imputes_lvl3': imputed_lvl3, 'imputes_lvl4': imputed_lvl4,
        'manquants_apres': n_missing_prod_after
    })

n_missing_after = df_imputed[product_cols].isna().sum().sum()
print(f"Valeurs manquantes après: {n_missing_after}")

if n_missing_after > 0: 
    print(f"ATTENTION: {n_missing_after} valeurs n'ont pu être imputées.")

# Sauvegarder les détails de l'imputation
df_imputation_report = pd.DataFrame(imputation_details)
report_filepath = os.path.join(output_dir, 'rapport_imputation.csv')
df_imputation_report.to_csv(report_filepath, index=False)
print(f"Rapport d'imputation sauvegardé: {report_filepath}")

# --- 6. Calcul du Coût du Panier Complet Imputé ---
print("\n--- Calcul Coût Panier Complet (Après Imputation) ---")
df_imputed['cout_panier_impute'] = df_imputed[product_cols].sum(axis=1, skipna=True)

# Vérifier les éventuels NaN résiduels
imputed_na_count = df_imputed[product_cols].isna().sum(axis=1)
rows_with_remaining_na = imputed_na_count > 0
if rows_with_remaining_na.any():
    print(f"Attention: {rows_with_remaining_na.sum()} lignes ont encore des NaN résiduels.")
    # Mettre NaN pour ces paniers incomplets
    df_imputed.loc[rows_with_remaining_na, 'cout_panier_impute'] = np.nan

print("Coût panier calculé. Statistiques:")
print(df_imputed['cout_panier_impute'].describe())

# --- 7. Préparation pour l'Analyse par Variables Socio-Économiques ---
print("\n--- Préparation pour l'Analyse Socio-Économique ---")

# 7.1 Regrouper TUU2017 en catégories descriptives précises selon les définitions officielles
if 'TUU2017' in df_imputed.columns:
    # Créer une colonne pour la description du type d'unité urbaine selon les modalités officielles
    tuu_mapping = {
        1: "UU de 2 000 à 4 999 hab",
        2: "UU de 5 000 à 9 999 hab",
        3: "UU de 10 000 à 19 999 hab",
        4: "UU de 20 000 à 49 999 hab",
        5: "UU de 50 000 à 99 999 hab",
        6: "UU de 100 000 à 199 999 hab",
        7: "UU de 200 000 à 1 999 999 hab",
        8: "UU de Paris"
    }
    
    # Convertir en integer pour assurer le mapping correct (et éviter les NaN)
    df_imputed['TUU2017'] = df_imputed['TUU2017'].fillna(0).astype(int)
    
    # Créer la colonne descriptive
    df_imputed['TUU2017_desc'] = df_imputed['TUU2017'].map(tuu_mapping)
    print(f"Mapping TUU2017 créé. Distribution: {df_imputed['TUU2017_desc'].value_counts().to_dict()}")
    
# 7.2 Regrouper TDUU2017 en catégories descriptives précises selon les définitions officielles
if 'TDUU2017' in df_imputed.columns:
    # Créer une colonne pour la description du type détaillé d'unité urbaine selon les modalités officielles
    tduu_mapping = {
        11: "UU de moins de 2 500 hab",
        12: "UU de 2 500 à 2 999 hab",
        13: "UU de 3 000 à 3 999 hab",
        14: "UU de 4 000 à 4 999 hab",
        21: "UU de 5 000 à 6 999 hab",
        22: "UU de 7 000 à 9 999 hab",
        31: "UU de 10 000 à 14 999 hab",
        32: "UU de 15 000 à 19 999 hab",
        41: "UU de 20 000 à 24 999 hab",
        42: "UU de 25 000 à 29 999 hab",
        43: "UU de 30 000 à 39 999 hab",
        44: "UU de 40 000 à 49 999 hab",
        51: "UU de 50 000 à 69 999 hab",
        52: "UU de 70 000 à 99 999 hab",
        61: "UU de 100 000 à 149 999 hab",
        62: "UU de 150 000 à 199 999 hab",
        71: "UU de 200 000 à 299 999 hab",
        72: "UU de 300 000 à 499 999 hab",
        73: "UU de 500 000 à 1 999 999 hab",
        80: "UU de Paris"
    }
    
    # Convertir en integer pour assurer le mapping correct (et éviter les NaN)
    df_imputed['TDUU2017'] = df_imputed['TDUU2017'].fillna(0).astype(int)
    
    # Créer la colonne descriptive
    df_imputed['TDUU2017_desc'] = df_imputed['TDUU2017'].map(tduu_mapping)
    print(f"Mapping TDUU2017 créé. Distribution: {df_imputed['TDUU2017_desc'].value_counts().to_dict()}")

# 7.3 Créer des catégories de revenu médian pour les visualisations
if 'MED21' in df_imputed.columns:
    # Utiliser des quantiles pour diviser le revenu médian en catégories
    quantiles = [0, 0.25, 0.5, 0.75, 1.0]
    labels = ['Très bas', 'Bas', 'Moyen', 'Élevé']
    
    df_imputed['MED21_cat'] = pd.qcut(df_imputed['MED21'], 
                                      q=quantiles, 
                                      labels=labels)
    
    print(f"Catégories de revenu médian créées. Distribution: {df_imputed['MED21_cat'].value_counts().to_dict()}")
    
    # Créer aussi des seuils absolus (en euros) pour une interprétation plus directe
    med_bins = [0, 20000, 25000, 30000, float('inf')]
    med_labels = ['< 20k€', '20k€-25k€', '25k€-30k€', '> 30k€']
    
    df_imputed['MED21_range'] = pd.cut(df_imputed['MED21'], 
                                       bins=med_bins, 
                                       labels=med_labels)
    
    print(f"Intervalles de revenu médian créés. Distribution: {df_imputed['MED21_range'].value_counts().to_dict()}")

# --- 8. Visualisations Croisées avec TUU2017 (Type d'unité urbaine) ---
print("\n--- Visualisations Croisées avec TUU2017 ---")

if 'TUU2017' in df_imputed.columns:
    # 8.1 Boxplot du coût du panier par type d'unité urbaine
    tuu_boxplot_filename = 'boxplot_cout_panier_by_TUU2017.png'
    tuu_boxplot_filepath = os.path.join(output_dir, tuu_boxplot_filename)
    
    plt.figure(figsize=(12, 7))
    if 'TUU2017_desc' in df_imputed.columns:
        # Utiliser les descriptions pour l'axe x
        order = [tuu_mapping[i] for i in sorted(tuu_mapping.keys()) if tuu_mapping[i] in df_imputed['TUU2017_desc'].values]
        sns.boxplot(data=df_imputed.dropna(subset=['cout_panier_impute']), 
                   x='TUU2017_desc', y='cout_panier_impute', 
                   palette='viridis', order=order)
    else:
        # Sinon utiliser les valeurs numériques
        sns.boxplot(data=df_imputed.dropna(subset=['cout_panier_impute']), 
                   x='TUU2017', y='cout_panier_impute', 
                   palette='viridis')
        
    plt.title('Coût du Panier par Type d\'Unité Urbaine')
    plt.xlabel('Type d\'Unité Urbaine')
    plt.ylabel('Coût Total du Panier (€)')
    plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(tuu_boxplot_filepath)
    plt.close()
    print(f"Boxplot TUU2017 sauvegardé: {tuu_boxplot_filepath}")
    
    # 8.2 Violinplot du coût du panier par type d'unité urbaine
    tuu_violin_filename = 'violin_cout_panier_by_TUU2017.png'
    tuu_violin_filepath = os.path.join(output_dir, tuu_violin_filename)
    
    plt.figure(figsize=(12, 7))
    if 'TUU2017_desc' in df_imputed.columns:
        sns.violinplot(data=df_imputed.dropna(subset=['cout_panier_impute']), 
                      x='TUU2017_desc', y='cout_panier_impute', 
                      palette='viridis', order=order, inner='quartile')
    else:
        sns.violinplot(data=df_imputed.dropna(subset=['cout_panier_impute']), 
                      x='TUU2017', y='cout_panier_impute', 
                      palette='viridis', inner='quartile')
        
    plt.title('Distribution du Coût du Panier par Type d\'Unité Urbaine')
    plt.xlabel('Type d\'Unité Urbaine')
    plt.ylabel('Coût Total du Panier (€)')
    plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(tuu_violin_filepath)
    plt.close()
    print(f"Violinplot TUU2017 sauvegardé: {tuu_violin_filepath}")
    
    # 8.3 Barplot de la moyenne du coût du panier par type d'unité urbaine (avec erreur std)
    tuu_barplot_filename = 'barplot_cout_panier_mean_by_TUU2017.png'
    tuu_barplot_filepath = os.path.join(output_dir, tuu_barplot_filename)
    
    plt.figure(figsize=(12, 7))
    if 'TUU2017_desc' in df_imputed.columns:
        # Calculer d'abord les statistiques
        stats_df = df_imputed.dropna(subset=['cout_panier_impute']).groupby('TUU2017_desc')['cout_panier_impute'].agg(['mean', 'std', 'count']).reset_index()
        stats_df = stats_df.sort_values(by='TUU2017_desc', key=lambda x: [order.index(val) if val in order else float('inf') for val in x])
        
        # Barplot avec barres d'erreur
        ax = sns.barplot(x='TUU2017_desc', y='mean', data=stats_df, 
                        palette='viridis', order=order)
        
        # Configurer l'axe Y pour commencer à 120
        plt.ylim(bottom=120)
        
        # Ajouter les barres d'erreur
        for i, row in stats_df.iterrows():
            ax.errorbar(i, row['mean'], yerr=row['std'], color='black', capsize=5)
            
        # Ajouter le nombre d'observations
        for i, row in stats_df.iterrows():
            ax.text(i, row['mean'] + 5, f"n={row['count']}", 
                   ha='center', va='bottom', color='black', fontweight='bold')
    else:
        # Version simplifiée si nous n'avons pas les descriptions
        stats_df = df_imputed.dropna(subset=['cout_panier_impute']).groupby('TUU2017')['cout_panier_impute'].agg(['mean', 'std', 'count']).reset_index()
        stats_df = stats_df.sort_values(by='TUU2017')
        
        ax = sns.barplot(x='TUU2017', y='mean', data=stats_df, palette='viridis')
        
        # Configurer l'axe Y pour commencer à 120
        plt.ylim(bottom=120)
        
        for i, row in stats_df.iterrows():
            ax.errorbar(i, row['mean'], yerr=row['std'], color='black', capsize=5)
            ax.text(i, row['mean'] + 5, f"n={row['count']}", 
                   ha='center', va='bottom', color='black', fontweight='bold')
    
    plt.title('Coût Moyen du Panier (± écart-type) par Type d\'Unité Urbaine')
    plt.xlabel('Type d\'Unité Urbaine')
    plt.ylabel('Coût Moyen du Panier (€)')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(tuu_barplot_filepath)
    plt.close()
    print(f"Barplot TUU2017 sauvegardé: {tuu_barplot_filepath}")
    
    # 8.4 Test ANOVA pour TUU2017
    print("\nTest ANOVA (Coût Panier ~ TUU2017):")
    tuu_groups = [df_imputed['cout_panier_impute'][df_imputed['TUU2017'] == tuu].dropna() for tuu in df_imputed['TUU2017'].unique()]
    valid_groups = [g for g in tuu_groups if len(g) > 1]
    
    if len(valid_groups) >= 2:
        f_statistic, p_value = stats.f_oneway(*valid_groups)
        print(f"  F={f_statistic:.4f}, p={p_value:.4g}")
        alpha = 0.05
        if p_value < alpha:
            print(f"  Conclusion: Différence significative (p < {alpha}).")
        else:
            print(f"  Conclusion: Pas de différence significative (p >= {alpha}).")
    else:
        print("  ANOVA impossible (pas assez de groupes valides).")

# --- 9. Visualisations Croisées avec TDUU2017 (Type détaillé d'unité urbaine) ---
print("\n--- Visualisations Croisées avec TDUU2017 ---")

if 'TDUU2017' in df_imputed.columns:
    # 9.1 Scatter plot du coût du panier par TDUU2017
    tduu_scatter_filename = 'scatter_cout_panier_by_TDUU2017.png'
    tduu_scatter_filepath = os.path.join(output_dir, tduu_scatter_filename)
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_imputed.dropna(subset=['cout_panier_impute', 'TDUU2017']),
                   x='TDUU2017', y='cout_panier_impute',
                   alpha=0.7, palette='viridis')
    
    # Ajouter une ligne de tendance
    sns.regplot(data=df_imputed.dropna(subset=['cout_panier_impute', 'TDUU2017']),
               x='TDUU2017', y='cout_panier_impute',
               scatter=False, color='red')
    
    plt.title('Coût du Panier vs Type Détaillé d\'Unité Urbaine')
    plt.xlabel('Type Détaillé d\'Unité Urbaine (TDUU2017)')
    plt.ylabel('Coût Total du Panier (€)')
    plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
    plt.tight_layout()
    plt.savefig(tduu_scatter_filepath)
    plt.close()
    print(f"Scatter plot TDUU2017 sauvegardé: {tduu_scatter_filepath}")
    
    # 9.2 Calculer et afficher la corrélation
    corr_tduu = df_imputed[['TDUU2017', 'cout_panier_impute']].corr().iloc[0, 1]
    print(f"Corrélation entre TDUU2017 et coût du panier: {corr_tduu:.4f}")
    
    # 9.3 Boxplot avec les descriptifs (si disponibles)
    if 'TDUU2017_desc' in df_imputed.columns:
        tduu_boxplot_filename = 'boxplot_cout_panier_by_TDUU2017_desc.png'
        tduu_boxplot_filepath = os.path.join(output_dir, tduu_boxplot_filename)
        
        # Ordonner les catégories par valeur numérique de TDUU2017
        ordered_tduu = df_imputed.dropna(subset=['TDUU2017_desc']).sort_values('TDUU2017')['TDUU2017_desc'].unique()
        
        plt.figure(figsize=(14, 8))
        sns.boxplot(data=df_imputed.dropna(subset=['cout_panier_impute', 'TDUU2017_desc']),
                   x='TDUU2017_desc', y='cout_panier_impute',
                   palette='viridis', order=ordered_tduu)
        
        plt.title('Coût du Panier par Type Détaillé d\'Unité Urbaine')
        plt.xlabel('Type Détaillé d\'Unité Urbaine')
        plt.ylabel('Coût Total du Panier (€)')
        plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(tduu_boxplot_filepath)
        plt.close()
        print(f"Boxplot TDUU2017 descriptif sauvegardé: {tduu_boxplot_filepath}")
    
    # 9.4 Analyser par groupes (pour gérer de nombreuses valeurs uniques)
    # Créer des groupes logiques plutôt que des quantiles arbitraires
    tduu_group_map = {
        # Petites UU
        11: "UU < 5 000 hab",
        12: "UU < 5 000 hab", 
        13: "UU < 5 000 hab",
        14: "UU < 5 000 hab",
        # UU moyennes petites
        21: "UU 5 000-19 999 hab",
        22: "UU 5 000-19 999 hab",
        31: "UU 5 000-19 999 hab",
        32: "UU 5 000-19 999 hab",
        # UU moyennes
        41: "UU 20 000-99 999 hab",
        42: "UU 20 000-99 999 hab",
        43: "UU 20 000-99 999 hab",
        44: "UU 20 000-99 999 hab",
        51: "UU 20 000-99 999 hab",
        52: "UU 20 000-99 999 hab",
        # Grandes UU
        61: "UU 100 000-499 999 hab",
        62: "UU 100 000-499 999 hab",
        71: "UU 100 000-499 999 hab",
        72: "UU 100 000-499 999 hab",
        # Très grandes UU et Paris
        73: "UU ≥ 500 000 hab",
        80: "UU de Paris"
    }
    
    # Appliquer le regroupement
    df_imputed['TDUU2017_groupe'] = df_imputed['TDUU2017'].map(tduu_group_map)
    
    tduu_group_boxplot_filename = 'boxplot_cout_panier_by_TDUU2017_groupe.png'
    tduu_group_boxplot_filepath = os.path.join(output_dir, tduu_group_boxplot_filename)
    
    # Ordre logique pour les groupes
    groupe_order = [
        "UU < 5 000 hab",
        "UU 5 000-19 999 hab",
        "UU 20 000-99 999 hab",
        "UU 100 000-499 999 hab",
        "UU ≥ 500 000 hab",
        "UU de Paris"
    ]
    
    plt.figure(figsize=(12, 7))
    sns.boxplot(data=df_imputed.dropna(subset=['cout_panier_impute', 'TDUU2017_groupe']),
               x='TDUU2017_groupe', y='cout_panier_impute',
               palette='viridis', order=groupe_order)
    
    plt.title('Coût du Panier par Groupe de Type Détaillé d\'Unité Urbaine')
    plt.xlabel('Groupe de Type Détaillé d\'Unité Urbaine')
    plt.ylabel('Coût Total du Panier (€)')
    plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(tduu_group_boxplot_filepath)
    plt.close()
    print(f"Boxplot TDUU2017 par groupe sauvegardé: {tduu_group_boxplot_filepath}")
    
    # 9.5 Test ANOVA pour les groupes TDUU2017
    print("\nTest ANOVA (Coût Panier ~ Groupe TDUU2017):")
    tduu_groups = [df_imputed['cout_panier_impute'][df_imputed['TDUU2017_groupe'] == group].dropna() 
                  for group in groupe_order if group in df_imputed['TDUU2017_groupe'].unique()]
    valid_groups = [g for g in tduu_groups if len(g) > 1]
    
    if len(valid_groups) >= 2:
        f_statistic, p_value = stats.f_oneway(*valid_groups)
        print(f"  F={f_statistic:.4f}, p={p_value:.4g}")
        alpha = 0.05
        if p_value < alpha:
            print(f"  Conclusion: Différence significative (p < {alpha}).")
        else:
            print(f"  Conclusion: Pas de différence significative (p >= {alpha}).")
    else:
        print("  ANOVA impossible (pas assez de groupes valides).")

# --- 10. Visualisations Croisées avec MED21 (Revenu médian) ---
print("\n--- Visualisations Croisées avec MED21 ---")

if 'MED21' in df_imputed.columns:
    # 10.1 Scatter plot du coût du panier par revenu médian
    med_scatter_filename = 'scatter_cout_panier_by_MED21.png'
    med_scatter_filepath = os.path.join(output_dir, med_scatter_filename)
    
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df_imputed.dropna(subset=['cout_panier_impute', 'MED21']),
                   x='MED21', y='cout_panier_impute',
                   alpha=0.7, hue='zone_type' if 'zone_type' in df_imputed.columns else None)
    
    # Ajouter une ligne de tendance
    sns.regplot(data=df_imputed.dropna(subset=['cout_panier_impute', 'MED21']),
               x='MED21', y='cout_panier_impute',
               scatter=False, color='red')
    
    plt.title('Coût du Panier vs Revenu Médian')
    plt.xlabel('Revenu Médian (€)')
    plt.ylabel('Coût Total du Panier (€)')
    plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
    plt.tight_layout()
    plt.savefig(med_scatter_filepath)
    plt.close()
    print(f"Scatter plot MED21 sauvegardé: {med_scatter_filepath}")
    
    # 10.2 Boxplot du coût du panier par catégorie de revenu médian
    if 'MED21_cat' in df_imputed.columns:
        med_boxplot_filename = 'boxplot_cout_panier_by_MED21_cat.png'
        med_boxplot_filepath = os.path.join(output_dir, med_boxplot_filename)
        
        plt.figure(figsize=(12, 7))
        sns.boxplot(data=df_imputed.dropna(subset=['cout_panier_impute']),
                   x='MED21_cat', y='cout_panier_impute',
                   palette='viridis', order=labels)
        
        plt.title('Coût du Panier par Catégorie de Revenu Médian')
        plt.xlabel('Catégorie de Revenu Médian')
        plt.ylabel('Coût Total du Panier (€)')
        plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
        plt.tight_layout()
        plt.savefig(med_boxplot_filepath)
        plt.close()
        print(f"Boxplot MED21_cat sauvegardé: {med_boxplot_filepath}")
    
    # 10.3 Boxplot du coût par intervalle de revenu (en euros)
    if 'MED21_range' in df_imputed.columns:
        med_range_boxplot_filename = 'boxplot_cout_panier_by_MED21_range.png'
        med_range_boxplot_filepath = os.path.join(output_dir, med_range_boxplot_filename)
        
        plt.figure(figsize=(12, 7))
        sns.boxplot(data=df_imputed.dropna(subset=['cout_panier_impute']),
                   x='MED21_range', y='cout_panier_impute',
                   palette='viridis', order=med_labels)
        
        plt.title('Coût du Panier par Intervalle de Revenu Médian')
        plt.xlabel('Intervalle de Revenu Médian')
        plt.ylabel('Coût Total du Panier (€)')
        plt.ylim(bottom=170)  # Commencer à 170 pour le coût total
        plt.tight_layout()
        plt.savefig(med_range_boxplot_filepath)
        plt.close()
        print(f"Boxplot MED21_range sauvegardé: {med_range_boxplot_filepath}")
    
    # 10.4 Calculer et afficher la corrélation
    corr_med = df_imputed[['MED21', 'cout_panier_impute']].corr().iloc[0, 1]
    print(f"Corrélation entre MED21 et coût du panier: {corr_med:.4f}")

# --- 11. Analyse Multivariée: Combiner TUU2017, TDUU2017 et MED21 ---
print("\n--- Analyse Multivariée ---")

# 11.1 Matrice de corrélation entre variables socio-économiques et coût du panier
socio_eco_cols = [col for col in ['TUU2017', 'TDUU2017', 'MED21', 'cout_panier_impute'] 
                 if col in df_imputed.columns]

if len(socio_eco_cols) > 1:
    corr_matrix = df_imputed[socio_eco_cols].corr()
    
    corr_matrix_filename = 'correlation_matrix_socioeco_cout.png'
    corr_matrix_filepath = os.path.join(output_dir, corr_matrix_filename)
    
    plt.figure(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, annot=True, fmt='.4f', cmap='coolwarm', 
               mask=mask, vmin=-1, vmax=1, center=0,
               square=True, linewidths=.5)
    
    plt.title('Matrice de Corrélation: Variables Socio-Économiques et Coût du Panier')
    plt.tight_layout()
    plt.savefig(corr_matrix_filepath)
    plt.close()
    print(f"Matrice de corrélation sauvegardée: {corr_matrix_filepath}")
    
    # 11.2 HeatMap croisée (si nous avons suffisamment de catégories)
    if 'TUU2017_desc' in df_imputed.columns and 'MED21_cat' in df_imputed.columns:
        heatmap_filename = 'heatmap_cout_panier_TUU2017_MED21.png'
        heatmap_filepath = os.path.join(output_dir, heatmap_filename)
        
        # Ordonner les types d'unité urbaine selon leur code numérique croissant
        tuu_order = df_imputed.sort_values('TUU2017')['TUU2017_desc'].unique()
        
        # Calculer le coût moyen du panier par croisement TUU2017 x MED21
        heatmap_data = df_imputed.pivot_table(values='cout_panier_impute', 
                                            index='TUU2017_desc', 
                                            columns='MED21_cat', 
                                            aggfunc='mean')
        
        # Réordonner les lignes selon l'ordre logique des TUU
        if all(idx in heatmap_data.index for idx in tuu_order):
            heatmap_data = heatmap_data.reindex(tuu_order)
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='viridis',
                   linewidths=.5, cbar_kws={'label': 'Coût Moyen du Panier (€)'})
        
        plt.title('Coût Moyen du Panier par Type d\'Unité Urbaine et Catégorie de Revenu')
        plt.tight_layout()
        plt.savefig(heatmap_filepath)
        plt.close()
        print(f"Heatmap croisée TUU2017 x MED21 sauvegardée: {heatmap_filepath}")
    
    # 11.2.2 HeatMap croisée pour TDUU2017 groupé
    if 'TDUU2017_groupe' in df_imputed.columns and 'MED21_cat' in df_imputed.columns:
        tduu_heatmap_filename = 'heatmap_cout_panier_TDUU2017_groupe_MED21.png'
        tduu_heatmap_filepath = os.path.join(output_dir, tduu_heatmap_filename)
        
        # Ordre logique pour les groupes TDUU
        groupe_order = [
            "UU < 5 000 hab",
            "UU 5 000-19 999 hab",
            "UU 20 000-99 999 hab",
            "UU 100 000-499 999 hab",
            "UU ≥ 500 000 hab",
            "UU de Paris"
        ]
        
        # Calculer le coût moyen du panier par croisement TDUU2017_groupe x MED21
        tduu_heatmap_data = df_imputed.pivot_table(values='cout_panier_impute', 
                                                 index='TDUU2017_groupe', 
                                                 columns='MED21_cat', 
                                                 aggfunc='mean')
        
        # Réordonner les lignes selon l'ordre logique des groupes TDUU
        available_groups = [g for g in groupe_order if g in tduu_heatmap_data.index]
        if available_groups:
            tduu_heatmap_data = tduu_heatmap_data.reindex(available_groups)
        
        plt.figure(figsize=(12, 8))
        sns.heatmap(tduu_heatmap_data, annot=True, fmt='.1f', cmap='viridis',
                   linewidths=.5, cbar_kws={'label': 'Coût Moyen du Panier (€)'})
        
        plt.title('Coût Moyen du Panier par Groupe d\'UU et Catégorie de Revenu')
        plt.tight_layout()
        plt.savefig(tduu_heatmap_filepath)
        plt.close()
        print(f"Heatmap croisée TDUU2017_groupe x MED21 sauvegardée: {tduu_heatmap_filepath}")

# 11.3 Modèle de régression multiple
print("\n--- Régression Multiple ---")
X_cols = [col for col in ['TUU2017', 'TDUU2017', 'MED21'] if col in df_imputed.columns]

if len(X_cols) >= 1:
    # Préparer les données
    model_data = df_imputed.dropna(subset=X_cols + ['cout_panier_impute'])
    
    X = model_data[X_cols]
    y = model_data['cout_panier_impute']
    
    # Standardiser les variables indépendantes
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Ajuster le modèle
    model = LinearRegression()
    model.fit(X_scaled, y)
    
    # Évaluer le modèle
    r_squared = model.score(X_scaled, y)
    
    # Afficher les résultats
    print(f"R² du modèle: {r_squared:.4f}")
    print("Coefficients de régression:")
    for i, col in enumerate(X_cols):
        print(f"  {col}: {model.coef_[i]:.4f}")
    print(f"  Intercept: {model.intercept_:.4f}")
    
    # Sauvegarder les résultats dans un fichier texte
    regression_results_filename = 'resultats_regression_multiple.txt'
    regression_results_filepath = os.path.join(output_dir, regression_results_filename)
    
    with open(regression_results_filepath, 'w') as f:
        f.write("RÉSULTATS DE LA RÉGRESSION MULTIPLE\n")
        f.write("==================================\n\n")
        f.write(f"Variable dépendante: cout_panier_impute\n")
        f.write(f"Variables indépendantes: {', '.join(X_cols)}\n\n")
        f.write(f"R² du modèle: {r_squared:.4f}\n\n")
        f.write("Coefficients standardisés:\n")
        for i, col in enumerate(X_cols):
            f.write(f"  {col}: {model.coef_[i]:.4f}\n")
        f.write(f"  Intercept: {model.intercept_:.4f}\n\n")
        f.write("Interprétation:\n")
        f.write("  - Un R² plus proche de 1 indique un meilleur ajustement.\n")
        f.write("  - Les coefficients indiquent l'effet marginal de chaque variable.\n")
        if r_squared < 0.3:
            f.write("  - Le R² est faible, suggérant que les variables socio-économiques\n")
            f.write("    expliquent peu la variation du coût du panier.\n")
        elif r_squared < 0.7:
            f.write("  - Le R² est modéré, suggérant que les variables socio-économiques\n")
            f.write("    expliquent partiellement la variation du coût du panier.\n")
        else:
            f.write("  - Le R² est élevé, suggérant que les variables socio-économiques\n")
            f.write("    expliquent bien la variation du coût du panier.\n")
    
    print(f"Résultats de régression sauvegardés: {regression_results_filepath}")

# --- 12. Synthèse et Conclusions ---
print("\n--- Synthèse et Conclusions ---")

# 12.1 Identifier les principaux résultats
conclusion_filename = 'synthese_et_conclusions.txt'
conclusion_filepath = os.path.join(output_dir, conclusion_filename)

with open(conclusion_filepath, 'w') as f:
    f.write("SYNTHÈSE ET CONCLUSIONS DE L'ANALYSE\n")
    f.write("==================================\n\n")
    
    f.write("1. CARACTÉRISTIQUES DU PANIER\n")
    f.write(f"   - Coût moyen du panier: {df_imputed['cout_panier_impute'].mean():.2f}€\n")
    f.write(f"   - Écart-type: {df_imputed['cout_panier_impute'].std():.2f}€\n")
    f.write(f"   - Médiane: {df_imputed['cout_panier_impute'].median():.2f}€\n")
    f.write(f"   - Minimum: {df_imputed['cout_panier_impute'].min():.2f}€\n")
    f.write(f"   - Maximum: {df_imputed['cout_panier_impute'].max():.2f}€\n\n")
    
    f.write("2. RELATION AVEC LA TYPOLOGIE URBAINE (TUU2017)\n")
    if 'TUU2017' in df_imputed.columns:
        # Tendance
        if 'TUU2017' in df_imputed.columns and 'cout_panier_impute' in df_imputed.columns:
            corr_tuu = df_imputed[['TUU2017', 'cout_panier_impute']].corr().iloc[0, 1]
            f.write(f"   - Corrélation avec TUU2017: {corr_tuu:.4f}\n")
            f.write("   - Rappel des modalités de TUU2017:\n")
            f.write("     1: UU de 2 000 à 4 999 hab\n")
            f.write("     2: UU de 5 000 à 9 999 hab\n")
            f.write("     3: UU de 10 000 à 19 999 hab\n")
            f.write("     4: UU de 20 000 à 49 999 hab\n")
            f.write("     5: UU de 50 000 à 99 999 hab\n")
            f.write("     6: UU de 100 000 à 199 999 hab\n")
            f.write("     7: UU de 200 000 à 1 999 999 hab\n")
            f.write("     8: UU de Paris\n\n")
            
            if abs(corr_tuu) < 0.1:
                f.write("   - Corrélation très faible: peu ou pas de relation linéaire entre\n")
                f.write("     la taille de l'unité urbaine et le coût du panier.\n")
            elif abs(corr_tuu) < 0.3:
                if corr_tuu > 0:
                    f.write("   - Corrélation positive faible: légère tendance à des paniers\n")
                    f.write("     plus chers dans les unités urbaines plus grandes.\n")
                else:
                    f.write("   - Corrélation négative faible: légère tendance à des paniers\n")
                    f.write("     moins chers dans les unités urbaines plus grandes.\n")
            elif abs(corr_tuu) < 0.5:
                if corr_tuu > 0:
                    f.write("   - Corrélation positive modérée: tendance à des paniers\n")
                    f.write("     plus chers dans les unités urbaines plus grandes.\n")
                else:
                    f.write("   - Corrélation négative modérée: tendance à des paniers\n")
                    f.write("     moins chers dans les unités urbaines plus grandes.\n")
            else:
                if corr_tuu > 0:
                    f.write("   - Corrélation positive forte: les paniers sont clairement\n")
                    f.write("     plus chers dans les unités urbaines plus grandes.\n")
                else:
                    f.write("   - Corrélation négative forte: les paniers sont clairement\n")
                    f.write("     moins chers dans les unités urbaines plus grandes.\n")
        else:
            f.write("   - Analyse de corrélation impossible (données manquantes).\n")
    else:
        f.write("   - Analyse impossible (TUU2017 non disponible).\n\n")
        
    # Ajouter une section pour TDUU2017
    f.write("3. RELATION AVEC LA TYPOLOGIE URBAINE DÉTAILLÉE (TDUU2017)\n")
    if 'TDUU2017' in df_imputed.columns:
        # Tendance
        if 'TDUU2017' in df_imputed.columns and 'cout_panier_impute' in df_imputed.columns:
            corr_tduu = df_imputed[['TDUU2017', 'cout_panier_impute']].corr().iloc[0, 1]
            f.write(f"   - Corrélation avec TDUU2017: {corr_tduu:.4f}\n")
            f.write("   - Rappel: TDUU2017 est une classification plus fine que TUU2017,\n")
            f.write("     allant de 11 (UU < 2 500 hab) à 80 (UU de Paris).\n\n")
            
            if 'TDUU2017_groupe' in df_imputed.columns:
                # Calculer les moyennes par groupe pour présenter dans les conclusions
                group_means = df_imputed.groupby('TDUU2017_groupe')['cout_panier_impute'].mean().sort_index()
                
                f.write("   - Coût moyen du panier par groupe d'unité urbaine:\n")
                for group, mean_cost in group_means.items():
                    f.write(f"     {group}: {mean_cost:.2f}€\n")
                f.write("\n")
            
            if abs(corr_tduu) < 0.1:
                f.write("   - Interprétation similaire à TUU2017, mais avec une typologie plus détaillée.\n")
                f.write("   - La corrélation très faible suggère que la taille précise de l'unité urbaine\n")
                f.write("     n'est pas un bon prédicteur du coût du panier de consommation.\n")
            elif corr_tduu > 0:
                f.write("   - La corrélation positive avec TDUU2017 confirme la tendance observée avec TUU2017:\n")
                f.write("     le coût du panier tend à augmenter avec la taille de l'unité urbaine.\n")
            else:
                f.write("   - La corrélation négative avec TDUU2017 confirme la tendance observée avec TUU2017:\n")
                f.write("     le coût du panier tend à diminuer avec la taille de l'unité urbaine.\n")
        else:
            f.write("   - Analyse de corrélation impossible (données manquantes).\n")
    else:
        f.write("   - Analyse impossible (TDUU2017 non disponible).\n\n")
    
    f.write("4. RELATION AVEC LE REVENU MÉDIAN (MED21)\n")
    if 'MED21' in df_imputed.columns:
        if 'MED21' in df_imputed.columns and 'cout_panier_impute' in df_imputed.columns:
            corr_med = df_imputed[['MED21', 'cout_panier_impute']].corr().iloc[0, 1]
            f.write(f"   - Corrélation avec MED21: {corr_med:.4f}\n")
            if abs(corr_med) < 0.1:
                f.write("   - Corrélation très faible: peu ou pas de relation linéaire entre\n")
                f.write("     le revenu médian et le coût du panier.\n")
            elif abs(corr_med) < 0.3:
                if corr_med > 0:
                    f.write("   - Corrélation positive faible: légère tendance à des paniers\n")
                    f.write("     plus chers dans les zones à revenu médian plus élevé.\n")
                else:
                    f.write("   - Corrélation négative faible: légère tendance à des paniers\n")
                    f.write("     moins chers dans les zones à revenu médian plus élevé.\n")
            elif abs(corr_med) < 0.5:
                if corr_med > 0:
                    f.write("   - Corrélation positive modérée: tendance à des paniers\n")
                    f.write("     plus chers dans les zones à revenu médian plus élevé.\n")
                else:
                    f.write("   - Corrélation négative modérée: tendance à des paniers\n")
                    f.write("     moins chers dans les zones à revenu médian plus élevé.\n")
            else:
                if corr_med > 0:
                    f.write("   - Corrélation positive forte: les paniers sont clairement\n")
                    f.write("     plus chers dans les zones à revenu médian plus élevé.\n")
                else:
                    f.write("   - Corrélation négative forte: les paniers sont clairement\n")
                    f.write("     moins chers dans les zones à revenu médian plus élevé.\n")
        else:
            f.write("   - Analyse de corrélation impossible (données manquantes).\n")
    else:
        f.write("   - Analyse impossible (MED21 non disponible).\n\n")
    
    # Si un modèle de régression a été exécuté
    if 'model' in locals() and len(X_cols) >= 1:
        f.write("5. MODÈLE DE RÉGRESSION MULTIPLE\n")
        f.write(f"   - R² du modèle: {r_squared:.4f}\n")
        f.write(f"   - Variables incluses: {', '.join(X_cols)}\n")
        if r_squared < 0.3:
            f.write("   - Conclusion: Les variables socio-économiques expliquent peu\n")
            f.write("     la variation du coût du panier (R² faible).\n")
        elif r_squared < 0.7:
            f.write("   - Conclusion: Les variables socio-économiques expliquent\n")
            f.write("     partiellement la variation du coût du panier (R² modéré).\n")
        else:
            f.write("   - Conclusion: Les variables socio-économiques expliquent bien\n")
            f.write("     la variation du coût du panier (R² élevé).\n\n")
    
    f.write("6. CONCLUSIONS GÉNÉRALES\n")
    f.write("   - L'imputation hiérarchique a permis de combler les valeurs manquantes\n")
    f.write("     tout en respectant les structures spatiales des prix.\n")
    f.write("   - Les analyses graphiques révèlent les relations entre structure\n")
    f.write("     urbaine, revenu médian et coût du panier de consommation.\n")
    f.write("   - Ces résultats permettent de mieux comprendre les disparités\n")
    f.write("     territoriales du pouvoir d'achat alimentaire.\n\n")
    
    f.write("7. LIMITES ET PERSPECTIVES\n")
    f.write("   - L'imputation reste une estimation et ne remplace pas des données réelles.\n")
    f.write("   - Le panier analysé n'est pas pondéré par la fréquence de consommation.\n")
    f.write("   - Une analyse temporelle permettrait de suivre l'évolution des prix.\n")
    f.write("   - L'intégration d'autres variables socio-économiques enrichirait l'analyse.\n")

print(f"Synthèse et conclusions sauvegardées: {conclusion_filepath}")

# 12.2 Générer un graphique de synthèse final
synthesis_plot_filename = 'synthese_cout_panier_variables_socioeco.png'
synthesis_plot_filepath = os.path.join(output_dir, synthesis_plot_filename)

vars_for_synthesis = []
if 'TUU2017' in df_imputed.columns:
    vars_for_synthesis.append(('TUU2017', 'Type d\'Unité Urbaine'))
if 'TDUU2017' in df_imputed.columns:
    vars_for_synthesis.append(('TDUU2017', 'Type Détaillé d\'Unité Urbaine'))
if 'MED21' in df_imputed.columns:
    vars_for_synthesis.append(('MED21', 'Revenu Médian (€)'))

if len(vars_for_synthesis) >= 1:
    fig, axes = plt.subplots(len(vars_for_synthesis), 1, figsize=(12, 5*len(vars_for_synthesis)))
    if len(vars_for_synthesis) == 1:
        axes = [axes]  # Assurer que axes est une liste même avec un seul graphique
    
    for i, (var_name, var_label) in enumerate(vars_for_synthesis):
        if var_name in ['TUU2017', 'TDUU2017']:  # Variables discrètes/catégorielles
            # Pour ces variables, un nuage de points avec jitter et boxplot superposé
            sns.boxplot(data=df_imputed.dropna(subset=[var_name, 'cout_panier_impute']),
                        x=var_name, y='cout_panier_impute',
                        ax=axes[i], color='lightgray', width=0.5)
            
            sns.stripplot(data=df_imputed.dropna(subset=[var_name, 'cout_panier_impute']),
                         x=var_name, y='cout_panier_impute',
                         ax=axes[i], size=4, color='blue', alpha=0.3, jitter=True)
            
            # Ajouter ligne de régression
            x_vals = df_imputed[var_name].dropna().unique()
            y_means = [df_imputed[df_imputed[var_name]==x]['cout_panier_impute'].mean() for x in x_vals]
            axes[i].plot(range(len(x_vals)), y_means, 'r-', linewidth=2)
            
            # Configurer l'axe Y pour commencer à 170 pour le coût total
            axes[i].set_ylim(bottom=170)
            
        else:  # Variables continues (comme MED21)
            # Pour les variables continues, un scatter plot avec ligne de régression
            sns.regplot(data=df_imputed.dropna(subset=[var_name, 'cout_panier_impute']),
                      x=var_name, y='cout_panier_impute',
                      ax=axes[i], scatter_kws={'alpha': 0.3, 's': 15},
                      line_kws={'color': 'red'})
            
            # Configurer l'axe Y pour commencer à 170 pour le coût total
            axes[i].set_ylim(bottom=170)
        
        # Calculer et afficher la corrélation sur le graphique
        corr = df_imputed[[var_name, 'cout_panier_impute']].corr().iloc[0, 1]
        axes[i].text(0.05, 0.95, f"Corrélation: {corr:.4f}", 
                    transform=axes[i].transAxes, fontsize=12,
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        axes[i].set_title(f"Coût du Panier vs {var_label}")
        axes[i].set_xlabel(var_label)
        axes[i].set_ylabel("Coût du Panier (€)")
    
    plt.tight_layout()
    plt.savefig(synthesis_plot_filepath)
    plt.close()
    print(f"Graphique de synthèse sauvegardé: {synthesis_plot_filepath}")

print("\n--- Script d'Analyse des Prix de Consommation Terminé ---")
print(f"Tous les résultats ont été sauvegardés dans le répertoire: {output_dir}")