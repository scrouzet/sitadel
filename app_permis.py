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

@st.cache_data
def load_data():
    """Charge tous les fichiers CSV et les combine"""
    
    # Chemins des fichiers - relatif au script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(script_dir, "data", "")
    
    # Chargement des fichiers
    df_logements = pd.read_csv(
        base_path + "Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv",
        delimiter=";",
        low_memory=False
    )
    df_logements['TYPE_PROJET'] = 'Logements'
    
    df_locaux = pd.read_csv(
        base_path + "Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv",
        delimiter=";",
        low_memory=False
    )
    df_locaux['TYPE_PROJET'] = 'Locaux non résidentiels'
    
    df_demolir = pd.read_csv(
        base_path + "Liste-des-permis-de-demolir.2026-01.csv",
        delimiter=";",
        low_memory=False
    )
    df_demolir['TYPE_PROJET'] = 'Démolition'
    
    df_amenager = pd.read_csv(
        base_path + "Liste-des-permis-damenager.2026-01.csv",
        delimiter=";",
        low_memory=False
    )
    df_amenager['TYPE_PROJET'] = 'Aménagement'
    
    # Mapping des colonnes réelles pour harmoniser les noms
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
    
    # Renommer les colonnes pour tous les dataframes
    for df in [df_logements, df_locaux, df_demolir, df_amenager]:
        for col_original, col_nouveau in colonnes_mapping.items():
            if col_original in df.columns:
                df.rename(columns={col_original: col_nouveau}, inplace=True)
    
    # Colonnes harmonisées
    colonnes_communes = [
        'AN_DEPOT', 'APE_DEM', 'CJ_DEM', 'DENOM_DEM', 'SIREN_DEM', 'SIRET_DEM',
        'CODPOST_DEM', 'LOCALITE_DEM', 'TYPE_PROJET'
    ]
    
    # Ajouter les colonnes spécifiques pour identifier le numéro de permis
    # Pour logements et locaux, chercher NUM_DAU; pour demolir et amenager, adapter à ce qui existe
    for df in [df_logements, df_locaux, df_demolir, df_amenager]:
        # Chercher les colonnes qui pourraient contenir un numéro de permis
        num_cols = [c for c in df.columns if 'numéro' in c.lower() and 'permis' in c.lower() or 'dau' in c.lower()]
        if num_cols:
            df['NUMERO_PERMIS'] = df[num_cols[0]]
        else:
            df['NUMERO_PERMIS'] = None
    
    colonnes_communes.append('NUMERO_PERMIS')
    
    # Sélectionner uniquement les colonnes communes qui existent
    def select_existing_cols(df, cols):
        return df[[c for c in cols if c in df.columns]].copy()
    
    df_log = select_existing_cols(df_logements, colonnes_communes)
    df_loc = select_existing_cols(df_locaux, colonnes_communes)
    df_dem = select_existing_cols(df_demolir, colonnes_communes)
    df_ame = select_existing_cols(df_amenager, colonnes_communes)
    
    # Ajouter des colonnes manquantes avec NaN
    all_cols = set()
    for df in [df_log, df_loc, df_dem, df_ame]:
        all_cols.update(df.columns)
    
    for df in [df_log, df_loc, df_dem, df_ame]:
        for col in all_cols:
            if col not in df.columns:
                df[col] = None
    
    # Combiner tous les dataframes
    df_all = pd.concat([df_log, df_loc, df_dem, df_ame], ignore_index=True)
    
    # Convertir AN_DEPOT en numérique si la colonne existe
    if 'AN_DEPOT' in df_all.columns:
        df_all['AN_DEPOT'] = pd.to_numeric(df_all['AN_DEPOT'], errors='coerce')
    
    return df_all, df_logements, df_locaux, df_demolir, df_amenager

# Chargement des données
df_all, df_logements, df_locaux, df_demolir, df_amenager = load_data()

# Titre
st.title("🏗️ Explorateur de Permis de Construire - Toulouse")
st.markdown("---")

# Barre latérale pour la recherche
with st.sidebar:
    st.header("🔍 Recherche")
    
    # Choix du type de recherche
    type_recherche = st.radio(
        "Type de recherche",
        ["Nom d'entreprise", "SIREN", "SIRET"]
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
    else:
        recherche = st.text_input(
            "Numéro SIRET",
            placeholder="Ex: 12345678900012"
        )
        col_recherche = 'SIRET_DEM'
    
    # Options d'affichage
    st.markdown("---")
    st.subheader("Options")
    afficher_details = st.checkbox("Afficher tous les détails", value=False)

# Filtrer les résultats
if recherche:
    # Filtrage selon le type de recherche
    if type_recherche == "Nom d'entreprise":
        # Normaliser la recherche et les données pour la comparaison
        recherche_norm = normalize_text(recherche)
        df_filtered = df_all[
            df_all[col_recherche].apply(lambda x: recherche_norm in normalize_text(x))
        ]
    else:
        # Pour SIREN et SIRET, recherche exacte (sensible aux tirets)
        df_filtered = df_all[
            df_all[col_recherche].astype(str).str.contains(recherche, na=False)
        ]
    
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
            if afficher_details:
                cols_display = df_filtered.columns.tolist()
            else:
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
    # Affichage initial
    st.info("👈 Utilisez la barre latérale pour rechercher une entreprise ou un numéro SIREN/SIRET")
    
    # Statistiques globales
    st.subheader("📊 Aperçu général de la base de données")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de projets", len(df_all))
    
    with col2:
        if 'DENOM_DEM' in df_all.columns:
            st.metric("Entreprises distinctes", df_all['DENOM_DEM'].nunique())
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
