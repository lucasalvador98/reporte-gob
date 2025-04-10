from moduls.carga import load_data_from_gitlab
import streamlit as st
from moduls import bco_gente, cbamecapacita, empleo
import requests

# Configuración de la página
st.set_page_config(page_title="Dashboard Integrado", layout="wide")

# Estilos básicos
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; text-align: center;}
    .tab-subheader {font-size: 1.8rem; font-weight: bold;}
    .stTabs [aria-selected="true"] {background-color: #4e8df5; color: white;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">Dashboard Integrado de Reportes</div>', unsafe_allow_html=True)

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
        'empleo': ['postulaciones_fup.parquet', 'inscripciones.parquet', 'inscriptos.parquet', 
                   'poblacion.parquet', 'empresas.parquet', 'capa_departamentos_2010.geojson']
    }

# Crear pestañas
tabs = st.tabs(["Banco de la Gente", "CBA ME CAPACITA", "Empleo +26"])

# Pestaña 1: Banco de la Gente
with tabs[0]:
    st.markdown('<div class="tab-subheader">Banco de la Gente</div>', unsafe_allow_html=True)
    # Pasar directamente all_data y all_dates al módulo
    bco_gente.show_bco_gente_dashboard(all_data, all_dates)

# Pestaña 2: CBA ME CAPACITA
with tabs[1]:
    st.markdown('<div class="tab-subheader">CBA ME CAPACITA</div>', unsafe_allow_html=True)
    # Pasar directamente all_data y all_dates al módulo
    cbamecapacita.show_cba_capacita_dashboard(all_data, all_dates)

# Pestaña 3: Empleo +26
with tabs[2]:
    st.markdown('<div class="tab-subheader">Empleo +26</div>', unsafe_allow_html=True)
    # Pasar directamente all_data y all_dates al módulo
    empleo.show_empleo_dashboard(all_data, all_dates)

