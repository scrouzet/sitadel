from app_permis import load_data

df_all = load_data()

# Calculer le nombre de projets par entreprise
entreprises_count = df_all[df_all['DENOM_DEM'].notna()]['DENOM_DEM'].value_counts()
top_entreprises = entreprises_count[entreprises_count >= 10].sort_values(ascending=False)

print(f"Nombre d'entreprises avec 10+ projets: {len(top_entreprises)}\n")
print("Top entreprises:")
for i, (nom, count) in enumerate(top_entreprises.items(), 1):
    print(f"{i:2}. {nom:45} : {count:3} projets")
