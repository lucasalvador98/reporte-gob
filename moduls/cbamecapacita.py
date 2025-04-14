import streamlit as st
import pandas as pd
import plotly.express as px
from utils.ui_components import display_kpi_row

def show_cba_capacita_dashboard(data, dates):
    """
    Muestra el dashboard de CBA ME CAPACITA.
    
    Args:
        data: Lista de dataframes cargados desde GitLab
        dates: Lista de fechas de actualización de los archivos
    """
    try:
        if data is None:
            st.error("No se pudieron cargar los datos de CBA ME CAPACITA.")
            return
        
        # Marcador de posición para la implementación real
        st.info("Dashboard de CBA ME CAPACITA en desarrollo.")
        
        # Mostrar información de actualización de datos
        if dates and any(dates.values()):
            latest_date = max([d for d in dates.values() if d is not None], default=None)
            if latest_date:
                st.caption(f"Última actualización de datos: {latest_date}")
        
        # Crear columnas para métricas
        col1, col2, col3 = st.columns(3)
        
        # Usar la función auxiliar para mostrar KPIs
        kpi_data = [
            {
                "title": "Total de Alumnos",
                "value": "5,678",
                "color_class": "kpi-primary",
                "delta": "↑ 8%",
                "delta_color": "#d4f7d4"
            },
            {
                "title": "Cursos Activos",
                "value": "42",
                "color_class": "kpi-secondary",
                "delta": "↑ 2",
                "delta_color": "#d4f7d4"
            },
            {
                "title": "Tasa de Finalización",
                "value": "65%",
                "color_class": "kpi-accent-2",
                "delta": "↑ 3%",
                "delta_color": "#d4f7d4"
            }
        ]
        
        display_kpi_row(kpi_data)
        
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
            
            # Serie histórica de inscripciones (ejemplo)
            try:
                st.subheader("Evolución de Inscripciones")
                # Datos de ejemplo para la serie histórica
                dates = pd.date_range(start='1/1/2023', periods=12, freq='M')
                historical_data = pd.DataFrame({
                    "Fecha": dates,
                    "Inscripciones": [120, 150, 180, 210, 190, 220, 250, 280, 310, 290, 320, 350]
                })
                
                fig_historia = px.line(
                    historical_data, 
                    x='Fecha', 
                    y='Inscripciones', 
                    title='Evolución de Inscripciones por Mes',
                    labels={'Inscripciones': 'Cantidad de Inscripciones', 'Fecha': 'Mes'},
                    markers=True
                )
                
                # Personalizar el diseño del gráfico
                fig_historia.update_layout(
                    xaxis=dict(
                        title='Fecha',
                        titlefont_size=14,
                        tickfont_size=12,
                        gridcolor='lightgray'
                    ),
                    yaxis=dict(
                        title='Cantidad de Inscripciones',
                        titlefont_size=14,
                        tickfont_size=12,
                        gridcolor='lightgray'
                    ),
                    plot_bgcolor='white'
                )
                
                st.plotly_chart(fig_historia)
            except Exception as e:
                st.warning(f"Error al generar la serie histórica de inscripciones: {str(e)}")
    except Exception as e:
        st.error(f"Error al mostrar el dashboard de CBA ME CAPACITA: {str(e)}")