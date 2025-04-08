import streamlit as st
import pandas as pd
import plotly.express as px

def show_cba_capacita_dashboard(data, dates):
    """
    Muestra el dashboard de CBA ME CAPACITA.
    
    Args:
        data: Lista de dataframes cargados desde GitLab
        dates: Lista de fechas de actualización de los archivos
    """
    if data is None:
        st.error("No se pudieron cargar los datos de CBA ME CAPACITA.")
        return
    
    # Marcador de posición para la implementación real
    st.info("Dashboard de CBA ME CAPACITA en desarrollo.")
    
    # Mostrar información de actualización de datos
    if dates and any(dates):
        latest_date = max([d for d in dates if d is not None], default=None)
        if latest_date:
            st.caption(f"Última actualización de datos: {latest_date}")
    
    # Crear columnas para métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total de Alumnos", value="5,678", delta="8%")
    
    with col2:
        st.metric(label="Cursos Activos", value="42", delta="2")
    
    with col3:
        st.metric(label="Tasa de Finalización", value="65%", delta="3%")
    
    # Crear pestañas para diferentes vistas
    tab1, tab2 = st.tabs(["Alumnos", "Cursos"])
    
    with tab1:
        st.subheader("Análisis de Alumnos")
        # Gráfico de ejemplo
        chart_data = pd.DataFrame({
            "Localidad": ["Córdoba", "Villa María", "Río Cuarto", "Carlos Paz", "Otros"],
            "Alumnos": [2500, 1200, 800, 600, 578]
        })
        fig = px.bar(chart_data, x="Localidad", y="Alumnos", title="Alumnos por Localidad")
        st.plotly_chart(fig)
        
        # Distribución por edad
        age_data = pd.DataFrame({
            "Rango": ["18-25", "26-35", "36-45", "46-55", "56+"],
            "Cantidad": [1800, 2200, 1000, 500, 178]
        })
        fig = px.pie(age_data, values='Cantidad', names='Rango', title='Distribución por Edad')
        st.plotly_chart(fig)
    
    with tab2:
        st.subheader("Análisis de Cursos")
        # Gráfico de ejemplo
        course_data = pd.DataFrame({
            "Categoría": ["Tecnología", "Oficios", "Administración", "Idiomas", "Otros"],
            "Cursos": [15, 12, 8, 5, 2],
            "Alumnos": [2200, 1800, 1000, 500, 178]
        })
        fig = px.bar(course_data, x="Categoría", y=["Cursos", "Alumnos"], 
                    barmode="group", title="Cursos y Alumnos por Categoría")
        st.plotly_chart(fig)