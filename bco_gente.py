import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
from datetime import datetime
import requests

def mostrar_feedback(comentario, valoracion):
    if not comentario or valoracion < 1 or valoracion > 5:
        st.error("Por favor, ingrese un comentario válido y una valoración entre 1 y 5 estrellas.")
        return False
    
    slack_webhook_url = st.secrets["slack"]["webhook_url"]
    
    mensaje = {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📝 Nuevo Comentario Recibido"}
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Comentario:*\n{comentario}"},
                    {"type": "mrkdwn", "text": f"*Valoración:*\n{'⭐' * valoracion}"}
                ]
            }
        ]
    }

    with st.spinner("Enviando feedback..."):
        try:
            response = requests.post(slack_webhook_url, json=mensaje)
            if response.status_code == 200:
                st.success("Comentario enviado exitosamente a Slack.")
                return True
            else:
                st.error(f"Error al enviar el mensaje. Código de estado: {response.status_code}.")
                return False
        except requests.exceptions.RequestException as e:
            st.error(f"Error al enviar a Slack: {str(e)}")
            return False



def mostrar_rechazados(df_global, geojson_data, df_departamentos):
    # Convertir la columna a tipo datetime y filtrar NaT
    if 'FECHA_INGRESO' in df_global.columns:
        df_global['FECHA_INGRESO'] = pd.to_datetime(df_global['FECHA_INGRESO'], errors='coerce')
        df_global = df_global.dropna(subset=['FECHA_INGRESO'])

    # Revisar si hay datos después de limpiar
    if df_global.empty:
        st.warning("No hay datos disponibles después de filtrar por fecha.")
        return

    # Definir las categorías de rechazo y sus ID
    categoria_rechazo = {
        "Rechazo": [4, 33, 18, 14, 17, 20, 30, 31, 32, 35, 13, 28, 29, 36, 22],
        "Desistido": [6],
    }

    # Contar rechazos por categoría
    conteo_rechazos = {categoria: df_global[df_global['ID_ESTADO_FORMULARIO'].isin(ids)].shape[0]
                       for categoria, ids in categoria_rechazo.items()}

    # Diseño de columnas y cuadros
    col1, col2, col3 = st.columns(3)
    cuadro_estilo = """
        <div style="margin: 10px; padding: 15px; border-radius: 8px; background-color: {bg_color}; color: {text_color};
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); font-family: Arial, sans-serif;">
            <h3 style="text-align: center; font-size: 18px;">{titulo}</h3>
            <p style="text-align: center; font-size: 32px; font-weight: bold;">{cantidad}</p>
        </div>
    """

    # Mostrar cuadros en las columnas
    with col1:
        st.markdown(cuadro_estilo.format(
            titulo="Rechazo",
            cantidad="{:,.0f}".format(conteo_rechazos["Rechazo"]),
            bg_color="#f2dede", text_color="#a94442"), unsafe_allow_html=True)

    with col2:
        st.markdown(cuadro_estilo.format(
            titulo="Desistido",
            cantidad="{:,.0f}".format(conteo_rechazos["Desistido"]),
            bg_color="#d9edf7", text_color="#31708f"), unsafe_allow_html=True)

    # Línea divisoria en gris claro
    st.markdown("<hr style='border: 2px solid #cccccc;'>", unsafe_allow_html=True)

    # Gráficos de barras por categoría y por localidad
    st.subheader("Gráfico de Barras: Rechazos por Categoría")
    grafico_barras_rechazos = df_global.groupby('N_ESTADO_FORMULARIO').size().reset_index(name='Cantidad')
    bar_chart_rechazos = px.bar(
        grafico_barras_rechazos,
        x='N_ESTADO_FORMULARIO',
        y='Cantidad',
        title='Cantidad de Rechazos por Categoría',
        labels={'Cantidad': 'Número de Rechazos', 'N_ESTADO_FORMULARIO': 'Tipo Rechazo'},
        color='Cantidad',
        color_continuous_scale='Reds'
    )
    st.plotly_chart(bar_chart_rechazos)

    # Top 10 Localidades Rechazadas
    st.subheader("Top 10 Localidades Rechazadas")
    conteo_localidades_rechazados = df_global['N_LOCALIDAD'].value_counts().reset_index()
    conteo_localidades_rechazados.columns = ['N_LOCALIDAD', 'Cantidad']
    conteo_localidades_rechazados = conteo_localidades_rechazados.sort_values(by='Cantidad', ascending=False).head(10)

    bar_chart_localidades_rechazados = px.bar(
        conteo_localidades_rechazados,
        x='N_LOCALIDAD',
        y='Cantidad',
        title='Top 10 Localidades Rechazadas',
        labels={'Cantidad': 'Número de Localidades Rechazadas'},
        color='Cantidad',
        color_continuous_scale='Reds'
    )
    bar_chart_localidades_rechazados.update_traces(texttemplate='%{y}', textposition='outside')
    st.plotly_chart(bar_chart_localidades_rechazados)

def mostrar_recupero(df_recupero, df_detalle_recupero, df_departamentos, geojson_data):
    
    # --- Procesamiento y Validación de df_recupero ---
    if 'FEC_FORM' not in df_recupero.columns:
        st.error("La columna 'FEC_FORM' no se encuentra en el DataFrame.")
        st.write("Columnas disponibles:", df_recupero.columns.tolist())
        return

    # Conversión de columnas de fecha con validación de rango
    date_columns = ['FEC_FORM', 'FEC_INICIO_PAGO', 'FEC_FIN_PAGO']
    min_date = pd.Timestamp.min
    max_date = pd.Timestamp.max

    # Validar columnas de fechas necesarias
    for col in date_columns:
        if col in df_recupero.columns:
            df_recupero[col] = pd.to_datetime(df_recupero[col], errors='coerce')
            df_recupero.loc[(df_recupero[col] < min_date) | (df_recupero[col] > max_date), col] = pd.NaT

    # Eliminar filas con fechas inválidas
    df_recupero = df_recupero.dropna(subset=['FEC_FORM'])

    if df_recupero.empty:
        st.warning("No hay datos válidos después de procesar las fechas. Verifica los datos cargados.")
        return

    # --- Cálculo de solicitudes en las últimas 24 horas ---
    fecha_actual = datetime.now()
    fecha_24hs_antes = fecha_actual - pd.Timedelta(days=1)
    solicitudes_ultimas_24hs = df_recupero[df_recupero['FEC_FORM'] >= fecha_24hs_antes]
    cantidad_solicitudes_24hs = solicitudes_ultimas_24hs.shape[0]

    # --- Categorías de estado ---
    estado_categorias = {
        "Pagados": [13, 14, 15, 16, 17, 18, 20, 21, 7],
        "Créditos con Deuda": [21],
        "Impagos/Bajas": [23, 22],
        "Finalizados": [7],
    }

    # Conteo por categoría
    conteo_estados = {
        categoria: df_recupero[df_recupero['ID_ESTADO_PRESTAMO'].isin(estados)].shape[0]
        for categoria, estados in estado_categorias.items()
    }

    # --- Diseño de columnas y cuadros de resumen ---
    col1, col2, col3, col4, col5 = st.columns(5)
    cuadro_estilo = """
        <div style="margin: 10px; padding: 15px; border-radius: 8px; background-color: {bg_color}; color: {text_color};
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); font-family: Arial, sans-serif;">
            <h3 style="text-align: center; font-size: 18px;">{titulo}</h3>
            <p style="text-align: center; font-size: 32px; font-weight: bold;">{cantidad}</p>
        </div>
    """

    # --- Mostrar cuadros de resumen ---
    with col1:
        st.markdown(cuadro_estilo.format(
            titulo="Pagados",
            cantidad="{:,.0f}".format(conteo_estados["Pagados"]),
            bg_color="#d9edf7", text_color="#31708f"), unsafe_allow_html=True)

    with col2:
        st.markdown(cuadro_estilo.format(
            titulo="Créditos con Deuda",
            cantidad="{:,.0f}".format(conteo_estados["Créditos con Deuda"]),
            bg_color="#f2dede", text_color="#a94442"), unsafe_allow_html=True)

    with col3:
        st.markdown(cuadro_estilo.format(
            titulo="Impagos/Bajas",
            cantidad="{:,.0f}".format(conteo_estados["Impagos/Bajas"]),
            bg_color="#f9e79f", text_color="#8a6d3b"), unsafe_allow_html=True)

    with col4:
        st.markdown(cuadro_estilo.format(
            titulo="Finalizados",
            cantidad="{:,.0f}".format(conteo_estados["Finalizados"]),
            bg_color="#dff0d8", text_color="#3c763d"), unsafe_allow_html=True)
        
    with col5:
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; flex-direction: column; align-items: center; margin-bottom: 30px;">
                <div style="width: 120px; height: 120px; background-color: #1E9AD8; color: white; 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center; 
                            font-size: 32px; font-weight: bold;">
                    {cantidad_solicitudes_24hs}
                </div>
                <p style="text-align: center; font-size: 16px; margin-top: 10px;">Solicitudes en las últimas 24 horas</p>
            </div>
            """, unsafe_allow_html=True)
        
    ## --- Divisor ---
    st.markdown("<hr style='border: 2px solid #cccccc;'>", unsafe_allow_html=True)

    # --- Calculo de deuda total y prescripta desde df_detalle_recupero ---
    if df_detalle_recupero is not None and not df_detalle_recupero.empty:
        deuda_total_detalle = df_detalle_recupero['DEUDA_TOTAL'].sum() if 'DEUDA_TOTAL' in df_detalle_recupero.columns else 0
        deuda_prescripta_detalle = df_detalle_recupero['DEUDA_PRESCRIPTA'].sum() if 'DEUDA_PRESCRIPTA' in df_detalle_recupero.columns else 0
        deuda_vencida_detalle = df_detalle_recupero['DEUDA_VENCIDA'].sum() if 'DEUDA_VENCIDA' in df_detalle_recupero.columns else 0
        deuda_no_vencida_detalle = df_detalle_recupero['DEUDA_NO_VENCIDA'].sum() if 'DEUDA_NO_VENCIDA' in df_detalle_recupero.columns else 0
    else:
        deuda_total_detalle = 0
        deuda_prescripta_detalle = 0
        deuda_vencida_detalle = 0
        deuda_no_vencida_detalle = 0
        st.warning("df_detalle_recupero esta vacio, no se pueden mostrar los datos de Deuda Total y deuda Prescripta")

    # --- Mostrar tarjetas de DEUDA VENCIDA, DEUDA NO VENCIDA, DEUDA TOTAL Y PRESCRIPTA---
    col5, col6, col8, col9 = st.columns(4)

    with col5:
        st.markdown(cuadro_estilo.format(
            titulo="DEUDA VENCIDA",
            cantidad="${:,.2f}".format(deuda_vencida_detalle),
            bg_color="#f2dede", text_color="#a94442"), unsafe_allow_html=True)

    with col6:
        st.markdown(cuadro_estilo.format(
            titulo="DEUDA NO VENCIDA",
            cantidad="${:,.2f}".format(deuda_no_vencida_detalle),
            bg_color="#d9edf7", text_color="#31708f"), unsafe_allow_html=True)
    
    with col8:
        st.markdown(cuadro_estilo.format(
            titulo="DEUDA TOTAL",
            cantidad="${:,.2f}".format(deuda_total_detalle),
            bg_color="#f9e79f", text_color="#8a6d3b"), unsafe_allow_html=True)

    with col9:
        st.markdown(cuadro_estilo.format(
            titulo="DEUDA PRESCRIPTA",
            cantidad="${:,.2f}".format(deuda_prescripta_detalle),
            bg_color="#dff0d8", text_color="#3c763d"), unsafe_allow_html=True)

def mostrar_global(geojson_data, df_departamentos, df_global, df_recupero):
    # Agregar título y fecha del archivo
    st.title("Análisis Global de Formularios")

    # Conversión de columnas de fecha con validación de rango
    date_columns = ['FECHA_INGRESO', 'FEC_INICIO_PAGO', 'FEC_FIN_PAGO']
    min_date = pd.Timestamp.min
    max_date = pd.Timestamp.max

    for col in date_columns:
        if col in df_global.columns:
            df_global[col] = pd.to_datetime(df_global[col], errors='coerce')
            df_global.loc[(df_global[col] < min_date) | (df_global[col] > max_date), col] = pd.NaT

    # Eliminar filas con fechas inválidas
    df_global = df_global.dropna(subset=['FECHA_INGRESO'])

    if df_global.empty:
        st.warning("No hay datos válidos después de procesar las fechas. Verifica los datos cargados.")
        return

    # Filtrar los datos por las fechas seleccionadas (sin barra lateral)
    df_filtrado_global = df_global  # Inicialmente el dataframe completo

    # Conteo de formularios por estado utilizando groupby con un diccionario de categorías
    estado_categorias = {
        "En Evaluación": [1, 2, 5],
        "Rechazados": [3, 6, 7, 15, 23],
        "A Pagar": [4, 9, 10, 11, 12, 13, 19, 20]
    }

    conteo_estados = (
        df_filtrado_global.groupby("ID_ESTADO_PRESTAMO")
        .size()
        .rename("conteo")
        .reset_index()
    )

    # Crear el diccionario de resultados con los totales para cada categoría
    resultados = {
        categoria: conteo_estados[conteo_estados["ID_ESTADO_PRESTAMO"].isin(estados)]['conteo'].sum()
        for categoria, estados in estado_categorias.items()
    }

    # Diseño de columnas y cuadros de resumen
    col1, col2, col3 = st.columns(3)
    cuadro_estilo = """
        <div style="margin: 10px; padding: 15px; border-radius: 8px; background-color: {bg_color}; color: {text_color};
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); font-family: Arial, sans-serif;">
            <h3 style="text-align: center; font-size: 18px;">{titulo}</h3>
            <p style="text-align: center; font-size: 32px; font-weight: bold;">{cantidad}</p>
        </div>
    """

    with col1:
        st.markdown(cuadro_estilo.format(
            titulo="Formularios en Evaluación",
            cantidad="{:,.0f}".format(resultados["En Evaluación"]),
            bg_color="#d9edf7", text_color="#31708f"), unsafe_allow_html=True)

    with col2:
        st.markdown(cuadro_estilo.format(
            titulo="Formularios Rechazados",
            cantidad="{:,.0f}".format(resultados["Rechazados"]),
            bg_color="#f2dede", text_color="#a94442"), unsafe_allow_html=True)

    with col3:
        st.markdown(cuadro_estilo.format(
            titulo="Formularios A Pagar",
            cantidad="{:,.0f}".format(resultados["A Pagar"]),
            bg_color="#dff0d8", text_color="#3c763d"), unsafe_allow_html=True)

    # Línea divisoria en gris claro
    st.markdown("<hr style='border: 2px solid #cccccc;'>", unsafe_allow_html=True)

    # Serie Histórica
    st.subheader("Serie Histórica: Evolución de Formularios a lo Largo del Tiempo")
    serie_historica = df_filtrado_global.groupby(df_filtrado_global['FECHA_INGRESO'].dt.to_period('M')).size().reset_index(name='Cantidad')
    serie_historica['FECHA_INGRESO'] = serie_historica['FECHA_INGRESO'].apply(
        lambda x: x.start_time if min_date <= x.start_time <= max_date else pd.NaT
    )
    serie_historica = serie_historica.dropna(subset=['FECHA_INGRESO'])

    fig_historia = px.line(
        serie_historica, 
        x='FECHA_INGRESO', 
        y='Cantidad', 
        title='Evolución de Formularios por Mes',
        labels={'Cantidad': 'Cantidad de Formularios', 'FECHA_INGRESO': 'Fecha'},
        markers=True
    )
    st.plotly_chart(fig_historia)

    # Línea divisoria en gris claro
    st.markdown("<hr style='border: 2px solid #cccccc;'>", unsafe_allow_html=True)

    # Gráfico de Torta
    st.subheader("Gráfico de Torta: Distribución de Formularios por Línea de Préstamo")
    grafico_torta = df_filtrado_global.groupby('N_LINEA_PRESTAMO').size().reset_index(name='Cantidad')

    fig_torta = px.pie(
        grafico_torta, 
        names='N_LINEA_PRESTAMO', 
        values='Cantidad', 
        title='Distribución de Formularios por Línea de Préstamo',
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig_torta)

def show_bco_gente_dashboard(data_dict, dates):
    """
    Muestra el dashboard de Banco de la Gente.
    
    Args:
        data_dict: Diccionario de dataframes cargados desde GitLab
        dates: Diccionario de fechas de actualización de los archivos
    """
    st.header("Banco de la Gente")
    
    # Verificar si tenemos los archivos necesarios
    required_files = ['vt_nomina_rep_dpto_localidad.parquet', 'VT_NOMINA_REP_RECUPERO_X_ANIO.parquet', 'Detalle_recupero.csv', 'capa_departamentos_2010.geojson', 'departamentos_poblacion.csv']
    missing_files = [file for file in required_files if file not in data_dict]
    
    if missing_files:
        st.warning(f"Faltan los siguientes archivos: {', '.join(missing_files)}")
        st.info("Se mostrarán datos de ejemplo.")
    
    # Obtener los dataframes específicos
    df_global = data_dict.get('vt_nomina_rep_dpto_localidad.parquet')
    df_recupero = data_dict.get('VT_NOMINA_REP_RECUPERO_X_ANIO.parquet')
    df_detalle_recupero = data_dict.get('Detalle_recupero.csv')
    geojson_data = data_dict.get('capa_departamentos_2010.geojson')
    df_departamentos = data_dict.get('departamentos_poblacion.csv')
    
    # Mostrar información de actualización de datos
    if dates:
        latest_date = max([d for d in dates.values() if d is not None], default=None)
        if latest_date:
            st.caption(f"Última actualización de datos: {latest_date}")
    
    # Crear pestañas para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["Global", "Recupero", "Rechazados"])
    
    with tab1:
        mostrar_global(geojson_data, df_departamentos, df_global, df_recupero)
    
    with tab2:
        mostrar_recupero(df_recupero, df_detalle_recupero, df_departamentos, geojson_data)
    
    with tab3:
        mostrar_rechazados(df_global, geojson_data, df_departamentos)