import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show_bco_gente_dashboard(data, dates):
    """
    Muestra el dashboard de Banco de la Gente.
    
    Args:
        data: Diccionario de dataframes cargados desde GitLab
        dates: Diccionario de fechas de actualización de los archivos
    """
    # Extraer los dataframes necesarios
    try:
        df_global = data.get('vt_nomina_rep_dpto_localidad.parquet')
        df_recupero = data.get('VT_NOMINA_REP_RECUPERO_X_ANIO.parquet')
        geojson_data = data.get('capa_departamentos_2010.geojson')
        df_departamentos = data.get('LOCALIDAD CIRCUITO ELECTORAL GEO Y ELECTORES - USAR.txt')
        
        # Verificar silenciosamente si los archivos existen
        has_global_data = df_global is not None and not df_global.empty
        has_recupero_data = df_recupero is not None and not df_recupero.empty
        has_geojson_data = geojson_data is not None
        
    except Exception as e:
        st.info("No se pudieron procesar algunos datos. Mostrando información disponible.")
        return
    
    # Mostrar información de actualización de datos
    if dates and any(dates.values()):
        latest_date = max([d for d in dates.values() if d is not None], default=None)
        if latest_date:
            st.caption(f"Última actualización de datos: {latest_date}")
    
    # Crear pestañas para diferentes vistas
    tab1, tab2 = st.tabs(["Global", "Recupero"])
    
    with tab1:
        if has_global_data and has_geojson_data:
            mostrar_global(geojson_data, df_departamentos, df_global, df_recupero)
        else:
            st.info("No hay datos suficientes para mostrar la vista global.")
    
    with tab2:
        if has_recupero_data and has_geojson_data:
            mostrar_recupero(df_recupero, df_departamentos, geojson_data)
        else:
            st.info("No hay datos suficientes para mostrar la vista de recupero.")
    

def mostrar_global(geojson_data, df_departamentos, df_global, df_recupero=None):
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
        "A Pagar": [4, 9, 10, 11, 12, 13, 19]
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

    # Línea divisoria en gris claro
    st.markdown("<hr style='border: 2px solid #cccccc;'>", unsafe_allow_html=True)

    # Filtros de fecha al final de la página en un formato compacto
    st.subheader("Filtros de Fecha para Global")

    # Convertir fechas de entrada a tipo datetime
    min_date = df_global['FECHA_INGRESO'].min().date()
    max_date = df_global['FECHA_INGRESO'].max().date()

    # Utilizando una sola fila para los filtros
    col_inicio, col_fin = st.columns(2)

    with col_inicio:
        fecha_inicio_global = st.date_input("Fecha de Inicio", min_date)

    with col_fin:
        fecha_fin_global = st.date_input("Fecha de Fin", max_date)

    # Verificar que las fechas seleccionadas sean válidas
    if fecha_inicio_global > fecha_fin_global:
        st.error("La fecha de inicio debe ser anterior a la fecha de fin.")
        return  # Detener la ejecución si las fechas son inválidas

    # Filtrar los datos por las fechas seleccionadas
    df_filtrado_global = df_global[
        (df_global['FECHA_INGRESO'] >= pd.to_datetime(fecha_inicio_global)) & 
        (df_global['FECHA_INGRESO'] <= pd.to_datetime(fecha_fin_global))
    ]

    # Confirmar filtro con un botón
    if st.button("Aplicar Filtros"):
        st.success(f"Filtros aplicados: desde {fecha_inicio_global} hasta {fecha_fin_global}.")

def mostrar_recupero(df_recupero, df_departamentos, geojson_data):
    
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
    fecha_24hs_antes = fecha_actual - timedelta(days=1)
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
    col1, col2, col3, col4,col5 = st.columns(5)
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

    # --- Calculo de deuda total y prescripta desde df_recupero ---
    deuda_total_detalle = df_recupero['DEUDA_TOTAL'].sum() if 'DEUDA_TOTAL' in df_recupero.columns else 0
    deuda_vencida_detalle = df_recupero['DEUDA_VENCIDA'].sum() if 'DEUDA_VENCIDA' in df_recupero.columns else 0
    deuda_no_vencida_detalle = df_recupero['DEUDA_NO_VENCIDA'].sum() if 'DEUDA_NO_VENCIDA' in df_recupero.columns else 0

    # --- Mostrar tarjetas de DEUDA VENCIDA, DEUDA NO VENCIDA, DEUDA TOTAL---
    col5, col6, col8,  = st.columns(3)

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
            bg_color="#f2dede", text_color="#a94442"), unsafe_allow_html=True)

   
    ## --- Divisor ---
    st.markdown("<hr style='border: 2px solid #cccccc;'>", unsafe_allow_html=True)

    # --- Serie de tiempo ---
    st.subheader("Evolución de la Deuda Vencida")
    if 'DEUDA' in df_recupero.columns and 'FEC_FORM' in df_recupero.columns:
        df_filtrado_deuda = df_recupero.dropna(subset=['FEC_FORM', 'DEUDA'])
        deuda_por_fecha = df_filtrado_deuda.groupby(df_filtrado_deuda['FEC_FORM'].dt.date)['DEUDA'].sum().reset_index()
        deuda_por_fecha.columns = ['Fecha', 'Deuda Total']

        if not deuda_por_fecha.empty:
            line_chart = px.line(
                deuda_por_fecha,
                x='Fecha',
                y='Deuda Total',
                labels={'Fecha': 'Fecha', 'Deuda Total': 'Deuda Vencida'},
                title='Evolución de la Deuda Vencida'
            )
            st.plotly_chart(line_chart)
        else:
            st.warning("No se encontraron datos para la serie de tiempo.")
    else:
        st.warning("No se encontró la columna 'DEUDA' para generar la serie de tiempo.")
