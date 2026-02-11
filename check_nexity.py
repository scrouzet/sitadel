import pandas as pd

# Chercher Nexity dans les donnees source
files = {
    'Logements': 'data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
    'Locaux non-resid': 'data/Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
    'Demolition': 'data/Liste-des-permis-de-demolir.2026-01.csv',
    'Amenagement': 'data/Liste-des-permis-damenager.2026-01.csv'
}

# Charger les codes INSEE de Toulouse Metropole
df_tm = pd.read_csv('data/Codes INSEE communes Toulouse Métropole.csv', delimiter=',')
codes_tm = set(df_tm['Code INSEE'].astype(str).str.strip().astype(int))

print('RECHERCHE NEXITY dans les donnees source:')
print('=' * 80)

for nom, chemin in files.items():
    df = pd.read_csv(chemin, delimiter=';', low_memory=False)
    denom_col = "Dénomination d'un demandeur avéré en tant que personne morale"
    if denom_col in df.columns:
        nexity = df[df[denom_col].astype(str).str.contains('NEXITY', case=False, na=False)]
        if len(nexity) > 0:
            print(f'\n{nom}: {len(nexity)} resultats')
            commune_col = [c for c in df.columns if 'commune' in c.lower() and 'code' in c.lower()][0]
            print(f"  Colonnes disponibles: {[c for c in df.columns if 'localite' in c.lower()]}")
            for idx, row in nexity.iterrows():
                code_insee = int(row[commune_col])
                in_tm = code_insee in codes_tm
                print(f"  Code INSEE: {code_insee:5} | Dans TM: {str(in_tm):5}")

print(f"\nCodes INSEE de Toulouse Metropole ({len(codes_tm)}):")
print(sorted(list(codes_tm)))
