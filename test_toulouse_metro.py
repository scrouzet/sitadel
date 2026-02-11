from app_permis import load_data

print("Chargement des données filtrées sur Toulouse Métropole...")
df_all, df_log, df_loc, df_dem, df_ame = load_data()

print(f"\n✅ Données chargées avec succès")
print(f"\nTOTAL: {len(df_all)} projets")
print(f"\nRépartition par type:")
for typ in sorted(df_all['TYPE_PROJET'].unique()):
    count = len(df_all[df_all['TYPE_PROJET'] == typ])
    print(f"  {typ:25} : {count:6} projets")

print(f"\nPériode couverte: {int(df_all['AN_DEPOT'].min())} - {int(df_all['AN_DEPOT'].max())}")

# Vérifier un promoteur bien connu
if len(df_all[df_all['DENOM_DEM'].notna()]) > 0:
    print(f"\nTop 5 promoteurs:")
    top5 = df_all['DENOM_DEM'].value_counts().head(5)
    for nom, count in top5.items():
        print(f"  {nom:40} : {count:3} projets")
