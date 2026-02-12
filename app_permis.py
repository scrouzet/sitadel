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

def clean_column_name(name):
    """Normalise les noms de colonnes pour ignorer accents, casses et apostrophes"""
    if not isinstance(name, str): return str(name)
    name = name.lower()
    # Normalisation Unicode (supprime les accents)
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')
    # Remplace les apostrophes courbes par des droites et supprime les caractères spéciaux
    name = name.replace("’", "'").replace("'", " ")
    return re.sub(r'[^a-z0-9]', ' ', name).strip()

@st.cache_data(ttl=3600)
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    # 1. Référentiel Communes
    communes_file = os.path.join(data_dir, "Codes INSEE communes Toulouse Métropole.csv")
    df_communes = pd.read_csv(communes_file, delimiter=",")
    codes_insee_tolmetro = set(df_communes['Code INSEE'].astype(str).str.strip())
    
    # Mapping basé sur des noms "nettoyés" (sans accents, minuscules)
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
        # Essai systématique de l'encodage pour éviter les erreurs
        try:
            df = pd.read_csv(filepath, delimiter=";", low_memory=False, encoding='utf-8-sig', dtype=str)
        except:
            df = pd.read_csv(filepath, delimiter=";", low_memory=False, encoding='cp1252', dtype=str)
        
        # Renommage intelligent
        mapping = {}
        for col in df.columns:
            cleaned = clean_column_name(col)
            # On cherche si l'une de nos cibles est contenue dans le nom nettoyé
            for target_clean, target_name in CLEAN_TARGETS.items():
                if target_clean in cleaned:
                    mapping[col] = target_name
                    break
        
        df = df.rename(columns=mapping)
        df['TYPE_PROJET'] = type_projet
        
        # Sécurité : créer les colonnes si le mapping a échoué
        for col in COLONNES_FINALES:
            if col not in df.columns: df[col] = None
            
        # Nettoyage des données
        if 'CODE_COMMUNE' in df.columns:
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

# --- Application ---
df_all = load_data()

st.title("🏗️ Explorateur de Permis - Toulouse Métropole")

with st.sidebar:
    st.header("🔍 Recherche")
    voir_tout = st.checkbox("Afficher toutes les données", value=False)
    if not voir_tout:
        type_r = st.radio("Type", ["Nom d'entreprise", "SIREN", "SIRET"])
        recherche = st.text_input("Valeur (ex: COGEDIM)")
        col_r = {"Nom d'entreprise": 'DENOM_DEM', "SIREN": 'SIREN_DEM', "SIRET": 'SIRET_DEM'}[type_r]
    else:
        recherche = ""

if voir_tout or (recherche and len(recherche) > 1):
    # --- AFFICHAGE DES RÉSULTATS DE RECHERCHE (Tes onglets existants) ---
    df_filtered = df_all.copy()
    if not voir_tout:
        df_filtered = df_filtered[df_filtered[col_r].astype(str).str.contains(recherche, case=False, na=False)]
    
    if not df_filtered.empty:
        # Métriques
        c1, c2, c3 = st.columns(3)
        c1.metric("Projets trouvés", len(df_filtered))
        c2.metric("Entreprises", df_filtered['DENOM_DEM'].nunique())
        c3.metric("Période", f"{int(df_filtered['AN_DEPOT'].min())}-{int(df_filtered['AN_DEPOT'].max())}")

        tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "📋 Tableau détaillé", "📈 Graphiques"])
        with tab1:
            st.plotly_chart(px.pie(df_filtered, names='TYPE_PROJET', title="Répartition"), use_container_width=True)
            evol = df_filtered.groupby(['AN_DEPOT', 'TYPE_PROJET']).size().reset_index(name='N')
            st.plotly_chart(px.line(evol, x='AN_DEPOT', y='N', color='TYPE_PROJET', markers=True), use_container_width=True)
        with tab2:
            st.dataframe(df_filtered, use_container_width=True)
        with tab3:
            top_loc = df_filtered['LOCALITE_TRAVAUX'].value_counts().head(10)
            st.plotly_chart(px.bar(x=top_loc.values, y=top_loc.index, orientation='h', title="Top 10 Communes"))
    else:
        st.warning("Aucun résultat.")

else:
    # --- NOUVELLE PAGE DE GARDE (TOP ACTEURS) ---
    st.info("👈 Saisissez un nom d'entreprise ou un SIREN dans la barre latérale pour explorer les détails.")
    
    st.subheader("🏢 Classement des entreprises les plus actives")
    st.markdown("Acteurs ayant déposé **au moins 10 dossiers** sur le périmètre de Toulouse Métropole.")

    if not df_all.empty:
        # Calcul du top
        stats_ent = df_all[df_all['DENOM_DEM'].notna()]['DENOM_DEM'].value_counts().reset_index()
        stats_ent.columns = ['Entreprise', 'Nombre de projets']
        
        # Filtre 10+ et tri
        top_acteurs = stats_ent[stats_ent['Nombre de projets'] >= 10].sort_values(by='Nombre de projets', ascending=False)

        if not top_acteurs.empty:
            col_table, col_info = st.columns([2, 1])
            
            with col_table:
                st.dataframe(
                    top_acteurs,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Entreprise": st.column_config.TextColumn("Nom de l'entreprise"),
                        "Nombre de projets": st.column_config.ProgressColumn(
                            "Nombre de permis",
                            format="%d",
                            min_value=0,
                            max_value=int(top_acteurs['Nombre de projets'].max())
                        ),
                    }
                )
            
            with col_info:
                # Statistiques de résumé
                total_projets = len(df_all)
                st.metric("Total des permis en base", total_projets)
                st.metric("Entreprises recensées", len(stats_ent))
                
                # Petit donut chart pour le fun
                fig_donut = px.pie(
                    df_all, 
                    names='TYPE_PROJET', 
                    hole=0.5,
                    title="Répartition par type (Global)"
                )
                fig_donut.update_layout(showlegend=False)
                st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.write("Aucune entreprise ne dépasse les 10 projets dans la base.")