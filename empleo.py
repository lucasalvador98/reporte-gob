import streamlit as st
import pandas as pd
import altair as alt
import math
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import io
import plotly.express as px
import pydeck as pdk
import requests
from datetime import datetime, timedelta

def calculate_cupo(cantidad_empleados, empleador, adherido):
    # Condición para el programa PPP
    if adherido == "PPP - PROGRAMA PRIMER PASO [2024]":
        if cantidad_empleados < 1:
            return 0
        elif cantidad_empleados <= 5:
            return 1
        elif cantidad_empleados <= 10:
            return 2
        elif cantidad_empleados <= 25:
            return 3
        elif cantidad_empleados <= 50:
            return math.ceil(0.2 * cantidad_empleados)
        else:
            return math.ceil(0.1 * cantidad_empleados)

    # Condición para el programa EMPLEO +26
    elif adherido == "EMPLEO +26":
        if empleador == 'N':
            return 1
        if cantidad_empleados < 1:
            return 1
        elif cantidad_empleados <= 7:
            return 2
        elif cantidad_empleados <= 30:
            return math.ceil(0.2 * cantidad_empleados)
        elif cantidad_empleados <= 165:
            return math.ceil(0.15 * cantidad_empleados)
        else:
            return math.ceil(0.1 * cantidad_empleados)

def show_companies(df_empresas, geojson_data):
    # Asegúrate de que las columnas numéricas sean del tipo correcto
    df_empresas['CANTIDAD_EMPLEADOS'] = pd.to_numeric(df_empresas['CANTIDAD_EMPLEADOS'], errors='coerce')
    df_empresas['CANTIDAD_EMPLEADOS'] = df_empresas['CANTIDAD_EMPLEADOS'].fillna(0)
    df_empresas['VACANTES'] = pd.to_numeric(df_empresas['VACANTES'], errors='coerce')
    df_empresas['VACANTES'] = df_empresas['VACANTES'].fillna(0)

    # Calcular la columna 'CUPO'
    df_empresas['CUPO'] = df_empresas.apply(lambda row: calculate_cupo(row['CANTIDAD_EMPLEADOS'], row['EMPLEADOR'], row['ADHERIDO']), axis=1)

    # Filtrar por CUIT único y eliminar duplicados
    df_display = df_empresas[['N_LOCALIDAD','N_DEPARTAMENTO', 'CUIT', 'N_EMPRESA', 'NOMBRE_TIPO_EMPRESA','ADHERIDO','CANTIDAD_EMPLEADOS', 'VACANTES', 'CUPO','IMP_GANANCIAS','IMP_IVA','MONOTRIBUTO','INTEGRANTE_SOC','EMPLEADOR','ACTIVIDAD_MONOTRIBUTO']].drop_duplicates(subset='CUIT')
    df_display = df_display.sort_values(by='CUPO', ascending=False).reset_index(drop=True)

    # Filtrar empresas adheridas al PPP 2024
    df_empresas_puestos = df_empresas[df_empresas['ADHERIDO'] == 'PPP - PROGRAMA PRIMER PASO [2024]'].copy()

    # Resto del código de visualización
    if not df_empresas_puestos.empty:
        st.markdown("### Programa Primer Paso - PERFIL de la demanda por categorías")

        with st.expander("Selecciona los departamentos (haz clic para expandir)"):
            departamentos_unicos = df_empresas_puestos['N_DEPARTAMENTO'].unique()
            departamentos_seleccionados = st.multiselect(
                label="Selecciona departamentos",
                options=departamentos_unicos,
                default=departamentos_unicos.tolist(),
                help='Mantén presionada la tecla Ctrl (o Cmd en Mac) para seleccionar múltiples opciones.',
                label_visibility="collapsed"
            )

        df_empresas_puestos = df_empresas_puestos[df_empresas_puestos['N_DEPARTAMENTO'].isin(departamentos_seleccionados)]
        
        df_puesto_agg = df_empresas_puestos.groupby(['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA']).agg({'CUIT': 'nunique'}).reset_index()
        top_10_categorias = df_puesto_agg.groupby('N_CATEGORIA_EMPLEO')['CUIT'].nunique().nlargest(10).index
        df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_CATEGORIA_EMPLEO'].isin(top_10_categorias)]

        st.markdown("""<div style='padding: 15px; border-radius: 5px; border: 1px solid #e0e0e0; background-color: #f8f9fa;margin-top: 10px; font-size: 0.9em;color: #505050;'>Este gráfico representa las empresas adheridas al programa PPP, que cargaron el PERFIL de su demanda, expresado en categorias.</div>""", unsafe_allow_html=True)
        
        stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
            x=alt.X('CUIT:Q', title='Cantidad de Empleados'),
            y=alt.Y('N_CATEGORIA_EMPLEO:N', title='Categoría de Empleo', sort='-x'),
            color=alt.Color('NOMBRE_TIPO_EMPRESA:N', title='Tipo de Empresa'),
            tooltip=['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA', 'CUIT']
        ).properties(width=600, height=400)

        st.altair_chart(stacked_bar_chart_2, use_container_width=True)

    # Mostrar estadísticas generales
    st.markdown("### Estadísticas Generales de Empresas")
    
    # Crear columnas para métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_empresas = df_empresas['CUIT'].nunique()
        st.metric(label="Total de Empresas", value=f"{total_empresas:,}")
    
    with col2:
        total_vacantes = df_empresas['VACANTES'].sum()
        st.metric(label="Total de Vacantes", value=f"{total_vacantes:,}")
    
    with col3:
        total_cupo = df_empresas['CUPO'].sum()
        st.metric(label="Cupo Total", value=f"{total_cupo:,}")
    
    # Gráfico de distribución por tipo de empresa
    st.markdown("### Distribución por Tipo de Empresa")
    
    df_tipo_empresa = df_display.groupby('NOMBRE_TIPO_EMPRESA').size().reset_index(name='Cantidad')
    df_tipo_empresa = df_tipo_empresa.sort_values('Cantidad', ascending=False)
    
    fig_tipo_empresa = px.pie(
        df_tipo_empresa, 
        values='Cantidad', 
        names='NOMBRE_TIPO_EMPRESA',
        title='Distribución por Tipo de Empresa',
        hole=0.4
    )
    st.plotly_chart(fig_tipo_empresa, use_container_width=True)
    
    # Gráfico de distribución por departamento
    st.markdown("### Distribución por Departamento")
    
    df_departamento = df_display.groupby('N_DEPARTAMENTO').size().reset_index(name='Cantidad')
    df_departamento = df_departamento.sort_values('Cantidad', ascending=False).head(10)
    
    fig_departamento = px.bar(
        df_departamento,
        x='N_DEPARTAMENTO',
        y='Cantidad',
        title='Top 10 Departamentos por Cantidad de Empresas',
        color='Cantidad',
        color_continuous_scale='Blues'
    )
    st.plotly_chart(fig_departamento, use_container_width=True)
    
    # Tabla de empresas
    st.markdown("### Tabla de Empresas")
    
    # Opciones de filtrado
    with st.expander("Opciones de Filtrado"):
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            selected_tipo = st.multiselect(
                "Tipo de Empresa",
                options=df_display['NOMBRE_TIPO_EMPRESA'].unique(),
                default=[]
            )
        
        with col_filter2:
            selected_departamento = st.multiselect(
                "Departamento",
                options=df_display['N_DEPARTAMENTO'].unique(),
                default=[]
            )
    
    # Aplicar filtros
    df_filtered = df_display.copy()
    
    if selected_tipo:
        df_filtered = df_filtered[df_filtered['NOMBRE_TIPO_EMPRESA'].isin(selected_tipo)]
    
    if selected_departamento:
        df_filtered = df_filtered[df_filtered['N_DEPARTAMENTO'].isin(selected_departamento)]
    
    # Mostrar tabla filtrada
    st.dataframe(
        df_filtered[['N_EMPRESA', 'CUIT', 'N_LOCALIDAD', 'N_DEPARTAMENTO', 'NOMBRE_TIPO_EMPRESA', 'CANTIDAD_EMPLEADOS', 'CUPO', 'VACANTES']],
        use_container_width=True
    )

def show_responses(df_respuestas, file_date_respuestas):
    columnas_relevantes = ["APRENDER", "DECISIONES", "INFORMACION", "EXPLICAR", "HERRAMIENTAS", "CALCULO", "INSTRUCCIONES"]

    if all(col in df_respuestas.columns for col in columnas_relevantes) and 'ID_INSCRIPCION' in df_respuestas.columns:
        df_respuestas = df_respuestas[columnas_relevantes + ["ID_INSCRIPCION"]]

        df_promedios = df_respuestas.groupby("ID_INSCRIPCION").mean().reset_index()
        df_promedios_melted = df_promedios.drop("ID_INSCRIPCION", axis=1).mean().reset_index()
        df_promedios_melted.columns = ['Aspecto', 'Promedio']
        df_promedios_melted['Promedio'] = df_promedios_melted['Promedio'].round(2)

        # Filtro por categoría si se desea (requiere una columna 'CATEGORIA' en df_respuestas)
        categorias = df_respuestas['CATEGORIA'].unique() if 'CATEGORIA' in df_respuestas.columns else []
        selected_categoria = st.selectbox("Seleccionar Categoría", categorias) if categorias else None
        
        if selected_categoria:
            df_respuestas = df_respuestas[df_respuestas['CATEGORIA'] == selected_categoria]
            
        st.subheader("Promedio por Aspecto")
        bar_chart_aspectos = alt.Chart(df_promedios_melted).mark_bar().encode(
            y=alt.Y('Aspecto:N', title='Aspecto', sort='-x'),
            x=alt.X('Promedio:Q', title='Promedio'),
            color=alt.Color('Aspecto:N', legend=None),  # Usa el esquema de color por defecto
            tooltip=['Aspecto:N', 'Promedio:Q']
        ).properties(width=800, height=400)

        text = bar_chart_aspectos.mark_text(align='left', baseline='middle', dx=3).encode(
            text=alt.Text('Promedio:Q', format='.2f')
        )
        final_chart = bar_chart_aspectos + text

        st.altair_chart(final_chart, use_container_width=True)

        st.subheader("Promedios de Aspectos")
        st.dataframe(df_promedios_melted, hide_index=True)
    else:
        st.error("Faltan columnas necesarias en el DataFrame. Verifica el archivo CSV.")

def show_inscriptions(df_postulaciones_fup, df_inscripciones, df_inscriptos, df_poblacion, geojson_data, file_date):
    # Verificar que los DataFrames no estén vacíos
    if df_postulaciones_fup is None or df_inscripciones is None or df_inscriptos is None or df_poblacion is None:
        st.warning("Uno o más DataFrames están vacíos. Se mostrarán datos de ejemplo.")
        show_example_data()
        return
    
    if df_postulaciones_fup.empty or df_inscripciones.empty or df_inscriptos.empty or df_poblacion.empty:
        st.warning("Uno o más DataFrames están vacíos. Se mostrarán datos de ejemplo.")
        show_example_data()
        return
    
    try:
        df_inscriptos['CUIL'] = df_inscriptos['CUIL'].str.replace("-", "", regex=False)
        # Filtrar los DataFrames según sea necesario
        df_inscriptos_ppp = df_inscriptos[df_inscriptos['IDETAPA'] == 53]    
        df_match_ppp = df_inscriptos_ppp[(df_inscriptos_ppp['ID_EST_FIC'] == 8)]
        df_cti_inscripto_ppp = df_inscriptos_ppp[(df_inscriptos_ppp['ID_EST_FIC'] == 12) & (df_inscriptos_ppp['ID_EMP'].notnull())]
        
        # Crear columnas para métricas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_inscriptos = len(df_inscriptos_ppp)
            st.metric(label="Total Inscriptos", value=f"{total_inscriptos:,}")
        
        with col2:
            total_match = len(df_match_ppp)
            st.metric(label="Match", value=f"{total_match:,}")
        
        with col3:
            total_cti = len(df_cti_inscripto_ppp)
            st.metric(label="CTI", value=f"{total_cti:,}")
        
        with col4:
            porcentaje_match = (total_match / total_inscriptos * 100) if total_inscriptos > 0 else 0
            st.metric(label="% Match", value=f"{porcentaje_match:.2f}%")
        
        # Gráfico de evolución temporal
        st.markdown("### Evolución de Inscripciones")
        
        # Convertir a datetime y agrupar por fecha
        df_inscriptos_ppp['FECHA_INSCRIPCION'] = pd.to_datetime(df_inscriptos_ppp['FECHA_INSCRIPCION'], errors='coerce')
        df_inscriptos_ppp = df_inscriptos_ppp.dropna(subset=['FECHA_INSCRIPCION'])
        
        df_evolucion = df_inscriptos_ppp.groupby(df_inscriptos_ppp['FECHA_INSCRIPCION'].dt.date).size().reset_index(name='Cantidad')
        df_evolucion['FECHA_INSCRIPCION'] = pd.to_datetime(df_evolucion['FECHA_INSCRIPCION'])
        df_evolucion = df_evolucion.sort_values('FECHA_INSCRIPCION')
        
        # Calcular acumulado
        df_evolucion['Acumulado'] = df_evolucion['Cantidad'].cumsum()
        
        # Gráfico de línea con Plotly
        fig_evolucion = px.line(
            df_evolucion, 
            x='FECHA_INSCRIPCION', 
            y=['Cantidad', 'Acumulado'],
            title='Evolución de Inscripciones',
            labels={'value': 'Cantidad', 'FECHA_INSCRIPCION': 'Fecha', 'variable': 'Tipo'},
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        st.plotly_chart(fig_evolucion, use_container_width=True)
        
        # Distribución por género
        st.markdown("### Distribución por Género")
        
        if 'SEXO' in df_inscriptos_ppp.columns:
            df_genero = df_inscriptos_ppp.groupby('SEXO').size().reset_index(name='Cantidad')
            
            fig_genero = px.pie(
                df_genero, 
                values='Cantidad', 
                names='SEXO',
                title='Distribución por Género',
                hole=0.4
            )
            st.plotly_chart(fig_genero, use_container_width=True)
        
        # Distribución por departamento
        st.markdown("### Distribución por Departamento")
        
        if 'N_DEPARTAMENTO' in df_inscriptos_ppp.columns:
            df_departamento = df_inscriptos_ppp.groupby('N_DEPARTAMENTO').size().reset_index(name='Cantidad')
            df_departamento = df_departamento.sort_values('Cantidad', ascending=False).head(10)
            
            fig_departamento = px.bar(
                df_departamento,
                x='N_DEPARTAMENTO',
                y='Cantidad',
                title='Top 10 Departamentos por Cantidad de Inscriptos',
                color='Cantidad',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_departamento, use_container_width=True)
        
        # Distribución por edad
        st.markdown("### Distribución por Edad")
        
        if 'EDAD' in df_inscriptos_ppp.columns:
            # Convertir a numérico y eliminar valores inválidos
            df_inscriptos_ppp['EDAD'] = pd.to_numeric(df_inscriptos_ppp['EDAD'], errors='coerce')
            df_inscriptos_ppp = df_inscriptos_ppp.dropna(subset=['EDAD'])
            
            # Crear rangos de edad
            bins = [25, 30, 35, 40, 45, 50, 55, 60, 65]
            labels = ['26-30', '31-35', '36-40', '41-45', '46-50', '51-55', '56-60', '61-65']
            df_inscriptos_ppp['RANGO_EDAD'] = pd.cut(df_inscriptos_ppp['EDAD'], bins=bins, labels=labels, right=False)
            
            df_edad = df_inscriptos_ppp.groupby('RANGO_EDAD').size().reset_index(name='Cantidad')
            
            fig_edad = px.bar(
                df_edad,
                x='RANGO_EDAD',
                y='Cantidad',
                title='Distribución por Rango de Edad',
                color='Cantidad',
                color_continuous_scale='Viridis'
            )
            st.plotly_chart(fig_edad, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error al procesar los datos: {str(e)}")
        show_example_data()

def show_example_data():
    """Muestra datos de ejemplo cuando no hay datos reales disponibles"""
    # Crear columnas para métricas de ejemplo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Total Inscriptos", value="3,500")
    
    with col2:
        st.metric(label="Match", value="1,200")
    
    with col3:
        st.metric(label="CTI", value="800")
    
    with col4:
        st.metric(label="% Match", value="34.29%")
    
    # Gráfico de evolución temporal de ejemplo
    st.markdown("### Evolución de Inscripciones (Ejemplo)")
    
    # Crear datos de ejemplo
    fechas = pd.date_range(start='2023-01-01', periods=30, freq='D')
    cantidades = [10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120, 125, 130, 135, 140, 145, 150, 155]
    acumulado = [sum(cantidades[:i+1]) for i in range(len(cantidades))]
    
    df_ejemplo = pd.DataFrame({
        'Fecha': fechas,
        'Cantidad': cantidades,
        'Acumulado': acumulado
    })
    
    fig_ejemplo = px.line(
        df_ejemplo, 
        x='Fecha', 
        y=['Cantidad', 'Acumulado'],
        title='Evolución de Inscripciones (Ejemplo)',
        labels={'value': 'Cantidad', 'Fecha': 'Fecha', 'variable': 'Tipo'},
        color_discrete_sequence=['#1f77b4', '#ff7f0e']
    )
    st.plotly_chart(fig_ejemplo, use_container_width=True)
    
    # Distribución por género de ejemplo
    st.markdown("### Distribución por Género (Ejemplo)")
    
    df_genero_ejemplo = pd.DataFrame({
        'Género': ['Masculino', 'Femenino', 'No Binario'],
        'Cantidad': [1800, 1650, 50]
    })
    
    fig_genero_ejemplo = px.pie(
        df_genero_ejemplo, 
        values='Cantidad', 
        names='Género',
        title='Distribución por Género (Ejemplo)',
        hole=0.4
    )
    st.plotly_chart(fig_genero_ejemplo, use_container_width=True)
    
    # Distribución por departamento de ejemplo
    st.markdown("### Distribución por Departamento (Ejemplo)")
    
    df_departamento_ejemplo = pd.DataFrame({
        'Departamento': ['Capital', 'Río Cuarto', 'Punilla', 'Colón', 'San Justo', 'General San Martín', 'Río Segundo', 'Tercero Arriba', 'Unión', 'Juárez Celman'],
        'Cantidad': [1200, 450, 350, 300, 250, 200, 180, 170, 150, 120]
    })
    
    fig_departamento_ejemplo = px.bar(
        df_departamento_ejemplo,
        x='Departamento',
        y='Cantidad',
        title='Top 10 Departamentos por Cantidad de Inscriptos (Ejemplo)',
        color='Cantidad',
        color_continuous_scale='Viridis'
    )
    st.plotly_chart(fig_departamento_ejemplo, use_container_width=True)

def enviar_a_slack(comentario, valoracion):
    """
    Envía el feedback a Slack usando un webhook.
    """
    try:
        SLACK_WEBHOOK_URL = st.secrets["slack"]["webhook_url"]
        mensaje = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Nuevo Feedback del Dashboard",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Comentario:*\n{comentario}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Valoración:*\n{'⭐' * valoracion}"
                        }
                    ]
                }
            ]
        }
        response = requests.post(SLACK_WEBHOOK_URL, json=mensaje)
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al enviar a Slack: {str(e)}")
        return False

def show_empleo_dashboard(data_dict, dates):
    """
    Muestra el dashboard de Empleo +26.
    
    Args:
        data_dict: Diccionario de dataframes cargados desde GitLab
        dates: Diccionario de fechas de actualización de los archivos
    """
    st.header("Empleo +26")
    
    # Verificar si tenemos los archivos necesarios
    required_files = ['vt_inscripciones_empleo.parquet', 'vt_empresas_ARCA.parquet', 'VT_PUESTOS_X_FICHAS.parquet']
    missing_files = [file for file in required_files if file not in data_dict]
    
    if missing_files:
        st.warning(f"Faltan los siguientes archivos: {', '.join(missing_files)}")
        st.info("Se mostrarán datos de ejemplo.")
    
    # Obtener los dataframes específicos
    df_postulaciones_fup = data_dict.get('vt_postulaciones_fup.parquet')
    df_inscripciones = data_dict.get('vt_inscripciones_empleo.parquet')
    df_inscriptos = data_dict.get('vt_inscriptos.parquet')
    df_poblacion = data_dict.get('vt_poblacion.parquet')
    df_empresas = data_dict.get('vt_empresas_ARCA.parquet')
    geojson_data = data_dict.get('capa_departamentos_2010.geojson')
    
    # Mostrar información de actualización de datos
    if dates:
        latest_date = max([d for d in dates.values() if d is not None], default=None)
        if latest_date:
            st.caption(f"Última actualización de datos: {latest_date}")
    
    # Crear pestañas para diferentes vistas
    tab1, tab2 = st.tabs(["Inscripciones", "Empresas"])
    
    with tab1:
        show_inscriptions(df_postulaciones_fup, df_inscripciones, df_inscriptos, df_poblacion, geojson_data, dates.get('vt_inscripciones_empleo.parquet'))
    
    with tab2:
        show_companies(df_empresas, geojson_data)