from app_permis import load_data

try:
    print("Chargement des données...")
    df_all, _, _, _, _ = load_data()
    print('✓ Données chargées avec succès')
    print(f'✓ Nombre de lignes: {len(df_all)}')
    print(f'✓ Colonnes disponibles: {list(df_all.columns)}')
    print(f'✓ AN_DEPOT existe: {"AN_DEPOT" in df_all.columns}')
    if "AN_DEPOT" in df_all.columns:
        print(f'✓ AN_DEPOT type: {df_all["AN_DEPOT"].dtype}')
        print(f'✓ AN_DEPOT exemples: {df_all["AN_DEPOT"].dropna().head().tolist()}')
except Exception as e:
    print(f'✗ Erreur: {e}')
    import traceback
    traceback.print_exc()
