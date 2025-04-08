import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_empleo_dashboard(data, dates):
    """
    Muestra el dashboard de Empleo +26.
    
    Args:
        data: Lista de dataframes cargados desde GitLab
        dates: Lista de fechas de actualización de los archivos
    """
    if data is None:
        st.error("No se pudieron cargar los datos de Empleo +26.")
        return
    
    # Marcador de posición para la implementación real
    st.info("Dashboard de Empleo +26 en desarrollo.")
    
    # Mostrar información de actualización de datos
    if dates and any(dates):
        latest_date = max([d for d in dates if d is not None], default=None)
        if latest_date:
            st.caption(f"Última actualización de datos: {latest_date}")
    
    # Crear columnas para métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total de Inscripciones", value="3,456", delta="15%")
    
    with col2:
        st.metric(label="Empresas Participantes", value="128", delta="5")
    
    with col3:
        st.metric(label="Tasa de Colocación", value="42%", delta="7%")
    
    # Crear pestañas para diferentes vistas
    tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])
    
    with tab1:
        st.subheader("Análisis de Inscripciones")
        # Gráfico de ejemplo para inscripciones a lo largo del tiempo
        time_data = pd.DataFrame({
            "Mes": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
            "Inscripciones": [300, 450, 400, 600, 800, 906]
        })
        fig = px.line(time_data, x="Mes", y="Inscripciones", 
                     title="Evolución de Inscripciones", markers=True)
        st.plotly_chart(fig)
        
        # Gráfico de ejemplo para inscripciones por localidad
        location_data = pd.DataFrame({
            "Localidad": ["Córdoba", "Villa María", "Río Cuarto", "Carlos Paz", "Otros"],
            "Inscripciones": [1800, 700, 500, 300, 156]
        })
        fig = px.bar(location_data, x="Localidad", y="Inscripciones", 
                    title="Inscripciones por Localidad")
        st.plotly_chart(fig)
    
    with tab2:
        st.subheader("Análisis de Empresas")
        # Gráfico de ejemplo para empresas por sector
        sector_data = pd.DataFrame({
            "Sector": ["Tecnología", "Servicios", "Industria", "Comercio", "Otros"],
            "Empresas": [40, 35, 25, 20, 8]
        })
        fig = px.pie(sector_data, values='Empresas', names='Sector', 
                    title='Empresas por Sector')
        st.plotly_chart(fig)
        
        # Gráfico de ejemplo para puestos de trabajo ofrecidos
        position_data = pd.DataFrame({
            "Puesto": ["Administrativo", "Técnico", "Ventas", "Atención", "Otros"],
            "Vacantes": [80, 65, 50, 40, 25]
        })
        fig = px.bar(position_data, x="Puesto", y="Vacantes", 
                    title="Vacantes por Tipo de Puesto")
        st.plotly_chart(fig)