import psutil
import os
from app_permis import load_data

# Récupérer l'utilisation mémoire avant
process = psutil.Process(os.getpid())
mem_before = process.memory_info().rss / 1024 / 1024  # En MB

print("Chargement des donnees optimisees...")
df_all = load_data()

# Récupérer l'utilisation mémoire après
mem_after = process.memory_info().rss / 1024 / 1024  # En MB

print("\n[OK] Donnees chargees avec succes")
print(f"\n[MEMORY]")
print(f"  Avant chargement : {mem_before:.1f} MB")
print(f"  Apres chargement : {mem_after:.1f} MB")
print(f"  Augmentation : {mem_after - mem_before:.1f} MB")

print(f"\n[SIZE] Taille du DataFrame en memoire : {df_all.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

print(f"\nTOTAL: {len(df_all)} projets")
print(f"Colonnes: {list(df_all.columns)}")
print(f"\nTypes de donnees optimises:")
print(df_all.dtypes)
