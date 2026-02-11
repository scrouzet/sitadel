import pandas as pd

files = [
    'data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
]

for f in files:
    df = pd.read_csv(f, delimiter=';', nrows=5)
    print("Colonnes avec 'localité' ou 'lieu':")
    for col in df.columns:
        if 'local' in col.lower() or 'lieu' in col.lower():
            print(f"  {col}")
