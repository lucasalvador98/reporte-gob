from moduls.carga import load_data_from_gitlab
import streamlit as st
from moduls import bco_gente, cbamecapacita, empleo
import requests

# Configuración de la página
st.set_page_config(page_title="Dashboard Integrado", layout="wide")

# Banner SVG superior - colocado antes de cualquier otro elemento
st.markdown("""
<div style="width:100%; overflow:hidden; margin-bottom:10px;">
    <svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 595.28 10.32" width="100%" height="10">
        <defs>
            <style>
                .cls-1 { fill: #bccf00; }
                .cls-2 { fill: #00a8e6; }
                .cls-3 { fill: #0085c8; }
                .cls-4 { fill: #e73446; }
                .cls-5 { fill: #8a1e82; }
                .cls-6 { fill: #fbbb21; }
                .cls-7 { fill: #ee7326; }
            </style>
        </defs>
        <g>
            <g id="Capa_1">
                <polygon class="cls-6" points="243.75 10.32 203.81 10.32 185.4 0 236.06 0 243.75 10.32"></polygon>
                <polygon class="cls-3" points="203.81 10.32 97.28 10.32 108.51 0 185.4 0 203.81 10.32"></polygon>
                <polygon class="cls-5" points="97.55 10.32 -2.8 10.32 -2.8 0 108.51 0 97.55 10.32"></polygon>
                <polygon class="cls-4" points="300.53 10.32 243.75 10.32 236.06 0 320.44 0 300.53 10.32"></polygon>
                <polygon class="cls-4" points="544.42 10.32 509.32 10.32 515.21 0 566.67 0 544.42 10.32"></polygon>
                <polygon class="cls-1" points="598.77 10.32 544.42 10.32 566.67 0 598.8 0 598.77 10.32"></polygon>
                <polygon class="cls-7" points="509.32 10.32 403.44 10.32 461.4 0 515.22 0 509.32 10.32"></polygon>
                <polygon class="cls-2" points="403.44 10.32 353.96 10.32 320.44 0 461.4 0 403.44 10.32"></polygon>
                <polygon class="cls-6" points="353.95 10.32 300.53 10.32 320.44 0 353.95 10.32"></polygon>
            </g>
        </g>
    </svg>
</div>
""", unsafe_allow_html=True)

# Estilos básicos
st.markdown("""
<style>
    /* Colores de la nueva identidad visual */
    :root {
        --color-primary: #0085c8;
        --color-secondary: #00a8e6;
        --color-accent-1: #e73446;
        --color-accent-2: #fbbb21;
        --color-accent-3: #bccf00;
        --color-accent-4: #8a1e82;
        --color-accent-5: #ee7326;
    }
    
    /* Estilos generales */
    .main-header {font-size: 2.5rem; font-weight: bold; text-align: center; color: var(--color-primary); margin-top: 10px;}
    .tab-subheader {font-size: 1.8rem; font-weight: bold; color: var(--color-primary);}
    
    /* Estilo para pestañas */
    .stTabs [aria-selected="true"] {background-color: var(--color-primary); color: white;}
    
    /* Estilo para el contenedor principal */
    .main {
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Tablero General de Reportes</div>', unsafe_allow_html=True)

# Configuración fija de GitLab
repo_id = "Dir-Tecno/Repositorio-Reportes"
branch = "main"

# Obtener token desde secrets
try:
    token = st.secrets["gitlab"]["token"]
except Exception as e:
    st.error(f"Error al obtener token: {str(e)}")
    st.stop()

# Cargar datos - Usar la función importada directamente
with st.spinner("Cargando datos.."):
    all_data, all_dates = load_data_from_gitlab(repo_id, branch, token)
    
    if not all_data:
        st.error("No se pudieron cargar los datos. Verifica el token y el ID del repositorio.")
        # Mostrar información de diagnóstico
        st.info("Información de diagnóstico:")
        st.code(f"Repositorio ID: {repo_id}")
        st.code(f"Token configurado: {'Sí' if token else 'No'}")
        st.stop()
    
    # Mapeo de archivos por módulo
    modules = {
        'bco_gente': ['vt_nomina_rep_dpto_localidad.parquet', 'VT_NOMINA_REP_RECUPERO_X_ANIO.parquet', 
                       'Detalle_recupero.csv', 'capa_departamentos_2010.geojson', 'LOCALIDAD CIRCUITO ELECTORAL GEO Y ELECTORES - USAR.txt'],
        'cba_capacita': ['ALUMNOS_X_LOCALIDAD.parquet', 'capa_departamentos_2010.geojson'],
        'empleo': ['VT_REPORTES_PPP_MAS26.parquet', 'vt_empresas_adheridas.parquet','vt_empresas_ARCA.parquet', 'VT_PUESTOS_X_FICHAS.parquet','capa_departamentos_2010.geojson', 'VT_REPORTE_LIQUIDACION_LOCALIDAD.parquet']
    }

    # Filtrar los datos para cada módulo
    bco_gente_data = {k: all_data.get(k) for k in modules['bco_gente'] if k in all_data}
    bco_gente_dates = {k: all_dates.get(k) for k in modules['bco_gente'] if k in all_dates}
    
    cba_capacita_data = {k: all_data.get(k) for k in modules['cba_capacita'] if k in all_data}
    cba_capacita_dates = {k: all_dates.get(k) for k in modules['cba_capacita'] if k in all_dates}
    
    empleo_data = {k: all_data.get(k) for k in modules['empleo'] if k in all_data}
    empleo_dates = {k: all_dates.get(k) for k in modules['empleo'] if k in all_dates}

# Crear pestañas
tabs = st.tabs(["Banco de la Gente", "CBA Me Capacita", "Programas de Empleo"])

# Pestaña 1: Banco de la Gente
with tabs[0]:
    st.markdown('<div class="tab-subheader">Banco de la Gente</div>', unsafe_allow_html=True)
    # Pasar solo los datos específicos del módulo
    bco_gente.show_bco_gente_dashboard(bco_gente_data, bco_gente_dates)

# Pestaña 2: CBA ME CAPACITA
with tabs[1]:
    st.markdown('<div class="tab-subheader">CBA ME CAPACITA</div>', unsafe_allow_html=True)
    # Pasar solo los datos específicos del módulo
    cbamecapacita.show_cba_capacita_dashboard(cba_capacita_data, cba_capacita_dates)

# Pestaña 3: Programas de Empleo
with tabs[2]:
    st.markdown('<div class="tab-subheader">Programas de Empleo</div>', unsafe_allow_html=True)
    # Pasar solo los datos específicos del módulo
    empleo.show_empleo_dashboard(empleo_data, empleo_dates)
