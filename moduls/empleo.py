import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import math
import requests
import io
from datetime import datetime, timedelta

def enviar_a_slack(mensaje, valoracion):
    """
    Envía un mensaje a Slack con la valoración del usuario.
    
    Args:
        mensaje: El mensaje del usuario
        valoracion: La valoración del 1 al 5
    
    Returns:
        bool: True si el mensaje se envió correctamente, False en caso contrario
    """
    try:
        # URL del webhook de Slack (reemplazar con la URL real)
        webhook_url = "https://hooks.slack.com/services/your/webhook/url"
        
        # Crear el mensaje con formato
        estrellas = "⭐" * valoracion
        payload = {
            "text": f"*Nueva valoración del reporte:* {estrellas}\n*Comentario:* {mensaje}"
        }
        
        # Enviar la solicitud POST a Slack
        response = requests.post(webhook_url, json=payload)
        
        # Verificar si la solicitud fue exitosa
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error al enviar a Slack: {str(e)}")
        return False

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
    
    return 0

def show_empleo_dashboard(data, dates):
    """
    Muestra el dashboard de PROGRAMAS DE EMPLEO.
    
    Args:
        data: Diccionario de dataframes cargados desde GitLab
        dates: Diccionario de fechas de actualización de los archivos
    """
    # Apply custom styles for better appearance
    st.markdown("""
        <style>
        /* General styles */
        .main {
            background-color: #f8f9fa;
            padding: 1rem;
        }
        
        /* Header styles */
        .dashboard-header {
            background-color: #4e73df;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Tab styles */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-radius: 8px;
            background-color: #e9ecef;
            padding: 5px;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            border-radius: 8px;
            padding: 10px 16px;
            background-color: #e9ecef;
            font-weight: 500;
            color: #495057;
            transition: all 0.3s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: #4e73df !important;
            color: white !important;
            font-weight: 600;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Card styles */
        .metric-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 15px;
            transition: transform 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: #4e73df;
        }
        
        .metric-label {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 5px;
        }
        
        /* Section styles */
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #343a40;
            margin: 25px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid #4e73df;
        }
        
        /* Chart container */
        .chart-container {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Info box */
        .info-box {
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            background-color: #f8f9fa;
            margin: 10px 0;
            font-size: 0.9em;
            color: #505050;
        }
        
        /* Status indicators */
        .status-success {background-color: #d1e7dd; border-left: 5px solid #198754;}
        .status-info {background-color: #d0e3f1; border-left: 5px solid #0d6efd;}
        .status-warning {background-color: #fff3cd; border-left: 5px solid #ffc107;}
        .status-danger {background-color: #f8d7da; border-left: 5px solid #dc3545;}
        
        /* Table styles */
        .styled-table {
            border-collapse: collapse;
            width: 100%;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .styled-table thead tr {
            background-color: #4e73df;
            color: white;
            text-align: left;
        }
        
        .styled-table th,
        .styled-table td {
            padding: 12px 15px;
        }
        
        .styled-table tbody tr {
            border-bottom: 1px solid #dddddd;
        }
        
        .styled-table tbody tr:nth-of-type(even) {
            background-color: #f3f3f3;
        }
        
        .styled-table tbody tr:last-of-type {
            border-bottom: 2px solid #4e73df;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if not data:
        st.info("No se pudieron cargar los datos de PROGRAMAS DE EMPLEO.")
        return
    
    # Extraer los dataframes necesarios
    try:
        # Actualizar los nombres de los archivos para que coincidan con los disponibles
        df_inscriptos = data.get('VT_REPORTES_PPP_MAS26.parquet')
        df_poblacion = data.get('departamentos_poblacion.txt')
        df_empresas = data.get('vt_empresas_adheridas.parquet')
        geojson_data = data.get('capa_departamentos_2010.geojson')
        
        # Verificar silenciosamente los archivos disponibles
        has_inscriptos = df_inscriptos is not None and not df_inscriptos.empty
        has_empresas = df_empresas is not None and not df_empresas.empty
        has_geojson = geojson_data is not None
        has_poblacion = df_poblacion is not None and not df_poblacion.empty
        
    except Exception as e:
        st.info(f"Se mostrarán los datos disponibles: {str(e)}")
    
    # Header with improved styling
    st.markdown("""
        <div class="dashboard-header">
            <h1 style="margin:0; font-size:28px;">Dashboard de PROGRAMAS DE EMPLEO</h1>
            <p style="margin:5px 0 0 0; opacity:0.8;">Análisis de inscripciones y empresas adheridas</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Mostrar información de actualización de datos con mejor estilo
    if dates and any(dates.values()):
        latest_date = max([d for d in dates.values() if d is not None], default=None)
        if latest_date:
            st.markdown(f"""
                <div style="background-color:#e9ecef; padding:10px; border-radius:5px; margin-bottom:20px; font-size:0.9em;">
                    <i class="fas fa-sync-alt"></i> <strong>Última actualización:</strong> {latest_date}
                </div>
            """, unsafe_allow_html=True)
    else:
        latest_date = datetime.now()
    
    # Crear pestañas para diferentes vistas con mejor estilo
    tab1, tab2 = st.tabs(["📊 Inscripciones", "🏢 Empresas"])
    
    with tab1:
        if has_inscriptos:
            show_inscriptions(df_inscriptos, 
                             df_poblacion if has_poblacion else pd.DataFrame(), 
                             geojson_data, latest_date)
        else:
            st.markdown("""
                <div class="info-box status-warning">
                    <strong>Información:</strong> No hay datos suficientes para mostrar la vista de inscripciones.
                </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        if has_empresas:
            show_companies(df_empresas, geojson_data)
        else:
            st.markdown("""
                <div class="info-box status-warning">
                    <strong>Información:</strong> No hay datos de empresas disponibles.
                </div>
            """, unsafe_allow_html=True)

def show_companies(df_empresas, geojson_data):
    # Asegúrate de que las columnas numéricas sean del tipo correcto
    if 'CANTIDAD_EMPLEADOS' in df_empresas.columns:
        df_empresas['CANTIDAD_EMPLEADOS'] = pd.to_numeric(df_empresas['CANTIDAD_EMPLEADOS'], errors='coerce')
        df_empresas['CANTIDAD_EMPLEADOS'] = df_empresas['CANTIDAD_EMPLEADOS'].fillna(0)
    else:
        df_empresas['CANTIDAD_EMPLEADOS'] = 0
        
    if 'VACANTES' in df_empresas.columns:
        df_empresas['VACANTES'] = pd.to_numeric(df_empresas['VACANTES'], errors='coerce')
        df_empresas['VACANTES'] = df_empresas['VACANTES'].fillna(0)
    else:
        df_empresas['VACANTES'] = 0

    # Calcular la columna 'CUPO'
    if all(col in df_empresas.columns for col in ['CANTIDAD_EMPLEADOS', 'EMPLEADOR', 'ADHERIDO']):
        df_empresas['CUPO'] = df_empresas.apply(lambda row: calculate_cupo(row['CANTIDAD_EMPLEADOS'], row['EMPLEADOR'], row['ADHERIDO']), axis=1)
    else:
        df_empresas['CUPO'] = 0

    # Filtrar por CUIT único y eliminar duplicados
    columns_to_select = [col for col in ['N_LOCALIDAD', 'N_DEPARTAMENTO', 'CUIT', 'N_EMPRESA', 
                                       'NOMBRE_TIPO_EMPRESA', 'ADHERIDO', 'CANTIDAD_EMPLEADOS', 
                                       'VACANTES', 'CUPO', 'IMP_GANANCIAS', 'IMP_IVA', 'MONOTRIBUTO',
                                       'INTEGRANTE_SOC', 'EMPLEADOR', 'ACTIVIDAD_MONOTRIBUTO'] 
                       if col in df_empresas.columns]
    
    df_display = df_empresas[columns_to_select].drop_duplicates(subset='CUIT')
    df_display = df_display.sort_values(by='CUPO', ascending=False).reset_index(drop=True)

    # Filtrar empresas adheridas al PPP 2024
    if 'ADHERIDO' in df_empresas.columns:
        df_empresas_puestos = df_empresas[df_empresas['ADHERIDO'] == 'PPP - PROGRAMA PRIMER PASO [2024]'].copy()
    else:
        df_empresas_puestos = pd.DataFrame()
    
    # Improved section title
    st.markdown('<div class="section-title">Programa Primer Paso - PERFIL de la demanda por categorías</div>', unsafe_allow_html=True)
    
    # Resto del código de visualización con mejoras visuales
    if not df_empresas_puestos.empty and 'N_DEPARTAMENTO' in df_empresas_puestos.columns:
        with st.expander("Selecciona los departamentos (haz clic para expandir)"):
            departamentos_unicos = df_empresas_puestos['N_DEPARTAMENTO'].unique()
            departamentos_seleccionados = st.multiselect(
                label="Selecciona departamentos",
                options=departamentos_unicos,
                default=departamentos_unicos.tolist(),
                help='Mantén presionada la tecla Ctrl (o Cmd en Mac) para seleccionar múltiples opciones.',
                label_visibility="collapsed",
                key="departamentos_multiselect"  # Added unique key
            )

        df_empresas_puestos = df_empresas_puestos[df_empresas_puestos['N_DEPARTAMENTO'].isin(departamentos_seleccionados)]
        
        if all(col in df_empresas_puestos.columns for col in ['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA', 'CUIT']):
            df_puesto_agg = df_empresas_puestos.groupby(['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA']).agg({'CUIT': 'nunique'}).reset_index()
            top_10_categorias = df_puesto_agg.groupby('N_CATEGORIA_EMPLEO')['CUIT'].nunique().nlargest(10).index
            df_puesto_agg_top10 = df_puesto_agg[df_puesto_agg['N_CATEGORIA_EMPLEO'].isin(top_10_categorias)]

            st.markdown("""<div class="info-box">Este gráfico representa las empresas adheridas al programa PPP, que cargaron el PERFIL de su demanda, expresado en categorias.</div>""", unsafe_allow_html=True)
            
            # Improved chart with better colors and styling
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            stacked_bar_chart_2 = alt.Chart(df_puesto_agg_top10).mark_bar().encode(
                x=alt.X('CUIT:Q', title='Cantidad de Empleados'),
                y=alt.Y('N_CATEGORIA_EMPLEO:N', title='Categoría de Empleo', sort='-x'),
                color=alt.Color('NOMBRE_TIPO_EMPRESA:N', title='Tipo de Empresa', scale=alt.Scale(scheme='blues')),
                tooltip=['N_CATEGORIA_EMPLEO', 'NOMBRE_TIPO_EMPRESA', 'CUIT']
            ).properties(width=600, height=400)
            st.altair_chart(stacked_bar_chart_2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border: 1px solid #e0e0e0; margin: 20px 0;'>", unsafe_allow_html=True)

    # Métricas y tabla final con mejor diseño
    empresas_adh = df_display['CUIT'].nunique()
    
    st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Empresas Adheridas</div>
            <div class="metric-value">{:,}</div>
        </div>
    """.format(empresas_adh), unsafe_allow_html=True)

    st.markdown("""<div class="info-box">Las empresas en esta tabla se encuentran adheridas a uno o más programas de empleo, han cumplido con los requisitos establecidos y han proporcionado sus datos a través de los registros de programasempleo.cba.gov.ar</div>""", unsafe_allow_html=True)

    # Mostrar el DataFrame con mejor estilo
    st.dataframe(df_display, hide_index=True, use_container_width=True)

    st.markdown("<hr style='border: 1px solid #e0e0e0; margin: 20px 0;'>", unsafe_allow_html=True)

    # --- Nuevo apartado: Perfil de Demanda con mejor estilo ---
    st.markdown('<div class="section-title">Perfil de Demanda</div>', unsafe_allow_html=True)

    # Filtrar solo los datos que tengan información de puesto y categoría
    required_columns = ['N_EMPRESA', 'CUIT', 'N_PUESTO_EMPLEO', 'N_CATEGORIA_EMPLEO']
    if all(col in df_empresas.columns for col in required_columns):
        df_perfil_demanda = df_empresas.dropna(subset=required_columns)
    else:
        df_perfil_demanda = pd.DataFrame()

    if df_perfil_demanda.empty:
        st.markdown("""
            <div class="info-box status-info">
                <strong>Información:</strong> No hay datos disponibles de perfil de demanda.
            </div>
        """, unsafe_allow_html=True)
    else:
        # Crear las dos columnas
        col1, col2 = st.columns(2)

        # --- Visualización 1: Tabla Agrupada (en col1) con mejor estilo ---
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 style="font-size: 18px; margin-bottom: 15px;">Puestos y Categorías Demandadas por Empresa</h3>', unsafe_allow_html=True)
            # Agrupar por empresa, puesto y categoría, sin columna de cantidad
            df_grouped = df_perfil_demanda.groupby(['N_EMPRESA','CUIT','N_PUESTO_EMPLEO', 'N_CATEGORIA_EMPLEO']).size().reset_index()
            # Eliminar la columna "0" que se crea
            df_grouped = df_grouped.drop(columns=[0])
            st.dataframe(df_grouped, hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # --- Visualización 2: Gráfico de Barras por Categoría (Top 10) (en col2) con mejor estilo ---
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 style="font-size: 18px; margin-bottom: 15px;">Top 10 - Distribución de Categorías de Empleo</h3>', unsafe_allow_html=True)

            # Agrupar por categoría y contar las ocurrencias
            df_cat_count = df_perfil_demanda.groupby('N_CATEGORIA_EMPLEO')['CUIT'].nunique().reset_index(name='Empresas que Buscan')
            df_cat_count = df_cat_count.sort_values(by='Empresas que Buscan', ascending=False)

            if len(df_cat_count) > 9:
                #tomar el top 9
                df_cat_count_top_9 = df_cat_count.head(9).copy()

                # Agrupar el resto en "Otros"
                otros_count = df_cat_count.iloc[9:]['Empresas que Buscan'].sum()
                df_otros = pd.DataFrame([{'N_CATEGORIA_EMPLEO': 'Otros', 'Empresas que Buscan': otros_count}]) 

                # Concatenar el top 9 con "Otros"
                df_cat_count_final = pd.concat([df_cat_count_top_9, df_otros], ignore_index=True)
            else:
                df_cat_count_final = df_cat_count.copy()

            # Improved chart with better colors
            chart_cat = alt.Chart(df_cat_count_final).mark_bar(
                cornerRadiusTopRight=5,
                cornerRadiusBottomRight=5
            ).encode( 
                x=alt.X('Empresas que Buscan', title=''),  
                y=alt.Y('N_CATEGORIA_EMPLEO', sort='-x', title=''), 
                tooltip=['N_CATEGORIA_EMPLEO', 'Empresas que Buscan'],
                text=alt.Text('Empresas que Buscan', format=',d'),
                color=alt.value('#4e73df')  # Consistent color scheme
            ).properties(
                width=600,
                height=400
            )
            
            # Agregar las labels al gráfico
            text = alt.Chart(df_cat_count_final).mark_text(
                align='left',
                baseline='middle',
                dx=3,
                color='white'  # Better contrast for text
            ).encode(
                x=alt.X('Empresas que Buscan', title=''),  
                y=alt.Y('N_CATEGORIA_EMPLEO', sort='-x', title=''), 
                text='Empresas que Buscan'
            )

            # Primero combinar los gráficos con layer
            combined_chart = alt.layer(chart_cat, text)
            
            # Luego aplicar la configuración al gráfico combinado
            combined_chart = combined_chart.configure_axisY(labels=False, domain=False, ticks=False)
            
            # Mostrar el gráfico combinado
            st.altair_chart(combined_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

def show_inscriptions(df_inscriptos, df_poblacion, geojson_data, file_date):
    """
    Muestra la vista de inscripciones con mejor estilo visual
    
    Args:
        df_inscriptos: DataFrame de VT_REPORTES_PPP_MAS26.parquet
        df_poblacion: DataFrame de poblacion_departamentos.csv (puede ser None)
        geojson_data: Datos GeoJSON para mapas
        file_date: Fecha de actualización de los archivos
    """

    # Verificar que los DataFrames no estén vacíos
    if df_inscriptos is None:
        st.markdown("""
            <div class="info-box status-warning">
                <strong>Información:</strong> Uno o más DataFrames necesarios no están disponibles.
            </div>
        """, unsafe_allow_html=True)
        return
    
    try:
        # Limpiar CUIL
        if 'CUIL' in df_inscriptos.columns:
            df_inscriptos['CUIL'] = df_inscriptos['CUIL'].astype(str).str.replace("-", "", regex=False)
        
        # Definir mapeo de programas
        programas = {
            53: "Programa Primer Paso",
            51: "Más 26",
            54: "CBA Mejora",
            55: "Nueva Oportunidad"
        }
        
        # Filtrar para obtener solo los registros con IDETAPA válidas
        if 'IDETAPA' in df_inscriptos.columns:
            # Obtener las etapas disponibles en los datos
            etapas_disponibles = df_inscriptos['IDETAPA'].dropna().unique()
            etapas_validas = [etapa for etapa in etapas_disponibles if etapa in programas.keys()]
            
            if len(etapas_validas) == 0:
                st.warning("No se encontraron programas válidos en los datos.")
                return
                
            # Crear selector de programa con estilo mejorado
            st.markdown('<div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 20px;">', unsafe_allow_html=True)
            st.markdown('<h3 style="font-size: 18px; margin: 0 0 10px 0;">Seleccionar Programa</h3>', unsafe_allow_html=True)
            
            # Determinar el programa por defecto (usar el primero disponible)
            programa_default = etapas_validas[0] if etapas_validas else 53
            
            # Crear opciones para el selector
            opciones_programa = {programas.get(etapa, f"Programa {etapa}"): etapa for etapa in etapas_validas}
            
            # Selector de programa
            programa_seleccionado_nombre = st.selectbox(
                "Programa:",
                options=list(opciones_programa.keys()),
                index=0,
                label_visibility="collapsed"
            )
            
            # Obtener el ID de etapa seleccionado
            programa_seleccionado = opciones_programa[programa_seleccionado_nombre]
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Filtrar los datos según el programa seleccionado
            df_programa = df_inscriptos[df_inscriptos['IDETAPA'] == programa_seleccionado].copy()
        else:
            st.warning("No se encontró la columna IDETAPA en los datos.")
            return
            
        # Título dinámico según el programa seleccionado
        st.markdown(f'<h2 style="font-size: 24px; margin-bottom: 20px;">Dashboard de {programa_seleccionado_nombre}</h2>', unsafe_allow_html=True)
            
        # Filtrar los DataFrames según el programa seleccionado
        if not df_programa.empty and 'ID_EST_FIC' in df_programa.columns:
            df_match = df_programa[(df_programa['ID_EST_FIC'] == 8)]
            df_cti_inscripto = df_programa[(df_programa['ID_EST_FIC'] == 12) & (df_programa['ID_EMP'].notnull())]
            df_cti_validos = df_programa[df_programa['ID_EST_FIC'] == 13]
            df_cti_benficiario = df_programa[df_programa['ID_EST_FIC'] == 14]
        else:
            df_match = pd.DataFrame()
            df_cti_inscripto = pd.DataFrame()
            df_cti_validos = pd.DataFrame()
            df_cti_benficiario = pd.DataFrame()
        
        # REPORTE PPP con mejor estilo
        file_date_inscripciones = pd.to_datetime(file_date) if file_date else datetime.now()
        file_date_inscripciones = file_date_inscripciones - timedelta(hours=3)
        
        st.markdown(f"""
            <div style="background-color:#e9ecef; padding:10px; border-radius:5px; margin-bottom:20px; font-size:0.9em;">
                <i class="fas fa-sync-alt"></i> <strong>Última actualización:</strong> {file_date_inscripciones.strftime('%d/%m/%Y %H:%M')}
            </div>
        """, unsafe_allow_html=True)
        
        # Calcular métricas para el programa seleccionado
        if not df_match.empty:
            total_match = len(df_match)
        else:
            total_match = 0

        if not df_programa.empty and 'ID_EST_FIC' in df_programa.columns:
            conteo_estados = df_programa['ID_EST_FIC'].value_counts()
            total_empresa_no_apta = conteo_estados.get(2, 0)  
            total_benef = conteo_estados.get(14, 0)
            total_validos = conteo_estados.get(13, 0)
            total_inscriptos = conteo_estados.get(12, 0)
            total_pendientes = conteo_estados.get(3, 0)
            total_rechazados = conteo_estados.get(17, 0) + conteo_estados.get(18, 0) + conteo_estados.get(19, 0)
        else:
            total_empresa_no_apta = 0
            total_benef = 0
            total_validos = 0
            total_inscriptos = 0
            total_pendientes = 0
            total_rechazados = 0
        
        # Crear tarjetas de métricas con mejor estilo
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card status-info">
                     <div class="metric-label">Total Match {programa_seleccionado_nombre}</div>
                     <div class="metric-value">{total_match:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card status-info">
                    <div class="metric-label">Total Beneficiarios {programa_seleccionado_nombre}</div>
                    <div class="metric-value">{total_benef:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Resto del código de visualización con mejoras visuales
        # Aquí puedes añadir más visualizaciones según sea necesario
    
    except Exception as e:
        st.markdown(f"""
            <div class="info-box status-warning">
                <strong>Información:</strong> Se mostrarán los datos disponibles: {str(e)}
            </div>
        """, unsafe_allow_html=True)