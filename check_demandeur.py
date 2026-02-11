import pandas as pd

print('RECHERCHE - Colonnes contenant maître d ouvrage / entreprise')
print('=' * 80)

# Vérifier logements (où DENOM_DEM est NULL)
df_log = pd.read_csv('data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv', delimiter=';', nrows=5)
print('\nFichier LOGEMENTS:')
print(f'Total colonnes: {len(df_log.columns)}')
print(f'Colonnes contenant "demandeur" ou "entreprise":')
found = False
for col in df_log.columns:
    if any(word in col.lower() for word in ['demandeur', 'maitrise', 'entreprise', 'promoteur', 'constructeur', 'dénomination']):
        print(f'  - {col}')
        found = True
if not found:
    print('  Aucune trouvée')

# Vérifier amenager (où DENOM_DEM est aussi NULL)
df_ame = pd.read_csv('data/Liste-des-permis-damenager.2026-01.csv', delimiter=';', nrows=5)
print('\nFichier AMÉNAGEMENT:')
print(f'Total colonnes: {len(df_ame.columns)}')
print(f'Colonnes contenant "demandeur" ou "entreprise":')
found = False
for col in df_ame.columns:
    if any(word in col.lower() for word in ['demandeur', 'maitrise', 'entreprise', 'promoteur', 'constructeur', 'dénomination']):
        print(f'  - {col}')
        found = True
if not found:
    print('  Aucune trouvée')

# Listing des colonnes de logements
print('\nTOUTES LES COLONNES - Logements:')
for i, col in enumerate(df_log.columns, 1):
    print(f'{i:2}. {col[:75]}')
