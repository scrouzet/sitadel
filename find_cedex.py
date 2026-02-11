import pandas as pd

files = {
    'Logements': 'data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
    'Locaux non-resid': 'data/Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
    'Demolition': 'data/Liste-des-permis-de-demolir.2026-01.csv',
    'Amenagement': 'data/Liste-des-permis-damenager.2026-01.csv'
}

# Charger tous les codes INSEE
all_codes = set()
for nom, chemin in files.items():
    df = pd.read_csv(chemin, delimiter=';', low_memory=False)
    commune_col = [c for c in df.columns if 'commune' in c.lower() and 'code' in c.lower()][0]
    codes = df[commune_col].dropna()
    # Convertir en int en ignorant les erreurs
    for code in codes:
        try:
            all_codes.add(int(code))
        except:
            pass

# Codes de Toulouse Metropole
df_tm = pd.read_csv('data/Codes INSEE communes Toulouse Métropole.csv', delimiter=',')
codes_tm = set(df_tm['Code INSEE'].astype(int).unique())

# Codes absent de TM mais dans le dept 31
cedex_codes = sorted([c for c in all_codes if c not in codes_tm and 31000 <= c < 32000])

print(f'Codes Cedex/autres a Toulouse ({len(cedex_codes)}):')
for code in cedex_codes:
    print(f'  {code}')
