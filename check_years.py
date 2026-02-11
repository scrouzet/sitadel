import pandas as pd
import os

files = [
    'data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
    'data/Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
    'data/Liste-des-permis-de-demolir.2026-01.csv',
    'data/Liste-des-permis-damenager.2026-01.csv'
]

print('VÉRIFICATION DES ANNÉES (valeurs uniques):')
print('=' * 60)

for f in files:
    if os.path.exists(f):
        df = pd.read_csv(f, delimiter=';', usecols=['Année de dépôt de la DAU'])
        col = df['Année de dépôt de la DAU'].astype(str).str.strip()
        print(f'\n{os.path.basename(f)}:')
        unique_vals = sorted(col.unique())
        print(f'  Nombre de valeurs : {len(unique_vals)}')
        # Afficher les 5 plus petites et 5 plus grandes
        print(f'  Plus petites : {unique_vals[:5]}')
        print(f'  Plus grandes : {unique_vals[-5:]}')
