import pandas as pd

files = [
    'data/Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
    'data/Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
]

for f in files:
    df = pd.read_csv(f, delimiter=';', nrows=5)
    print(f"\n{f}:")
    print("Colonnes avec 'surface', 'superficie', 'SU', 'shob':")
    for col in df.columns:
        if any(x in col.lower() for x in ['surface', 'superficie', 'su', 'shob', 'shon']):
            print(f"  {col}")
