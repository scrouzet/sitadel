# Explorateur de Permis de Construire - Toulouse

Application Streamlit pour explorer les permis de construire, aménager et démolir dans la région toulousaine.

## Fonctionnalités

- 🔍 **Recherche multi-critères** : par nom d'entreprise, SIREN ou SIRET
- 📊 **Statistiques détaillées** : nombre de projets, répartition par type, évolution temporelle
- 📋 **Tableau complet** : visualisation de tous les projets avec leurs détails
- 📈 **Graphiques interactifs** : visualisations avec Plotly
- 📥 **Export CSV** : téléchargement des résultats filtrés

## Données intégrées

L'application charge et combine 4 types de données :
- Autorisations d'urbanisme créant des logements
- Autorisations d'urbanisme créant des locaux non résidentiels
- Permis de démolir
- Permis d'aménager

## Installation

### Prérequis

```bash
pip install streamlit pandas plotly
```

### Lancement

```bash
streamlit run app_permis.py
```

L'application s'ouvrira automatiquement dans votre navigateur par défaut.

## Utilisation

1. **Recherche** : Utilisez la barre latérale pour :
   - Choisir le type de recherche (Nom d'entreprise, SIREN ou SIRET)
   - Saisir votre critère de recherche
   
2. **Consultation des résultats** :
   - Onglet "Statistiques" : vue synthétique avec KPIs et graphiques
   - Onglet "Tableau détaillé" : liste complète des projets avec option d'export
   - Onglet "Graphiques" : visualisations complémentaires (communes, superficies)

3. **Options** :
   - Cochez "Afficher tous les détails" pour voir toutes les colonnes disponibles
   - Utilisez le bouton de téléchargement pour exporter les résultats

## Exemples de recherche

- **Par entreprise** : "TOULOUSE", "BOUYGUES", "VINCI"
- **Par SIREN** : "123456789"
- **Par SIRET** : "12345678900012"

## Structure des données

Les fichiers CSV doivent être placés dans `/mnt/user-data/uploads/` :
- `Liste-des-autorisations-durbanisme-creant-des-logements_2026-01.csv`
- `Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels_2026-01.csv`
- `Liste-des-permis-de-demolir_2026-01.csv`
- `Liste-des-permis-damenager_2026-01.csv`

## Statistiques disponibles

### Globales
- Nombre total de projets
- Période couverte
- Nombre d'entreprises distinctes
- Répartition par type de projet

### Par entreprise
- Nombre de projets
- Types de projets réalisés
- Évolution temporelle
- Surfaces totales de terrain
- Pour les logements : nombre de logements créés par année
- Répartition géographique

## Notes techniques

- L'application utilise `@st.cache_data` pour optimiser le chargement des données
- Les recherches par nom sont insensibles à la casse
- Les fichiers CSV sont lus avec le délimiteur `;`
- Les données sont combinées dans un dataframe unique pour faciliter la recherche cross-type
