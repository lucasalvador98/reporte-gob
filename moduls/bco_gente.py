import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def show_bco_gente_dashboard(data, dates):
    """
    Muestra el dashboard de Banco de la Gente.
    
    Args:
        data: Lista de dataframes cargados desde GitLab
        dates: Lista de fechas de actualización de los archivos
    """
    if data is None:
        st.error("No se pudieron cargar los datos de Banco de la Gente.")
        return
    
    # Marcador de posición para la implementación real
    st.info("Dashboard de Banco de la Gente en desarrollo.")
    
    # Mostrar información de actualización de datos
    if dates and any(dates):
        latest_date = max([d for d in dates if d is not None], default=None)
        if latest_date:
            st.caption(f"Última actualización de datos: {latest_date}")
    
    # Crear columnas para métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total de Préstamos", value="1,234", delta="12%")
    
    with col2:
        st.metric(label="Monto Total", value="$12.5M", delta="-2%")
    
    with col3:
        st.metric(label="Tasa de Recupero", value="78%", delta="5%")
    
    # Crear pestañas para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["Global", "Recupero", "Rechazos"])
    
    with tab1:
        st.subheader("Vista Global")
        # Gráfico de ejemplo
        chart_data = pd.DataFrame({
            "Mes": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
            "Préstamos": [10, 20, 15, 25, 30, 35]
        })
        st.bar_chart(chart_data, x="Mes", y="Préstamos")
    
    with tab2:
        st.subheader("Análisis de Recupero")
        # Gráfico de ejemplo
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=["Ene", "Feb", "Mar", "Abr", "May", "Jun"], 
                                y=[75, 76, 78, 77, 80, 82], 
                                mode='lines+markers',
                                name='Tasa de Recupero'))
        st.plotly_chart(fig)
    
    with tab3:
        st.subheader("Gestión de Rechazos")
        # Gráfico de ejemplo
        rejection_data = pd.DataFrame({
            "Motivo": ["Documentación", "Ingresos", "Historial", "Otros"],
            "Cantidad": [45, 30, 15, 10]
        })
        fig = px.pie(rejection_data, values='Cantidad', names='Motivo', title='Motivos de Rechazo')
        st.plotly_chart(fig)