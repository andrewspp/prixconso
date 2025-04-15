import pandas as pd

def enrichir_uucp():
    # Chemins des fichiers
    uu_file = "/Users/pierreandrews/Desktop/Prix conso/dataUU/UU.csv"
    uucp_file = "/Users/pierreandrews/Desktop/Prix conso/dataUU/UUCP.csv"
    output_file = "/Users/pierreandrews/Desktop/Prix conso/dataUU/UUCP_enrichi.csv"
    
    print("Lecture des fichiers sources...")
    
    # Lecture des fichiers CSV
    # header=1 car la première ligne est une description des colonnes
    # et la deuxième ligne contient les vrais noms de colonnes
    try:
        uu_df = pd.read_csv(uu_file, sep=";", header=1)
        uucp_df = pd.read_csv(uucp_file, sep=";", header=1)
    except Exception as e:
        print(f"Erreur lors de la lecture des fichiers: {e}")
        return
    
    print(f"Fichier UU.csv: {len(uu_df)} lignes")
    print(f"Fichier UUCP.csv: {len(uucp_df)} lignes")
    
    # Sélection des colonnes à joindre depuis UU.csv - ajout de TDUU2017
    uu_selected = uu_df[['UU2020', 'TUU2017', 'TDUU2017', 'TYPE_UU2020']]
    
    # Fusion des DataFrames sur la clé commune UU2020
    print("Fusion des données en cours...")
    merged_df = pd.merge(uucp_df, uu_selected, on='UU2020', how='left')
    
    print(f"Résultat après fusion: {len(merged_df)} lignes")
    
    # Pour conserver le format original avec deux lignes d'en-tête,
    # extraction des en-têtes originaux du fichier UUCP
    with open(uucp_file, 'r', encoding='utf-8') as f:
        header_line1 = f.readline().strip()
        header_line2 = f.readline().strip()
    
    # Ajout des nouvelles colonnes aux en-têtes
    header_line1 += ";Tranche d'unité urbaine 2020 calculée sur la population 2017;Tranche détaillée d'unité urbaine 2020 calculée sur la population 2017;Type d'unité urbaine"
    header_line2 += ";TUU2017;TDUU2017;TYPE_UU2020"
    
    # Écriture du fichier de sortie
    print(f"Enregistrement du résultat dans {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header_line1 + "\n")
        f.write(header_line2 + "\n")
    
    # Ajout des données au fichier de sortie
    merged_df.to_csv(output_file, sep=';', index=False, mode='a', header=False)
    
    # Vérification des valeurs manquantes
    missing_count = merged_df['TUU2017'].isna().sum()
    if missing_count > 0:
        print(f"Attention: {missing_count} lignes n'ont pas pu être associées à un TUU2017/TDUU2017/TYPE_UU2020")
    
    print("Opération terminée avec succès!")

if __name__ == "__main__":
    enrichir_uucp()