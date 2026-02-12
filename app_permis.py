import streamlit as st
import pandas as pd
import plotly.express as px
import os
import unicodedata
import re

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Explorateur de Permis - Toulouse",
    page_icon="🏗️",
    layout="wide"
)

# 2. FONCTIONS DE NETTOYAGE ET CHARGEMENT
def clean_column_name(name):
    if not isinstance(name, str): return str(name)
    name = name.lower()
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    name = name.replace("’", "'").replace("'", " ")
    return re.sub(r'[^a-z0-9]', ' ', name).strip()

@st.cache_data(ttl=3600)
def load_collections():
    """Charge les fichiers de groupes avec nettoyage strict des SIREN et apostrophes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    collections = {}
    
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.startswith("Data PC -") and file.endswith(".csv"):
                group_name = file.replace("Data PC -", "").replace(".csv", "").strip()
                path = os.path.join(data_dir, file)
                try:
                    # On force la lecture en texte et on gère l'encodage
                    df_group = pd.read_csv(path, sep=None, engine='python', dtype=str)
                    
                    # 1. Nettoyage des colonnes (pour trouver 'SIREN' peu importe l'accent)
                    df_group.columns = [clean_column_name(c).upper() for c in df_group.columns]
                    
                    if 'SIREN' in df_group.columns:
                        # 2. Nettoyage strict des SIREN : on enlève tout ce qui n'est pas un chiffre
                        sirens = df_group['SIREN'].str.replace(r'\D', '', regex=True).dropna().unique().tolist()
                        collections[group_name] = sirens
                except Exception as e:
                    st.error(f"Erreur sur le groupe {group_name}: {e}")
    return collections


@st.cache_data(ttl=3600)
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    # Référentiel Communes
    communes_file = os.path.join(data_dir, "Codes INSEE communes Toulouse Métropole.csv")
    codes_insee_tolmetro = set()
    if os.path.exists(communes_file):
        df_communes = pd.read_csv(communes_file, delimiter=",")
        codes_insee_tolmetro = set(df_communes['Code INSEE'].astype(str).str.strip())
    
    CLEAN_TARGETS = {
        'code de la commune du lieu des travaux': 'CODE_COMMUNE',
        'annee de depot': 'AN_DEPOT',
        'denomination d un demandeur': 'DENOM_DEM',
        'numero siren': 'SIREN_DEM',
        'numero siret': 'SIRET_DEM',
        'numero d enregistrement': 'NUMERO_PERMIS',
        'localite du terrain': 'LOCALITE_TRAVAUX'
    }
    
    COLONNES_FINALES = ['TYPE_PROJET', 'NUMERO_PERMIS', 'AN_DEPOT', 'CODE_COMMUNE', 'DENOM_DEM', 'SIREN_DEM', 'SIRET_DEM', 'LOCALITE_TRAVAUX']
    
    def charger_fichier(filepath, type_projet):
        try:
            df = pd.read_csv(filepath, delimiter=";", low_memory=False, encoding='utf-8-sig', dtype=str)
        except:
            df = pd.read_csv(filepath, delimiter=";", low_memory=False, encoding='cp1252', dtype=str)
        
        mapping = {}
        for col in df.columns:
            cleaned = clean_column_name(col)
            for target_clean, target_name in CLEAN_TARGETS.items():
                if target_clean in cleaned:
                    mapping[col] = target_name
                    break
        
        df = df.rename(columns=mapping)
        df['TYPE_PROJET'] = type_projet
        
        for col in COLONNES_FINALES:
            if col not in df.columns: df[col] = None
        
        # Nettoyage strict du SIREN dans la base Sitadel (enlève espaces et points)
        if 'SIREN_DEM' in df.columns:
            df['SIREN_DEM'] = df['SIREN_DEM'].str.replace(r'\D', '', regex=True)
            
        if 'CODE_COMMUNE' in df.columns and codes_insee_tolmetro:
            df['CODE_COMMUNE'] = df['CODE_COMMUNE'].str.strip()
            df = df[df['CODE_COMMUNE'].isin(codes_insee_tolmetro)].copy()
            
        if 'AN_DEPOT' in df.columns:
            df['AN_DEPOT'] = pd.to_numeric(df['AN_DEPOT'], errors='coerce')
            df = df.dropna(subset=['AN_DEPOT'])
            
        return df[COLONNES_FINALES]

    fichiers = {
        'Logements': 'Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
        'Locaux': 'Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
        'Démolition': 'Liste-des-permis-de-demolir.2026-01.csv',
        'Aménagement': 'Liste-des-permis-damenager.2026-01.csv'
    }
    
    all_dfs = []
    for label, name in fichiers.items():
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            all_dfs.append(charger_fichier(path, label))
            
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

# 3. INITIALISATION
df_all = load_data()
dict_groupes = load_collections()

# 4. INTERFACE SIDEBAR
st.title("🏗️ Explorateur de Permis - Toulouse Métropole")

with st.sidebar:
    st.header("🔍 Recherche")
    voir_tout = st.checkbox("Afficher toutes les données", value=False)
    
    if not voir_tout:
        # Ajout du nouveau mode de recherche
        modes = ["Nom d'entreprise", "SIREN", "SIRET"]
        if dict_groupes:
            modes.append("Groupe d'entreprises")
            
        type_r = st.radio("Type de recherche", modes)
        
        recherche = ""
        groupe_selectionne = None
        
        if type_r == "Groupe d'entreprises":
            groupe_selectionne = st.selectbox("Sélectionnez un groupe", options=list(dict_groupes.keys()))
        else:
            recherche = st.text_input("Valeur (ex: COGEDIM)")
            col_r = {"Nom d'entreprise": 'DENOM_DEM', "SIREN": 'SIREN_DEM', "SIRET": 'SIRET_DEM'}[type_r]
    else:
        recherche = ""

# 5. LOGIQUE DE FILTRAGE
if voir_tout or (recherche and len(recherche) > 1) or (type_r == "Groupe d'entreprises" and not voir_tout):
    df_filtered = df_all.copy()
    
    if not voir_tout:
        if type_r == "Groupe d'entreprises":
            sirens_du_groupe = dict_groupes.get(groupe_selectionne, [])
            df_filtered = df_filtered[df_filtered['SIREN_DEM'].isin(sirens_du_groupe)]
        else:
            df_filtered = df_filtered[df_filtered[col_r].astype(str).str.contains(recherche, case=False, na=False)]
    
    # 6. AFFICHAGE DES RÉSULTATS
    if not df_filtered.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Projets", len(df_filtered))
        c2.metric("Entreprises distinctes", df_filtered['DENOM_DEM'].nunique())
        c3.metric("Période", f"{int(df_filtered['AN_DEPOT'].min())}-{int(df_filtered['AN_DEPOT'].max())}")

        tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "📋 Tableau détaillé", "📈 Graphiques"])
        with tab1:
            st.plotly_chart(px.pie(df_filtered, names='TYPE_PROJET', title="Répartition"), use_container_width=True)
            evol = df_filtered.groupby(['AN_DEPOT', 'TYPE_PROJET']).size().reset_index(name='N')
            st.plotly_chart(px.line(evol, x='AN_DEPOT', y='N', color='TYPE_PROJET', markers=True, title="Évolution"), use_container_width=True)
        with tab2:
            st.dataframe(df_filtered, use_container_width=True)
        with tab3:
            top_loc = df_filtered['LOCALITE_TRAVAUX'].value_counts().head(10)
            st.plotly_chart(px.bar(x=top_loc.values, y=top_loc.index, orientation='h', title="Top 10 Communes"))
    else:
        st.warning(f"Aucun projet trouvé pour cette sélection.")

else:
    # --- PAGE DE GARDE ---
    st.info("👈 Utilisez la barre latérale pour explorer par entreprise ou par groupe immobilier.")
    st.subheader("🏢 Top 15 des acteurs les plus actifs")
    stats_ent = df_all[df_all['DENOM_DEM'].notna()]['DENOM_DEM'].value_counts().head(15).reset_index()
    stats_ent.columns = ['Entreprise', 'Nombre de projets']
    st.dataframe(stats_ent, use_container_width=True, hide_index=True)