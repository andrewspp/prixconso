import pandas as pd
import numpy as np
import re
import os

# --- Configuration du Nettoyage (Améliorée) ---
# (keyword_rules reste le même que dans la version précédente)
keyword_rules = {
    "Lait demi-écrémé": (["lait"], ["yaourt", "fromage", "beurre", "crème", "dessert", "boisson"]),
    "Oeufs de poules élevées": (["oeuf", "œuf", "oeufs", "œufs"], ["mayonnaise", "brioche", "gâteau", "madeleine"]),
    "Yaourts nature": (["yaourt", "yaourts"], ["lait", "fromage", "beurre", "crème", "dessert", "boire"]),
    "Camembert": (["camembert"], ["feuilleté", "tarte", "quiche"]),
    "Beurre doux": (["beurre"], ["sel", "salé", "demi-sel", "margarine", "huile"]), # Exclut explicitement beurre salé/demi-sel
    "Pain complet aux céréales": (["pain", "baguette"], ["biscotte", "grillé", "mie (sauf si complet)", "viennois", "burger", "hot-dog"]), # Plus spécifique
    "Baguettes traditionnelles": (["baguette"], ["pain", "viennoise"]),
    "Special K": (["special k", "spécial k"], []), # Marque spécifique, reste tel quel
    "Farine de blé": (["farine"], ["sarrasin", "châtaigne", "maïs", "riz", "épeautre", "seigle", "pois chiche"]), # Cible blé
    "Sucre de canne poudre": (["sucre", "cassonade"], ["cube", "morceaux", "liquide", "sirop", "vanillé", "glace"]),
    "Capsule café Nespresso": (["capsule", "dosette", "café", "nespresso"], ["thé", "chocolat", "machine", "compatible dolce gusto"]),
    "Thé noir Twinings": (["thé", "twinings"], ["infusion", "tisane", "rooibos", "café"]),
    "Confiture": (["confiture"], ["compote", "gelée (sauf si confiture)", "marmelade (sauf si confiture)", "purée"]),
    "Miel naturel": (["miel"], ["serviette", "papier", "gel douche", "savon", "bonbon", "nougat", "pain d'épices"]),
    "Jus d'orange": (["jus", "orange"], ["boisson à", "nectar", "limonade", "soda", "sirop", "thé", "concentré"]),
    "Eau gazeuse Badoit": (["eau", "badoit", "gazeuse", "pétillante"], ["plate", "sirop", "jus"]),
    "Riz basmati": (["riz"], ["risotto", "galette", "pâtes", "semoule", "soufflé", "boisson"]),
    "Spaghetti": (["spaghetti", "linguine"], ["pâtes farcies", "tagliatelle", "penne", "coquillette", "riz", "gnocchi"]),
    "Pommes de terre": (["pomme de terre", "pommes de terre"], ["tortilla", "chips", "frites (sauf si produit brut)", "purée (sauf si produit brut)", "gratin", "soupe"]),
    "Lentilles vertes": (["lentille", "lentilles"], ["soupe", "plat cuisiné", "salade composée"]),
    "Conserves de tomates pelées": (["tomate", "tomates"], ["cerise", "séchée", "concentré", "farcie", "ketchup", "soupe"]), # Vise tomates en conserve non transformées
    "Pommes Golden": (["pomme", "pommes"], ["compote", "gourde", "sac", "spécialité", "jus", "purée", "cidre", "pétillant", "tarte", "beignet"]), # Vise pommes fraîches
    "Bananes": (["banane", "bananes"], ["compote", "gourde", "spécialité", "chips", "nectar", "bonbon", "yaourt", "dessert"]), # Vise bananes fraîches
    "Oranges à jus": (["orange", "oranges"], ["boisson", "confiture", "compote", "gourde", "marmelade", "salade de fruits", "chocolat"]), # Vise oranges fraîches
    "Citrons": (["citron", "citrons"], ["jus", "boisson", "orangeade", "thé", "sirop", "vinaigrette", "tarte", "sorbet", "bonbon", "yaourt"]), # Vise citrons frais
    "Raisins sans pépins": (["raisin", "raisins"], ["jus", "compote", "secs", "gâteau", "alcool", "vinaigre"]), # Vise raisins frais
    "Tomates": (["tomate", "tomates"], ["pelée", "pelées", "conserve", "sauce", "séchée", "concentré", "farcie", "ketchup", "jus", "soupe"]), # Vise tomates fraîches (cerises, rondes...)
    "Carottes": (["carotte", "carottes"], ["jus", "boisson", "mélange", "petits pois", "râpée", "purée", "soupe", "gâteau", "salade composée"]), # Vise carottes fraîches
    "Oignons jaunes": (["oignon", "oignons"], ["mélange", "pot au feu", "tortilla", "soupe", "confit", "frit", "rings", "congelé", "poudre", "semoule"]), # Vise oignons frais
    "Salade verte": (["salade", "laitue", "mâche", "feuille de chêne", "iceberg", "batavia", "roquette", "frisée"], ["vinaigrette", "sauce", "mélange pour", "composée", "piémontaise", "endive"]), # Vise salades vertes en feuilles/coeur
    "Concombres": (["concombre", "concombres"], ["tzatziki", "fromage blanc", "salade de", "pickles", "soupe"]), # Vise concombres frais
    "Poivrons": (["poivron", "poivrons"], ["farci", "grillé", "mélange", "conserve", "sauce", "tapenade"]), # Vise poivrons frais
    "Courgettes": (["courgette", "courgettes"], ["poêlée", "cuisinée", "gratin", "farci", "soupe", "purée", "ratatouille", "conserve"]), # Vise courgettes fraîches
    "Aubergine": (["aubergine", "aubergines"], ["cuisinée", "moussaka", "riste", "farci", "gratin", "caviar", "ratatouille", "conserve"]), # Vise aubergines fraîches
    "Filet Blanc de poulet": (["poulet", "volaille", "filet", "blanc de", "escalope"], ["pané", "cordon bleu", "nugget", "bouillon", "rôti", "cuisse", "brochette", "saucisse", "jambon"]),
    "Steak haché": (["steak", "haché", "bœuf"], ["végétal", "soja", "burger (sauf si steak)", "cheval", "poulet", "dinde"]),
    "Knackis": (["knacki", "knacks", "saucisse de strasbourg"], ["poulet", "volaille"]), # Cibler porc/standard
    "Filets de poisson blanc": (["poisson", "merlu", "lieu", "colin", "cabillaud", "filet", "dos"], ["pané", "surimi", "brandade", "soupe", "terrine", "thon", "saumon", "sardine", "maquereau", "façon meunière", "sauce", "cuisiné", "rillettes"]),
    "Huile d’olive extra vierge": (["huile", "olive"], ["tournesol", "colza", "pépins de raisin", "arachide", "sésame", "coco", "noix", "avocat"]),
    "Vinaigre balsamique": (["vinaigre", "balsamique"], ["sauce", "pesto", "cidre", "alcool", "ménager", "framboise", "xérès", "vin"]),
    "Sel marin": (["sel"], ["beurre", "piscine", "test", "céleri", "herbes", "bain"]),
    "Poivre noir": (["poivre"], ["mélange", "baies", "sel", "gris", "blanc"]),
    "Ducros basilic": (["basilic"], ["mélange", "croûtons", "persil", "thym", "herbes de provence", "sauce", "pesto"]),
    "Granola": (["granola", "mcvities", "cookies", "sablé", "palmier", "petit déjeuner", "lu", "bn", "prince"], ["kellogg's", "spécial k", "barre", "céréale (sauf si biscuit)", "yaourt"]),
    "Chocolat noir": (["chocolat"], ["biscuit", "granola", "spécial k", "sablé", "pâtissier", "lait", "blanc", "poudre", "boisson", "céréale", "tablette (sauf si dégustation)", "oeuf", "lapin"]),
    "Papier toilette": (["papier toilette", "toilette", "pq"], ["serviette", "essuie-tout", "mouchoir"]),
    "Sacs poubelles biodégradables": (["sac", "poubelle", "poubelles"], ["congélation", "zip", "courses", "gravats"]),
    "Liquide vaisselle": (["liquide vaisselle", "vaisselle"], ["eponge", "éponge", "pastille", "tablette", "lave-vaisselle", "poudre", "sel régénérant"]),
    "Lessive hypoallergénique": (["lessive"], ["adoucissant", "assouplissant", "détachant", "vaisselle", "nettoyant"]),
    "Nettoyant multi-usage": (["nettoyant", "lingette", "spray", "vinaigre", "multi-usage", "multi usage", "vinaigre"], ["lessive", "vaisselle", "vitres", "wc", "sols", "javel (sauf si nettoyant)"]),
    "Éponges de cuisine": ([], []),
    "Shampooing": (["shampooing", "shampoing"], ["gel douche", "après-shampooing", "après-shampoing", "masque", "soin", "savon", "coloration"]),
    "Gel douche": (["gel douche", "douche"], ["shampooing", "shampoing", "savon", "bain moussant", "huile lavante"]),
    "Dentifrice": (["dentifrice"], ["brosse à dents", "bain de bouche", "fil dentaire"]),
    "Savon mains": (["savon", "crème lavante", "gel lavant"], ["douche", "shampooing", "vaisselle", "lessive", "marseille (sauf si mains)", "alep", "noir"]),
    "Mouchoirs en papier": (["mouchoirs", "Mouchoir"], ["essuie-tout", "serviette"]),
    "Papier aluminium": (["aluminium", "albal"], ["film", "cuisson", "sulfurisé", "étirable", "cellophane"]),
    "Sacs de congélation": (["sac", "congélation", "congelation"], ["poubelle", "courses", "zip (sauf si congélation)"]),
    "Bouillon cube bio": (["bouillon", "kub"], ["liquide", "fond", "fumet", "pot au feu", "légumes déshydratés"])
}

# --- Chargement et Traitement ---

file_path = '/Users/pierreandrews/Desktop/Prix conso/CSV RELATIF/dataRELATIF.csv'
input_dir = os.path.dirname(file_path)
output_filename = 'dataRELATIF_nettoye.csv'
output_file = os.path.join(input_dir, output_filename)

try:
    # Charger le CSV
    df = pd.read_csv(file_path, delimiter=';', low_memory=False, dtype=str)
    df = df.replace(r'^\s*$', np.nan, regex=True)

    product_cols = [col for col in df.columns if col.endswith('_Produit')]
    categories_in_file = [col.replace('_Produit', '') for col in product_cols]

    print(f"Traitement de {len(categories_in_file)} catégories trouvées dans le fichier...")
    cleaned_counts_per_category = {}
    total_cleaned_entries = 0

    # --- Boucle de Nettoyage ---
    for category in keyword_rules:
        # (Le code de nettoyage reste identique)
        # ...
        col_produit = f"{category}_Produit"
        col_prix = f"{category}_Prix"
        col_unite = f"{category}_Unite"

        if col_produit not in df.columns:
            continue

        col_exists = {
            'prix': col_prix in df.columns,
            'unite': col_unite in df.columns
        }

        required_keywords, excluded_keywords = keyword_rules[category]
        indices_to_clear = []

        for index, product_name in df[col_produit].items():
            if pd.isna(product_name):
                continue

            product_name_lower = str(product_name).lower()
            is_relevant = False

            if not required_keywords:
                is_relevant = True
            else:
                for keyword in required_keywords:
                    if re.search(r'(?i)\b' + re.escape(keyword) + r'\b', product_name_lower):
                        is_relevant = True
                        break

            if is_relevant and excluded_keywords:
                for excluded in excluded_keywords:
                    if re.search(r'(?i)\b' + re.escape(excluded) + r'\b', product_name_lower):
                        is_relevant = False
                        break

            if not is_relevant:
                indices_to_clear.append(index)

        count_for_this_category = len(indices_to_clear)
        if count_for_this_category > 0:
            cleaned_counts_per_category[category] = count_for_this_category
            total_cleaned_entries += count_for_this_category

            df.loc[indices_to_clear, col_produit] = np.nan
            if col_exists['prix']:
                df.loc[indices_to_clear, col_prix] = np.nan
            if col_exists['unite']:
                df.loc[indices_to_clear, col_unite] = np.nan
        # (Les print pendant le nettoyage sont optionnels)

    print("\nNettoyage basé sur les mots-clés terminé.")
    print(f"Total de {total_cleaned_entries} entrées produit/prix/unité activement nettoyées.")

    # --- Calcul des valeurs manquantes/invalidées FINALES ---
    print("\nCalcul du nombre total de valeurs manquantes/invalidées par catégorie...")
    missing_summary = {}
    for category in categories_in_file:
        col_produit = f"{category}_Produit"
        if col_produit in df.columns:
            missing_count = df[col_produit].isna().sum()
            missing_summary[category] = missing_count
        else:
            missing_summary[category] = 0
            print(f"  - Avertissement: Colonne {col_produit} non trouvée pour le résumé des NaN.")

    # --- Création de la nouvelle ligne pour les comptes ---
    print("Création de la ligne de compte...")
    new_row_data = {}
    first_col_name = df.columns[0] # Nom de la première colonne
    new_row_data[first_col_name] = '--- COMPTE LIGNES INVALIDEES/MANQUANTES ---'

    for col in df.columns:
        if col == first_col_name:
            continue

        is_product_col = False
        category_name = None
        if col.endswith('_Produit'):
            is_product_col = True
            category_name = col.replace('_Produit', '')
        elif col.endswith('_Prix'):
             category_name = col.replace('_Prix', '')
        elif col.endswith('_Unite'):
             category_name = col.replace('_Unite', '')

        if is_product_col:
            count = missing_summary.get(category_name, 0)
            new_row_data[col] = count # Mettre le compte dans la colonne _Produit
        else:
            # Mettre NaN dans toutes les autres colonnes (Prix, Unite, Catégorie Ville etc.)
            # pour la ligne de compte.
            new_row_data[col] = np.nan

    new_row = pd.Series(new_row_data, index=df.columns)
    new_row_df = pd.DataFrame([new_row])

    # --- Insertion de la nouvelle ligne en PREMIÈRE position des DONNÉES ---
    print("Insertion de la ligne de compte...")
    # Concaténer la nouvelle ligne AVANT le DataFrame original
    # Utiliser ignore_index=True pour reconstruire l'index de 0 à N-1
    df_final = pd.concat([new_row_df, df], ignore_index=True)

    # --- Conversion des prix (à faire sur df_final, en ignorant la nouvelle ligne de compte à l'index 0) ---
    print("\nTentative de conversion des colonnes de prix en numérique (en ignorant la ligne de compte)...")
    for col in df_final.columns:
        if col.endswith('_Prix'):
            try:
                # Sélectionner toutes les lignes SAUF la première (index 0)
                rows_to_convert = df_final.index != 0
                # Appliquer le remplacement et la conversion sur ces lignes
                prices_to_convert = df_final.loc[rows_to_convert, col].astype(str).str.replace(',', '.', regex=False)
                numeric_prices = pd.to_numeric(prices_to_convert, errors='coerce')
                # Réassigner les valeurs converties aux lignes originales
                df_final.loc[rows_to_convert, col] = numeric_prices
                # print(f"  - Colonne {col} convertie.") # Optionnel
            except Exception as e:
                print(f"  - Erreur lors de la conversion de {col}: {e}")
    print("Conversion des prix terminée (les erreurs ont été transformées en NaN).")

    # --- Sauvegarde du résultat ---
    df_final.to_csv(output_file, sep=';', index=False, encoding='utf-8-sig')

    print(f"\nFichier nettoyé avec ligne de compte insérée en haut enregistré sous : {output_file}")

except FileNotFoundError:
    print(f"Erreur : Le fichier '{file_path}' n'a pas été trouvé.")
except pd.errors.EmptyDataError:
     print(f"Erreur : Le fichier '{file_path}' est vide.")
except Exception as e:
    print(f"Une erreur générale est survenue : {e}")
    import traceback
    traceback.print_exc()