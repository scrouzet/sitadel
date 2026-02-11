from app_permis import load_data

df_all, _, _, _, _ = load_data()

print('TEST - Tous les projets:')
print(f'Total: {len(df_all)}')
print(f'Avec DENOM_DEM: {df_all["DENOM_DEM"].notna().sum()}')
print(f'Sans DENOM_DEM: {df_all["DENOM_DEM"].isna().sum()}')
print()
print('Par type:')
for typ in df_all['TYPE_PROJET'].unique():
    count = len(df_all[df_all['TYPE_PROJET'] == typ])
    print(f'  {typ}: {count}')
