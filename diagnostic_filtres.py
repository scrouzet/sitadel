import pandas as pd
import os
from app_permis import normalize_text

print("=" * 80)
print("DIAGNOSTIC COMPLET - Vérification des filtres de données")
print("=" * 80)

# Charger les données brutes
files = {
    'Logements': 'data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
    'Locaux non-résidentiels': 'data/Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
    'Démolition': 'data/Liste-des-permis-de-demolir.2026-01.csv',
    'Aménagement': 'data/Liste-des-permis-damenager.2026-01.csv'
}

total_brut = 0
print("\n1️⃣  DONNÉES BRUTES (avant traitement):")
print("-" * 80)
for nom, chemin in files.items():
    df = pd.read_csv(chemin, delimiter=';', low_memory=False)
    total_brut += len(df)
    print(f"  {nom:30} : {len(df):6} lignes")
    
    # Vérifier DENOM_DEM
    denom_col = "Dénomination d'un demandeur avéré en tant que personne morale"
    if denom_col in df.columns:
        valides = df[denom_col].notna().sum()
        print(f"    ├─ DENOM_DEM non-null    : {valides:6} ({100*valides/len(df):.1f}%)")
        print(f"    └─ DENOM_DEM null        : {len(df)-valides:6} ({100*(len(df)-valides)/len(df):.1f}%)")

print(f"\n  TOTAL BRUT : {total_brut} lignes")

# Charger avec la fonction du code
print("\n2️⃣  DONNÉES APRÈS load_data() (après harmonisation):")
print("-" * 80)
from app_permis import load_data
df_all, df_log, df_loc, df_dem, df_ame = load_data()
print(f"  Total combiné : {len(df_all)} lignes")
print(f"    ├─ Perte : {total_brut - len(df_all)} lignes ({100*(total_brut-len(df_all))/total_brut:.2f}%)")

# Vérifier les colonnes critiques
print("\n3️⃣  COLONNES CRITIQUES (non-null):")
print("-" * 80)
critical_cols = ['DENOM_DEM', 'SIREN_DEM', 'SIRET_DEM', 'AN_DEPOT']
for col in critical_cols:
    if col in df_all.columns:
        valides = df_all[col].notna().sum()
        print(f"  {col:20} : {valides:6} / {len(df_all):6} ({100*valides/len(df_all):5.1f}%)")
    else:
        print(f"  {col:20} : COLONNE MANQUANTE ❌")

# Test de recherche - simuler une recherche réelle
print("\n4️⃣  TEST DE RECHERCHE - 'BOUYGUES':")
print("-" * 80)

# Avant normalization
bouygues_brut = df_all[df_all['DENOM_DEM'].astype(str).str.contains('BOUYGUES', case=False, na=False)]
print(f"  Résultats (ancien code) : {len(bouygues_brut)} projets")

# Avec normalization
recherche_norm = normalize_text('BOUYGUES')
bouygues_norm = df_all[df_all['DENOM_DEM'].apply(lambda x: recherche_norm in normalize_text(x))]
print(f"  Résultats (code actuel) : {len(bouygues_norm)} projets")

if len(bouygues_norm) > 0:
    print(f"  Variantes trouvées:")
    for idx, nom in enumerate(bouygues_norm['DENOM_DEM'].unique()[:10], 1):
        print(f"    {idx}. {nom}")

# Vérifier les données null
print("\n5️⃣  ANALYSE DES DONNÉES NULL:")
print("-" * 80)
null_cols = ['DENOM_DEM', 'SIREN_DEM']
for col in null_cols:
    if col in df_all.columns:
        null_count = df_all[col].isna().sum()
        if null_count > 0:
            print(f"  ⚠️  {col}: {null_count} valeurs NULL")
            # Voir les types de projets avec null
            types_with_null = df_all[df_all[col].isna()]['TYPE_PROJET'].value_counts()
            for typ, count in types_with_null.items():
                print(f"       ├─ {typ}: {count}")

# Résumé par type de projet
print("\n6️⃣  DISTRIBUTION PAR TYPE DE PROJET:")
print("-" * 80)
for typ in df_all['TYPE_PROJET'].unique():
    count = len(df_all[df_all['TYPE_PROJET'] == typ])
    with_denom = df_all[(df_all['TYPE_PROJET'] == typ) & (df_all['DENOM_DEM'].notna())].shape[0]
    print(f"  {typ:25} : {count:6} projets ({with_denom:6} avec DENOM_DEM)")

print("\n" + "=" * 80)
print("FIN DIAGNOSTIC")
print("=" * 80)
