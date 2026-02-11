import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import unicodedata
import re

# Configuration de la page
st.set_page_config(
    page_title="Explorateur de Permis - Toulouse",
    page_icon="🏗️",
    layout="wide"
)

# Initialiser la session_state pour gérer l'accueil
if 'reset_search' not in st.session_state:
    st.session_state.reset_search = False

def normalize_text(text):
    """Normalise le texte pour améliorer la recherche: supprime accents, tirets, espaces multiples"""
    if pd.isna(text):
        return ""
    text = str(text)
    # Supprimer les accents
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
    # Remplacer tirets et caractères spéciaux par espaces
    text = re.sub(r'[-_/.]', ' ', text)
    # Supprimer espaces multiples
    text = re.sub(r'\s+', ' ', text)
    # Minuscules
    return text.lower().strip()

def get_cache_key():
    """Invalidate cache when the communes reference file changes"""
    import hashlib
    script_dir = os.path.dirname(os.path.abspath(__file__))
    communes_file = os.path.join(script_dir, "data", "Codes INSEE communes Toulouse Métropole.csv")
    if os.path.exists(communes_file):
        with open(communes_file, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    return "default"

@st.cache_data(hash_funcs={str: lambda x: x}, ttl=3600)
def load_data(_cache_key=None):
    """Charge tous les fichiers CSV et les combine pour Toulouse Métropole avec optimisation mémoire"""
    
    # Chemins des fichiers - relatif au script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, "data", "")
    
    # Charger la liste des communes de Toulouse Métropole
    df_communes_tolmétro = pd.read_csv(
        base_path + "Codes INSEE communes Toulouse Métropole.csv",
        delimiter=","
    )
    codes_insee_tolmetro = set(df_communes_tolmétro['Code INSEE'].astype(str))
    
    # Colonnes utiles de chaque fichier (pour réduire la mémoire)
    colonnes_a_garder = [
        'Code de la commune du lieu des travaux',
        'Année de dépôt de la DAU',
        "Code d'activité principale de l'établissement d'un demandeur avéré en tant que personne morale",
        "Catégorie juridique d'un demandeur avéré en tant que personne morale",
        "Dénomination d'un demandeur avéré en tant que personne morale",
        "Numéro SIREN d'un demandeur avéré en tant que personne morale",
        "Numéro SIRET d'un demandeur avéré en tant que personne morale",
        'Code postal du demandeur',
        'Localité du demandeur',
        "Numéro d'enregistrement de la DAU",
    ]
    
    # Fonction helper pour charger, filtrer et optimiser
    def load_filter_optimize(filepath, type_projet, delimiter=";"):
        # Charger avec colonnes limitées
        df = pd.read_csv(
            filepath, 
            delimiter=delimiter, 
            low_memory=False,
            usecols=colonnes_a_garder,
        )
        
        # Filtrer sur Toulouse Métropole - utiliser la colonne "Code de la commune du lieu des travaux"
        col_commune = 'Code de la commune du lieu des travaux'
        if col_commune in df.columns:
            df = df[df[col_commune].astype(str).isin(codes_insee_tolmetro)].copy()
        
        # Ajouter le type de projet
        df['TYPE_PROJET'] = type_projet
        
        # Optimiser les types de données
        for col in df.columns:
            if df[col].dtype == 'object':
                # Convertir les colonnes catégories en type category
                if col in ['TYPE_PROJET', 'Localité du demandeur']:
                    df[col] = df[col].astype('category')
                # Pour les colonnes quasi-vides, utiliser string plutôt que object
                elif df[col].notna().sum() / len(df) < 0.5:
                    df[col] = df[col].astype('string')
        
        return df
    
    # Charger et filtrer les 4 fichiers
    df_logements = load_filter_optimize(
        base_path + "Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv",
        'Logements'
    )
    
    df_locaux = load_filter_optimize(
        base_path + "Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv",
        'Locaux non résidentiels'
    )
    
    df_demolir = load_filter_optimize(
        base_path + "Liste-des-permis-de-demolir.2026-01.csv",
        'Démolition'
    )
    
    df_amenager = load_filter_optimize(
        base_path + "Liste-des-permis-damenager.2026-01.csv",
        'Aménagement'
    )
    
    # Mapping des colonnes réelles pour harmoniser les noms (version minimaliste)
    colonnes_mapping = {
        'Année de dépôt de la DAU': 'AN_DEPOT',
        "Code d'activité principale de l'établissement d'un demandeur avéré en tant que personne morale": 'APE_DEM',
        "Catégorie juridique d'un demandeur avéré en tant que personne morale": 'CJ_DEM',
        "Dénomination d'un demandeur avéré en tant que personne morale": 'DENOM_DEM',
        "Numéro SIREN d'un demandeur avéré en tant que personne morale": 'SIREN_DEM',
        "Numéro SIRET d'un demandeur avéré en tant que personne morale": 'SIRET_DEM',
        'Code postal du demandeur': 'CODPOST_DEM',
        'Localité du demandeur': 'LOCALITE_DEM',
    }
    
    # Dictionnaire pour tracker les suppressions par catégorie
    suppressions = {
        'Logements': {'avant': 0, 'apres': 0, 'details': {}},
        'Locaux non résidentiels': {'avant': 0, 'apres': 0, 'details': {}},
        'Démolition': {'avant': 0, 'apres': 0, 'details': {}},
        'Aménagement': {'avant': 0, 'apres': 0, 'details': {}}
    }
    
    dfs_and_names = [
        (df_logements, 'Logements'),
        (df_locaux, 'Locaux non résidentiels'),
        (df_demolir, 'Démolition'),
        (df_amenager, 'Aménagement')
    ]
    
    # Renommer et nettoyer les colonnes
    cleaned_dfs = {}
    for df_tmp, categorie in dfs_and_names:
        suppressions[categorie]['avant'] = len(df_tmp)
        
        # Renommer les colonnes
        for col_original, col_nouveau in colonnes_mapping.items():
            if col_original in df_tmp.columns:
                df_tmp.rename(columns={col_original: col_nouveau}, inplace=True)
        
        # Ajouter NUMERO_PERMIS
        num_cols = [c for c in df_tmp.columns if 'numéro' in c.lower() and 'enregistrement' in c.lower()]
        if num_cols:
            df_tmp.rename(columns={num_cols[0]: 'NUMERO_PERMIS'}, inplace=True)
        else:
            df_tmp['NUMERO_PERMIS'] = None
        
        # Convertir l'année en entier et nettoyer les valeurs invalides
        if 'AN_DEPOT' in df_tmp.columns:
            # Convertir en string pour traiter
            df_tmp['AN_DEPOT'] = df_tmp['AN_DEPOT'].astype(str).str.strip()
            
            # Compter les valeurs non numériques avant de les supprimer
            non_numeric_mask = ~df_tmp['AN_DEPOT'].str.isdigit()
            suppressions[categorie]['details']['Non-numériques (AN_DEPOT, etc.)'] = non_numeric_mask.sum()
            
            # Supprimer les valeurs non numériques
            df_tmp.loc[non_numeric_mask, 'AN_DEPOT'] = pd.NA
            
            # Convertir en entier
            df_tmp['AN_DEPOT'] = pd.to_numeric(df_tmp['AN_DEPOT'], errors='coerce')
            
            # Filtrer les années aberrantes (avant 2000 ou après 2030)
            before_filter = len(df_tmp)
            mask = (df_tmp['AN_DEPOT'].isna()) | ((df_tmp['AN_DEPOT'] >= 2000) & (df_tmp['AN_DEPOT'] <= 2030))
            df_tmp = df_tmp[mask].copy()
            aberrantes = before_filter - len(df_tmp)
            if aberrantes > 0:
                suppressions[categorie]['details']['Années aberrantes (< 2000 ou > 2030)'] = aberrantes
        
        suppressions[categorie]['apres'] = len(df_tmp)
        cleaned_dfs[categorie] = df_tmp
    
    # Récupérer les dataframes nettoyées
    df_logements = cleaned_dfs['Logements']
    df_locaux = cleaned_dfs['Locaux non résidentiels']
    df_demolir = cleaned_dfs['Démolition']
    df_amenager = cleaned_dfs['Aménagement']
    
    # Colonnes finales à conserver
    colonnes_finales = [
        'AN_DEPOT', 'DENOM_DEM', 'SIREN_DEM', 'SIRET_DEM',
        'LOCALITE_DEM', 'TYPE_PROJET', 'NUMERO_PERMIS'
    ]
    
    # Sélectionner uniquement les colonnes finales
    def select_final_cols(df):
        cols = [c for c in colonnes_finales if c in df.columns]
        return df[cols].copy()
    
    df_log = select_final_cols(df_logements)
    df_loc = select_final_cols(df_locaux)
    df_dem = select_final_cols(df_demolir)
    df_ame = select_final_cols(df_amenager)
    
    # Supprimer les dataframes originaux pour libérer la mémoire
    del df_logements, df_locaux, df_demolir, df_amenager
    
    # Ajouter les colonnes manquantes avec NaN
    all_cols = set()
    for df in [df_log, df_loc, df_dem, df_ame]:
        all_cols.update(df.columns)
    
    for df in [df_log, df_loc, df_dem, df_ame]:
        for col in all_cols:
            if col not in df.columns:
                df[col] = None
    
    # Combiner tous les dataframes
    df_all = pd.concat([df_log, df_loc, df_dem, df_ame], ignore_index=True)
    
    # Supprimer les dataframes temporaires
    del df_log, df_loc, df_dem, df_ame
    
    # Convertir AN_DEPOT en numérique
    if 'AN_DEPOT' in df_all.columns:
        df_all['AN_DEPOT'] = pd.to_numeric(df_all['AN_DEPOT'], errors='coerce')
    
    # Convertir TYPE_PROJET en category pour réduire la mémoire
    if 'TYPE_PROJET' in df_all.columns:
        df_all['TYPE_PROJET'] = df_all['TYPE_PROJET'].astype('category')
    
    # Retourner le dataframe et les statistiques de suppression
    return {
        'data': df_all,
        'suppressions': suppressions
    }

# Chargement des données avec invalidation de cache basée sur le fichier communes
result = load_data(_cache_key=get_cache_key())
df_all = result['data']
suppressions_data = result['suppressions']

# Titre
st.title("🏗️ Explorateur de Permis de Construire - Toulouse")
st.markdown("---")

# Barre latérale pour la recherche
with st.sidebar:
    # Bouton pour revenir à l'accueil
    if st.button("🏠 Accueil", use_container_width=True):
        st.session_state.reset_search = True
        st.rerun()
    
    st.markdown("---")
    st.header("🔍 Recherche")
    
    # Choix du type de recherche
    type_recherche = st.radio(
        "Type de recherche",
        ["Nom d'entreprise", "SIREN", "SIRET", "Toutes les données"]
    )
    
    # Champ de recherche
    if type_recherche == "Nom d'entreprise":
        recherche = st.text_input(
            "Nom de l'entreprise",
            placeholder="Ex: TOULOUSE, BOUYGUES, etc."
        )
        col_recherche = 'DENOM_DEM'
    elif type_recherche == "SIREN":
        recherche = st.text_input(
            "Numéro SIREN",
            placeholder="Ex: 123456789"
        )
        col_recherche = 'SIREN_DEM'
    elif type_recherche == "SIRET":
        recherche = st.text_input(
            "Numéro SIRET",
            placeholder="Ex: 12345678900012"
        )
        col_recherche = 'SIRET_DEM'
    else:
        st.info("ℹ️ Affichage de toutes les données disponibles")
        recherche = ""
        col_recherche = None
    
    # Avertissement pour les recherches par nom
    if type_recherche == "Nom d'entreprise":
        st.warning(
            "⚠️ **Important**: Seuls 29% des projets ont un nom d'entreprise. "
            "Les logements et aménagements n'ont généralement pas de nom d'entreprise."
        )

# Filtrer les résultats
if (recherche or type_recherche == "Toutes les données") and not st.session_state.reset_search:
    # Filtrage selon le type de recherche
    if type_recherche == "Nom d'entreprise":
        # Normaliser la recherche et les données pour la comparaison
        recherche_norm = normalize_text(recherche)
        df_filtered = df_all[
            df_all[col_recherche].apply(lambda x: recherche_norm in normalize_text(x))
        ]
    elif type_recherche == "SIREN":
        # Pour SIREN et SIRET, recherche exacte (sensible aux tirets)
        df_filtered = df_all[
            df_all[col_recherche].astype(str).str.contains(recherche, na=False)
        ]
    elif type_recherche == "SIRET":
        # Pour SIRET
        df_filtered = df_all[
            df_all[col_recherche].astype(str).str.contains(recherche, na=False)
        ]
    else:
        # Toutes les données
        df_filtered = df_all.copy()
    
    if len(df_filtered) > 0:
        st.success(f"✅ {len(df_filtered)} projet(s) trouvé(s)")
        
        # Statistiques générales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Nombre de projets", len(df_filtered))
        
        with col2:
            if 'AN_DEPOT' in df_filtered.columns and len(df_filtered['AN_DEPOT'].dropna()) > 0:
                annee_min = int(df_filtered['AN_DEPOT'].min())
                annee_max = int(df_filtered['AN_DEPOT'].max())
                st.metric("Période", f"{annee_min} - {annee_max}")
            else:
                st.metric("Période", "N/A")
        
        with col3:
            types = df_filtered['TYPE_PROJET'].nunique()
            st.metric("Types de projets", types)
        
        with col4:
            st.metric("Projets trouvés", len(df_filtered))
        
        # Onglets
        tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "📋 Tableau détaillé", "📈 Graphiques"])
        
        with tab1:
            st.subheader("Statistiques par type de projet")
            
            # Répartition par type
            col1, col2 = st.columns(2)
            
            with col1:
                type_counts = df_filtered['TYPE_PROJET'].value_counts()
                st.dataframe(
                    type_counts.reset_index().rename(columns={'index': 'Type', 'TYPE_PROJET': 'Nombre'}),
                    hide_index=True,
                    use_container_width=True
                )
            
            with col2:
                fig_pie = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="Répartition par type de projet"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # Évolution par année
            if 'AN_DEPOT' in df_filtered.columns and len(df_filtered['AN_DEPOT'].dropna()) > 0:
                st.subheader("Évolution temporelle")
                
                projets_par_annee = df_filtered.dropna(subset=['AN_DEPOT']).groupby(['AN_DEPOT', 'TYPE_PROJET']).size().reset_index(name='Nombre')
                
                fig_line = px.line(
                    projets_par_annee,
                    x='AN_DEPOT',
                    y='Nombre',
                    color='TYPE_PROJET',
                    markers=True,
                    title="Nombre de projets par année et par type"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            
            # Statistiques pour les projets logements
            df_log_filtered = df_filtered[df_filtered['TYPE_PROJET'] == 'Logements']
            if len(df_log_filtered) > 0:
                st.subheader("Projets de logements")
                st.info(f"Nombre de projets logements: {len(df_log_filtered)}")
        
        with tab2:
            st.subheader("Liste des projets")
            
            # Colonnes à afficher
            cols_display = [
                'TYPE_PROJET', 'NUMERO_PERMIS', 'DENOM_DEM', 'SIREN_DEM',
                'AN_DEPOT', 'LOCALITE_DEM'
            ]
            cols_display = [c for c in cols_display if c in df_filtered.columns]
            
            # Affichage du tableau
            st.dataframe(
                df_filtered[cols_display].reset_index(drop=True),
                use_container_width=True,
                height=400
            )
            
            # Bouton de téléchargement
            csv = df_filtered.to_csv(index=False, sep=';')
            st.download_button(
                label="📥 Télécharger les résultats (CSV)",
                data=csv,
                file_name=f"permis_{recherche}.csv",
                mime="text/csv"
            )
        
        with tab3:
            st.subheader("Visualisations complémentaires")
            
            # Localisation des projets
            col1, col2 = st.columns(2)
            
            with col1:
                if 'LOCALITE_DEM' in df_filtered.columns:
                    communes = df_filtered['LOCALITE_DEM'].value_counts().head(10)
                    fig_communes = px.bar(
                        x=communes.values,
                        y=communes.index,
                        orientation='h',
                        labels={'x': 'Nombre de projets', 'y': 'Localité'},
                        title="Top 10 des localités"
                    )
                    st.plotly_chart(fig_communes, use_container_width=True)
            
            with col2:
                if 'TYPE_PROJET' in df_filtered.columns:
                    types = df_filtered['TYPE_PROJET'].value_counts()
                    fig_types = px.bar(
                        x=types.index,
                        y=types.values,
                        labels={'x': 'Type de projet', 'y': 'Nombre'},
                        title="Distribution par type de projet"
                    )
                    st.plotly_chart(fig_types, use_container_width=True)
    
    elif recherche.strip() != "":
        st.warning(f"❌ Aucun projet trouvé pour '{recherche}'")
        
        # Suggérer quelques entreprises présentes
        st.info("💡 Quelques entreprises présentes dans la base :")
        entreprises_sample = df_all['DENOM_DEM'].dropna().unique()[:10]
        for ent in entreprises_sample:
            st.text(f"  • {ent}")

else:
    # Réinitialiser le flag
    if st.session_state.reset_search:
        st.session_state.reset_search = False
    
    # Affichage initial
    st.info("👈 Utilisez la barre latérale pour rechercher une entreprise ou un numéro SIREN/SIRET, ou sélectionnez 'Toutes les données'")
    
    st.success("✅ **Données filtrées**: Les 37 communes de Toulouse Métropole (Département 31)")
    
    st.warning("⚠️ **Attention données incomplètes**: Seuls **29% des projets** ont un nom d'entreprise associé. "
               "Les projets de logements et d'aménagement n'ont généralement pas d'entreprise renseignée.")
    
    # Afficher les statistiques de nettoyage des données
    with st.expander("📋 Détails du nettoyage des données"):
        st.markdown("**Lignes supprimées par défaut de données:**")
        
        for categorie, stats in suppressions_data.items():
            avant = stats['avant']
            apres = stats['apres']
            supprimees = avant - apres
            pct = (supprimees / avant * 100) if avant > 0 else 0
            
            st.markdown(f"**{categorie}**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Avant", avant)
            with col2:
                st.metric(f"Supprimées ({pct:.1f}%)", supprimees)
            
            # Détails des suppressions
            if stats['details']:
                for raison, nombre in stats['details'].items():
                    st.text(f"  • {raison}: {nombre} lignes")
            st.markdown("")
    
    # Statistiques globales
    st.subheader("📊 Aperçu général - Toulouse Métropole")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de projets", len(df_all))
    
    with col2:
        if 'DENOM_DEM' in df_all.columns:
            with_denom = df_all['DENOM_DEM'].notna().sum()
            st.metric("Avec nom d'entreprise", f"{with_denom} ({100*with_denom/len(df_all):.0f}%)")
        else:
            st.metric("Entreprises distinctes", "N/A")
    
    with col3:
        if 'AN_DEPOT' in df_all.columns and len(df_all['AN_DEPOT'].dropna()) > 0:
            annee_min = int(df_all['AN_DEPOT'].min())
            annee_max = int(df_all['AN_DEPOT'].max())
            st.metric("Période couverte", f"{annee_min} - {annee_max}")
        else:
            st.metric("Période couverte", "N/A")
    
    with col4:
        st.metric("Types de projets", df_all['TYPE_PROJET'].nunique())
    
    # Graphique de répartition
    st.subheader("Répartition des projets par type")
    type_counts = df_all['TYPE_PROJET'].value_counts()
    fig = px.bar(
        x=type_counts.index,
        y=type_counts.values,
        labels={'x': 'Type de projet', 'y': 'Nombre'},
        color=type_counts.index
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top entreprises (avec plus de 10 projets)
    st.subheader("Top entreprises (10+ projets)")
    
    # Calculer le nombre de projets par entreprise
    entreprises_count = df_all[df_all['DENOM_DEM'].notna()]['DENOM_DEM'].value_counts()
    top_entreprises = entreprises_count[entreprises_count >= 10].sort_values(ascending=False)
    
    if len(top_entreprises) > 0:
        fig_entreprises = px.bar(
            x=top_entreprises.index,
            y=top_entreprises.values,
            labels={'x': 'Entreprise', 'y': 'Nombre de projets'},
            title=f"Répartition des {len(top_entreprises)} entreprises ayant 10+ projets",
            color=top_entreprises.values,
            color_continuous_scale='Viridis'
        )
        fig_entreprises.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_entreprises, use_container_width=True)
        
        # Table récapitulative
        st.dataframe(
            top_entreprises.reset_index().rename(columns={'index': 'Entreprise', 'DENOM_DEM': 'Nombre de projets'}),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("Aucune entreprise avec 10+ projets dans les données.")
