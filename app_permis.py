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
    """Charge les fichiers de groupes avec double sécurité (SIREN + Mot-clé)"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    collections = {}
    
    if os.path.exists(data_dir):
        for file in os.listdir(data_dir):
            if file.startswith("Data PC -") and file.endswith(".csv"):
                group_name = file.replace("Data PC -", "").replace(".csv", "").strip()
                path = os.path.join(data_dir, file)
                try:
                    df_group = pd.read_csv(path, sep=None, engine='python', dtype=str)
                    df_group.columns = [clean_column_name(c).upper() for c in df_group.columns]
                    
                    # SIREN : Nettoyage strict (uniquement les chiffres)
                    sirens = []
                    # Dans la fonction load_collections() :
                    if 'SIREN' in df_group.columns:
                        sirens = df_group['SIREN'].str.replace(r'\D', '', regex=True).dropna().unique().tolist()
                        
                        # ON AJOUTE CETTE LIGNE :
                        keyword = group_name.upper() 
                        
                        # ON MODIFIE LE DICTIONNAIRE :
                        collections[group_name] = {"sirens": sirens, "keyword": keyword}
                        
                    # On définit le nom du groupe comme mot-clé pour capturer les dérivés (ex: "LP PROMOTION BOREAL")
                    collections[group_name] = {
                        "sirens": sirens,
                        "keyword": group_name.upper()
                    }
                except Exception as e:
                    st.error(f"Erreur sur le groupe {group_name}: {e}")
    return collections

@st.cache_data(ttl=3600)
def load_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    
    communes_file = os.path.join(data_dir, "Codes INSEE communes Toulouse Métropole.csv")
    codes_insee_tolmetro = set()
    if os.path.exists(communes_file):
        df_com = pd.read_csv(communes_file, delimiter=",")
        codes_insee_tolmetro = set(df_com['Code INSEE'].astype(str).str.strip())
    
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
        debug_log = []
        try:
            df = pd.read_csv(filepath, delimiter=";", low_memory=False, encoding='utf-8-sig', dtype=str)
        except:
            df = pd.read_csv(filepath, delimiter=";", low_memory=False, encoding='cp1252', dtype=str)
        
        debug_log.append(f"Chargé: {len(df)} lignes")
        
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
            
        if 'SIREN_DEM' in df.columns:
            df['SIREN_DEM'] = df['SIREN_DEM'].str.replace(r'\D', '', regex=True)
            
        if 'CODE_COMMUNE' in df.columns and codes_insee_tolmetro:
            df['CODE_COMMUNE'] = df['CODE_COMMUNE'].str.strip()
            df = df[df['CODE_COMMUNE'].isin(codes_insee_tolmetro)].copy()
            
        if 'AN_DEPOT' in df.columns:
            df['AN_DEPOT'] = pd.to_numeric(df['AN_DEPOT'], errors='coerce')
            df = df.dropna(subset=['AN_DEPOT'])
            
        return df[COLONNES_FINALES], debug_log

    fichiers = {
        'Logements': 'Liste-des-autorisations-durbanisme-creant-des-logements.2026-01.csv',
        'Locaux': 'Liste-des-autorisations-durbanisme-creant-des-locaux-non-residentiels.2026-01.csv',
        'Démolition': 'Liste-des-permis-de-demolir.2026-01.csv',
        'Aménagement': 'Liste-des-permis-damenager.2026-01.csv'
    }
    
    all_dfs, debug_logs = [], {}
    for label, name in fichiers.items():
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            df_p, log = charger_fichier(path, label)
            all_dfs.append(df_p)
            debug_logs[label] = log
            
    return pd.concat(all_dfs, ignore_index=True), debug_logs

# 3. INITIALISATION
df_all, debug_logs = load_data()
dict_groupes = load_collections()

# 4. INTERFACE
st.title("🏗️ Explorateur de Permis - Toulouse Métropole")

with st.sidebar:
    st.header("🔍 Recherche")
    voir_tout = st.checkbox("Afficher toutes les données", value=False)
    
    if not voir_tout:
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

# 5. LOGIQUE D'AFFICHAGE
# On déclenche l'affichage si voir_tout est coché, ou si une recherche est saisie, ou si on est en mode Groupe
is_searching = voir_tout or (not voir_tout and type_r == "Groupe d'entreprises") or (recherche and len(recherche) > 1)

if is_searching:
    df_filtered = df_all.copy()
    
    if not voir_tout:
        if type_r == "Groupe d'entreprises":
            info_groupe = dict_groupes.get(groupe_selectionne, {})
            
            # Sécurité 1 : On cherche par SIREN (ceux du fichier CSV)
            liste_siren = info_groupe.get("sirens", [])
            mask_siren = df_filtered['SIREN_DEM'].isin(liste_siren)
            
            # Sécurité 2 : On cherche par NOM (si le nom contient "LP PROMOTION" par ex)
            mot_cle = info_groupe.get("keyword", "")
            mask_nom = df_filtered['DENOM_DEM'].str.contains(mot_cle, case=False, na=False)
            
            # On applique le filtre "L'un OU l'autre" (| signifie OU)
            df_filtered = df_filtered[mask_siren | mask_nom]
        else:
            df_filtered = df_filtered[df_filtered[col_r].astype(str).str.contains(recherche, case=False, na=False)]
    
    if not df_filtered.empty:
        # Métriques
        c1, c2, c3 = st.columns(3)
        c1.metric("Projets", len(df_filtered))
        c2.metric("Entreprises", df_filtered['DENOM_DEM'].nunique())
        c3.metric("Période", f"{int(df_filtered['AN_DEPOT'].min())}-{int(df_filtered['AN_DEPOT'].max())}")

        # RÉTABLISSEMENT DES 4 ONGLETS
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Statistiques", "📋 Tableau détaillé", "📈 Graphiques", "🔍 Debug"])
        
        with tab1:
            st.plotly_chart(px.pie(df_filtered, names='TYPE_PROJET', title="Répartition par type"), use_container_width=True)
            evol = df_filtered.groupby(['AN_DEPOT', 'TYPE_PROJET']).size().reset_index(name='N')
            st.plotly_chart(px.line(evol, x='AN_DEPOT', y='N', color='TYPE_PROJET', markers=True, title="Évolution annuelle"), use_container_width=True)
        
        with tab2:
            st.dataframe(df_filtered, use_container_width=True)
            st.download_button("📥 Télécharger CSV", df_filtered.to_csv(index=False, sep=';'), "extract.csv")
            
        with tab3:
            if 'LOCALITE_TRAVAUX' in df_filtered.columns:
                top_loc = df_filtered['LOCALITE_TRAVAUX'].value_counts().head(10)
                st.plotly_chart(px.bar(x=top_loc.values, y=top_loc.index, orientation='h', title="Top 10 Communes"))

        with tab4:
            st.subheader("Logs de chargement")
            for t, logs in debug_logs.items():
                with st.expander(f"Fichier : {t}"):
                    for l in logs: st.text(l)
    else:
        st.warning("Aucun résultat pour cette sélection.")

else:
    # --- PAGE DE GARDE (TOP ACTEURS) ---
    st.info("👈 Utilisez la barre latérale pour explorer les données.")
    
    st.subheader("🏢 Classement des demandeurs les plus actifs")
    st.markdown("Acteurs ayant déposé **au moins 10 dossiers** (Tri décroissant).")

    if not df_all.empty:
        stats_ent = df_all[df_all['DENOM_DEM'].notna()]['DENOM_DEM'].value_counts().reset_index()
        stats_ent.columns = ['Entreprise', 'Nombre de projets']
        top_acteurs = stats_ent[stats_ent['Nombre de projets'] >= 10].sort_values(by='Nombre de projets', ascending=False)

        if not top_acteurs.empty:
            col_table, col_info = st.columns([2, 1])
            with col_table:
                st.dataframe(
                    top_acteurs,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Entreprise": st.column_config.TextColumn("Dénomination"),
                        "Nombre de projets": st.column_config.ProgressColumn(
                            "Nombre de permis",
                            format="%d",
                            min_value=0,
                            max_value=int(top_acteurs['Nombre de projets'].max())
                        ),
                    }
                )
            with col_info:
                st.metric("Total Permis en base", len(df_all))
                st.plotly_chart(px.pie(df_all, names='TYPE_PROJET', hole=.4, title="Répartition globale"), use_container_width=True)