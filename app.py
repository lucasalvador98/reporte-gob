# Importar directamente la función en lugar de importar el módulo
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
repo_id = "42788385"  # ID numérico del repositorio
branch = "main"

# Obtener token desde secrets
try:
    token = st.secrets["gitlab"]["token"]
except Exception as e:
    st.error(f"Error al obtener token: {str(e)}")
    st.stop()

# Cargar datos - Usar la función importada directamente
with st.spinner("Cargando datos de GitLab..."):
    all_data, all_dates = load_data_from_gitlab(repo_id, branch, token)
    
    # Resto del código permanece igual
    
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
                      'Detalle_recupero.csv', 'capa_departamentos_2010.geojson', 'departamentos_poblacion.csv'],
        'cba_capacita': ['VT_ALUMNOS_X_LOCALIDAD.parquet', 'VT_CURSOS_X_LOCALIDAD.parquet'],
        'empleo': ['vt_postulaciones_fup.parquet', 'vt_inscripciones_empleo.parquet', 'vt_inscriptos.parquet', 
                   'vt_poblacion.parquet', 'vt_empresas_ARCA.parquet', 'capa_departamentos_2010.geojson']
    }
    
    # Organizar datos por módulo
    data_dict = {}
    for module, files in modules.items():
        data_dict[module] = {}
        for file in files:
            data_dict[module][file] = all_data.get(file)
            if file not in all_data:
                st.warning(f"Archivo no encontrado: {file}")

# Mostrar archivos cargados
st.success(f"Se cargaron {len(all_data)} archivos")
with st.expander("Ver archivos cargados"):
    for file in all_data.keys():
        st.write(f"✅ {file}")

# Crear pestañas
tabs = st.tabs(["Banco de la Gente", "CBA ME CAPACITA", "Empleo +26"])

# Pestaña 1: Banco de la Gente
with tabs[0]:
    st.markdown('<div class="tab-subheader">Banco de la Gente</div>', unsafe_allow_html=True)
    if all(v is not None for v in data_dict['bco_gente'].values()):
        bco_gente.show_bco_gente_dashboard(data_dict['bco_gente'], all_dates)
    else:
        missing = [k for k, v in data_dict['bco_gente'].items() if v is None]
        st.error(f"Faltan archivos: {', '.join(missing)}")

# Pestaña 2: CBA ME CAPACITA
with tabs[1]:
    st.markdown('<div class="tab-subheader">CBA ME CAPACITA</div>', unsafe_allow_html=True)
    if all(v is not None for v in data_dict['cba_capacita'].values()):
        cbamecapacita.show_cba_capacita_dashboard(data_dict['cba_capacita'], all_dates)
    else:
        missing = [k for k, v in data_dict['cba_capacita'].items() if v is None]
        st.error(f"Faltan archivos: {', '.join(missing)}")

# Pestaña 3: Empleo +26
with tabs[2]:
    st.markdown('<div class="tab-subheader">Empleo +26</div>', unsafe_allow_html=True)
    if all(v is not None for v in data_dict['empleo'].values()):
        empleo.show_empleo_dashboard(data_dict['empleo'], all_dates)
    else:
        missing = [k for k, v in data_dict['empleo'].items() if v is None]
        st.error(f"Faltan archivos: {', '.join(missing)}")

# Sección de feedback
st.divider()
with st.expander("Enviar Feedback"):
    feedback = st.text_area("Comentarios:", height=100)
    rating = st.slider("Valoración:", 1, 5, 3)
    
    if st.button("Enviar"):
        if feedback:
            try:
                webhook_url = st.secrets["slack"]["webhook_url"]
                mensaje = {
                    "blocks": [
                        {"type": "header", "text": {"type": "plain_text", "text": "📊 Nuevo Feedback", "emoji": True}},
                        {"type": "section", "fields": [
                            {"type": "mrkdwn", "text": f"*Comentario:*\n{feedback}"},
                            {"type": "mrkdwn", "text": f"*Valoración:*\n{'⭐' * rating}"}
                        ]}
                    ]
                }
                response = requests.post(webhook_url, json=mensaje)
                if response.status_code == 200:
                    st.success("¡Gracias por tu feedback!")
                else:
                    st.error("Error al enviar feedback")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Por favor, escribe un comentario")