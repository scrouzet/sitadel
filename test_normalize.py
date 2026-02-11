from app_permis import load_data, normalize_text

print('Test de normalisation:')
tests = ['LP PROMOTION', 'lp-promotion', 'LP--PROMOTION', 'Café', 'CAFE', 'L.P/PROMOTION']
for test in tests:
    print(f'  "{test}" → "{normalize_text(test)}"')

print('\nChargement des données et test de recherche:')
df_all, _, _, _, _ = load_data()
recherche_norm = normalize_text('LP PROMOTION')
results = df_all[df_all['DENOM_DEM'].apply(lambda x: recherche_norm in normalize_text(x))]
print(f'Résultats pour "LP PROMOTION": {len(results)} entreprises trouvées')
if len(results) > 0:
    print('Exemples:')
    for nom in results['DENOM_DEM'].unique()[:5]:
        print(f'  - {nom}')
