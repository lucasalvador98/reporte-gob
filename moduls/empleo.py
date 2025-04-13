import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import math
import requests
import io
import json
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
        /* Variables de colores de la identidad visual */
        :root {
            --color-primary: #0085c8;
            --color-secondary: #00a8e6;
            --color-accent-1: #e73446;
            --color-accent-2: #fbbb21;
            --color-accent-3: #bccf00;
            --color-accent-4: #8a1e82;
            --color-accent-5: #ee7326;
        }
        
        /* General styles */
        .main {
            background-color: #f8f9fa;
            padding: 1rem;
        }
        
        /* Header styles */
        .dashboard-header {
            background-color: var(--color-primary);
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Filter container */
        .filter-container {
            background-color: #f0f2f6;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border-left: 4px solid var(--color-secondary);
        }
        
        /* Card styles */
        .metric-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 15px;
            transition: transform 0.3s ease;
            border-top: 4px solid var(--color-primary);
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: bold;
            color: var(--color-primary);
        }
        
        .metric-label {
            font-size: 14px;
            color: #6c757d;
            margin-bottom: 5px;
        }
        
        /* Table styles */
        .styled-table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.9em;
            font-family: sans-serif;
            min-width: 400px;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .styled-table thead tr {
            background-color: var(--color-primary);
            color: #ffffff;
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
            border-bottom: 2px solid var(--color-primary);
        }
        
        /* Status indicators */
        .status-success {background-color: #d1e7dd; border-left: 5px solid var(--color-accent-3);}
        .status-info {background-color: #d0e3f1; border-left: 5px solid var(--color-primary);}
        .status-warning {background-color: #fff3cd; border-left: 5px solid var(--color-accent-2);}
        .status-danger {background-color: #f8d7da; border-left: 5px solid var(--color-accent-1);}
        
        /* Section headers */
        h3 {
            color: var(--color-primary);
            border-bottom: 2px solid var(--color-secondary);
            padding-bottom: 5px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if not data:
        st.info("No se pudieron cargar los datos de PROGRAMAS DE EMPLEO.")
        return
    
    # Extraer los dataframes necesarios
    try:
        # Cargar los datasets necesarios
        df_inscriptos_raw = data.get('VT_REPORTES_PPP_MAS26.parquet')
        geojson_data = data.get('capa_departamentos_2010.geojson')
        
        # Cargar el dataset de empresas
        df_empresas = data.get('vt_empresas_adheridas.parquet')
        has_empresas = df_empresas is not None and not df_empresas.empty
        
        # Cargar el nuevo dataset de liquidación por localidad
        df_liquidacion = data.get('VT_REPORTE_LIQUIDACION_LOCALIDAD.parquet')
        has_liquidacion = df_liquidacion is not None and not df_liquidacion.empty
        
        # Solo mostrar mensaje si hay error al cargar el dataset
        if not has_liquidacion:
            st.warning("No se pudo cargar el dataset de liquidación por localidad.")
        
        # Verificar que los datos estén disponibles
        if df_inscriptos_raw is None or df_inscriptos_raw.empty:
            st.error("No se pudieron cargar los datos de inscripciones.")
            return
            
        # Filtrar para excluir el estado "ADHERIDO"
        if 'N_ESTADO_FICHA' in df_inscriptos_raw.columns:
            df_inscriptos = df_inscriptos_raw[df_inscriptos_raw['N_ESTADO_FICHA'] != "ADHERIDO"].copy()
            # No mostrar información sobre los registros filtrados
            total_registros = len(df_inscriptos_raw)
            registros_adheridos = total_registros - len(df_inscriptos)
        else:
            df_inscriptos = df_inscriptos_raw.copy()
            st.warning("No se encontró la columna 'N_ESTADO_FICHA' para filtrar el estado 'ADHERIDO'.")
            
        # Corregir localidades del departamento CAPITAL a "CORDOBA"
        if 'N_DEPARTAMENTO' in df_inscriptos.columns and 'N_LOCALIDAD' in df_inscriptos.columns:
            # Crear una máscara para identificar registros del departamento CAPITAL
            capital_mask = df_inscriptos['N_DEPARTAMENTO'] == 'CAPITAL'
            
            # Aplicar la corrección solo a los registros del departamento CAPITAL
            df_inscriptos.loc[capital_mask, 'N_LOCALIDAD'] = 'CORDOBA'
        
        # Añadir columna de ZONA FAVORECIDA
        zonas_favorecidas = [
            'PRESIDENTE ROQUE SAENZ PEÑA', 'GENERAL ROCA', 'RIO SECO', 'TULUMBA', 
            'POCHO', 'SAN JAVIER', 'SAN ALBERTO', 'MINAS', 'CRUZ DEL EJE', 
            'TOTORAL', 'SOBREMONTE', 'ISCHILIN'
        ]
        
        # Crear la columna ZONA
        df_inscriptos['ZONA'] = df_inscriptos['N_DEPARTAMENTO'].apply(
            lambda x: 'ZONA FAVORECIDA' if x in zonas_favorecidas else 'ZONA REGULAR'
        )
        
        # Obtener la fecha de última actualización
        file_dates = [dates.get(k) for k in dates.keys() if 'VT_REPORTES_PPP_MAS26.parquet' in k]
        latest_date = file_dates[0] if file_dates else None
        
        if latest_date:
            latest_date = pd.to_datetime(latest_date)
            st.markdown(f"""
                <div style="background-color:#e9ecef; padding:10px; border-radius:5px; margin-bottom:20px; font-size:0.9em;">
                    <i class="fas fa-sync-alt"></i> <strong>Última actualización:</strong> {latest_date.strftime('%d/%m/%Y')}
                </div>
            """, unsafe_allow_html=True)
   
        
        # Preparar datos para los filtros
        # Limpiar y preparar los datos
        df = df_inscriptos.copy()
        
        # Mapeo de programas según IDETAPA
        programas = {
            53: "Programa Primer Paso",
            51: "Más 26",
            54: "CBA Mejora",
            55: "Nueva Oportunidad"
        }
        
        # Crear columna con nombres de programas
        if 'IDETAPA' in df.columns:
            df['PROGRAMA'] = df['IDETAPA'].map(lambda x: programas.get(x, f"Programa {x}"))
        else:
            df['PROGRAMA'] = "No especificado"
            
        # Asegurar que las columnas necesarias existan
        required_columns = ['N_DEPARTAMENTO', 'N_LOCALIDAD', 'ID_FICHA', 'N_ESTADO_FICHA', 'IDETAPA']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.warning(f"Faltan las siguientes columnas en los datos: {', '.join(missing_columns)}")
            st.write("Columnas disponibles:", df.columns.tolist())
            return
        
        # Calcular KPIs importantes antes de aplicar filtros
        total_beneficiarios = df[df['N_ESTADO_FICHA'] == "BENEFICIARIO"].shape[0]
        total_beneficiarios_cti = df[df['N_ESTADO_FICHA'] == "BENEFICIARIO- CTI"].shape[0]
        total_general = total_beneficiarios + total_beneficiarios_cti
        
        # Calcular beneficiarios por zona
        beneficiarios_zona_favorecida = df[(df['N_ESTADO_FICHA'].isin(["BENEFICIARIO", "BENEFICIARIO- CTI"])) & 
                                          (df['ZONA'] == 'ZONA FAVORECIDA')].shape[0]
        
        # Mostrar KPIs en la parte superior
        st.markdown('<div style="padding: 10px 0 20px 0;">', unsafe_allow_html=True)
        kpi_cols = st.columns(4)
        
        with kpi_cols[0]:
            st.markdown(f"""
                <div style="background-color: var(--color-primary); color: white; padding: 15px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 14px; margin-bottom: 5px;">BENEFICIARIOS</div>
                    <div style="font-size: 28px; font-weight: bold;">{total_beneficiarios:,}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with kpi_cols[1]:
            st.markdown(f"""
                <div style="background-color: var(--color-secondary); color: white; padding: 15px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 14px; margin-bottom: 5px;">BENEFICIARIOS CTI</div>
                    <div style="font-size: 28px; font-weight: bold;">{total_beneficiarios_cti:,}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with kpi_cols[2]:
            st.markdown(f"""
                <div style="background-color: var(--color-accent-3); color: white; padding: 15px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 14px; margin-bottom: 5px;">TOTAL BENEFICIARIOS</div>
                    <div style="font-size: 28px; font-weight: bold;">{total_general:,}</div>
                </div>
            """, unsafe_allow_html=True)
            
        with kpi_cols[3]:
            st.markdown(f"""
                <div style="background-color: var(--color-accent-4); color: white; padding: 15px; border-radius: 10px; text-align: center;">
                    <div style="font-size: 14px; margin-bottom: 5px;">ZONA FAVORECIDA</div>
                    <div style="font-size: 28px; font-weight: bold;">{beneficiarios_zona_favorecida:,}</div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Crear pestañas para organizar el contenido
        tab_beneficiarios, tab_empresas = st.tabs(["Beneficiarios", "Empresas"])
        
        # Contenido de la pestaña Beneficiarios
        with tab_beneficiarios:
            # Contenedor para filtros
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            st.markdown('<h3 style="font-size: 18px; margin-top: 0;">Filtros</h3>', unsafe_allow_html=True)
            
            # Crear dos columnas para los filtros
            col1, col2 = st.columns(2)
            
            # Filtro de departamento en la primera columna
            with col1:
                departamentos = sorted(df['N_DEPARTAMENTO'].dropna().unique())
                all_dpto_option = "Todos los departamentos"
                selected_dpto = st.selectbox("Departamento:", [all_dpto_option] + list(departamentos))
            
            # Filtrar por departamento seleccionado
            if selected_dpto != all_dpto_option:
                df_filtered = df[df['N_DEPARTAMENTO'] == selected_dpto]
                # Filtro de localidad (dependiente del departamento)
                localidades = sorted(df_filtered['N_LOCALIDAD'].dropna().unique())
                all_loc_option = "Todas las localidades"
                
                # Mostrar filtro de localidad en la segunda columna
                with col2:
                    selected_loc = st.selectbox("Localidad:", [all_loc_option] + list(localidades))
                
                if selected_loc != all_loc_option:
                    df_filtered = df_filtered[df_filtered['N_LOCALIDAD'] == selected_loc]
            else:
                df_filtered = df
                # Si no se seleccionó departamento, mostrar todas las localidades
                localidades = sorted(df['N_LOCALIDAD'].dropna().unique())
                all_loc_option = "Todas las localidades"
                
                # Mostrar filtro de localidad en la segunda columna
                with col2:
                    selected_loc = st.selectbox("Localidad:", [all_loc_option] + list(localidades))
                
                if selected_loc != all_loc_option:
                    df_filtered = df_filtered[df_filtered['N_LOCALIDAD'] == selected_loc]
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Mostrar resumen de filtros aplicados
            filtros_aplicados = []
            if selected_dpto != all_dpto_option:
                filtros_aplicados.append(f"Departamento: {selected_dpto}")
            if selected_loc != all_loc_option:
                filtros_aplicados.append(f"Localidad: {selected_loc}")
                
            if filtros_aplicados:
                st.markdown(f"""
                    <div style="background-color:#e9ecef; padding:10px; border-radius:5px; margin-bottom:20px; font-size:0.9em;">
                        <strong>Filtros aplicados:</strong> {' | '.join(filtros_aplicados)}
                    </div>
                """, unsafe_allow_html=True)
            
            # Crear tabla de conteo por ETAPA y ESTADO_FICHA
            if not df_filtered.empty:
                # Conteo de ID_FICHA por PROGRAMA y ESTADO_FICHA
                pivot_table = df_filtered.pivot_table(
                    index='PROGRAMA',
                    columns='N_ESTADO_FICHA',
                    values='ID_FICHA',
                    aggfunc='count',
                    fill_value=0
                )
                
                # Añadir totales
                pivot_table['Total'] = pivot_table.sum(axis=1)
                pivot_table.loc['Total'] = pivot_table.sum()
                
                # Mostrar tabla con estilo mejorado
                st.markdown('<h3 style="font-size: 20px; margin: 20px 0 15px 0;">Conteo de Fichas por Programa y Estado</h3>', unsafe_allow_html=True)
                
                # Convertir pivot table a DataFrame para mejor visualización
                pivot_df = pivot_table.reset_index()
                
                # Estilizar la tabla con st.dataframe y ocultar el índice
                st.dataframe(pivot_df, use_container_width=True, hide_index=True)
                
                # Mostrar tabla de beneficiarios por localidad
                st.markdown('<h3 style="font-size: 20px; margin: 20px 0 15px 0;">Beneficiarios por Localidad</h3>', unsafe_allow_html=True)
                
                # Filtrar solo beneficiarios del DataFrame ya filtrado por departamento/localidad
                beneficiarios_estados = ["BENEFICIARIO", "BENEFICIARIO- CTI"]
                df_beneficiarios = df_filtered[df_filtered['N_ESTADO_FICHA'].isin(beneficiarios_estados)]
                
                if df_beneficiarios.empty:
                    st.warning("No hay beneficiarios con los filtros seleccionados.")
                else:
                    # Crear pivot table para mostrar cada estado en una columna separada
                    df_pivot = df_beneficiarios.pivot_table(
                        index=['N_DEPARTAMENTO', 'N_LOCALIDAD'],
                        columns='N_ESTADO_FICHA',
                        values='ID_FICHA',
                        aggfunc='count',
                        fill_value=0
                    ).reset_index()
                    
                    # Renombrar columnas para mejor visualización
                    if 'BENEFICIARIO' not in df_pivot.columns:
                        df_pivot['BENEFICIARIO'] = 0
                    if 'BENEFICIARIO- CTI' not in df_pivot.columns:
                        df_pivot['BENEFICIARIO- CTI'] = 0
                    
                    # Añadir columna de total
                    df_pivot['TOTAL'] = df_pivot['BENEFICIARIO'] + df_pivot['BENEFICIARIO- CTI']
                    
                    # Ordenar por departamento y total (descendente)
                    df_pivot_sorted = df_pivot.sort_values(['N_DEPARTAMENTO', 'TOTAL'], ascending=[True, False])
                    
                    # Mostrar tabla con estilo mejorado y sin índice
                    st.dataframe(
                        df_pivot_sorted,
                        use_container_width=True,
                        hide_index=True
                    )
            
            # Mostrar distribución geográfica si hay datos geojson y no hay filtros específicos
            if geojson_data is not None and selected_dpto == all_dpto_option:
                st.markdown('<h3 style="font-size: 20px; margin: 20px 0 15px 0;">Distribución Geográfica</h3>', unsafe_allow_html=True)
                
                # Filtrar solo beneficiarios
                beneficiarios_estados = ["BENEFICIARIO", "BENEFICIARIO- CTI"]
                df_beneficiarios = df[df['N_ESTADO_FICHA'].isin(beneficiarios_estados)]
                
                if df_beneficiarios.empty:
                    st.warning("No hay beneficiarios para mostrar en el mapa.")
                    return
                
                # Contar beneficiarios por departamento
                # Verificar si existe la columna ID_DPTO para relacionar con el GeoJSON
                if 'ID_DPTO' in df_beneficiarios.columns:
                    # Usar ID_DPTO para agrupar
                    df_mapa = df_beneficiarios.groupby('ID_DPTO').size().reset_index(name='Cantidad')
                    
                    # Convertir ID_DPTO a entero y luego a string para eliminar decimales
                    df_mapa['ID_DPTO'] = df_mapa['ID_DPTO'].astype(int).astype(str)
                    
                    id_field = 'ID_DPTO'
                else:
                    # Usar N_DEPARTAMENTO como alternativa
                    df_mapa = df_beneficiarios.groupby('N_DEPARTAMENTO').size().reset_index(name='Cantidad')
                    id_field = 'N_DEPARTAMENTO'
                
                # Mostrar tabla de datos para el mapa
                st.write(f"Datos para el mapa (agrupados por {id_field}):")
                st.dataframe(df_mapa)
                
                # Intentar crear el mapa con los datos disponibles
                try:
                    # Determinar qué campo usar para la relación
                    if isinstance(geojson_data, dict) and 'features' in geojson_data:
                        # Verificar qué campos están disponibles en el GeoJSON
                        sample_props = geojson_data['features'][0]['properties'] if geojson_data['features'] else {}
                        
                        # Usar CODDEPTO (en mayúsculas) como clave de relación
                        featureidkey = "properties.CODDEPTO"
                        
                        # Intentar un enfoque alternativo para el mapa
                        try:
                            # Crear mapa coroplético simplificado
                            fig = px.choropleth_mapbox(
                                df_mapa,
                                geojson=geojson_data,
                                locations=id_field,
                                featureidkey=featureidkey,
                                color='Cantidad',
                                color_continuous_scale="Blues",
                                mapbox_style="carto-positron",
                                zoom=6,
                                center={"lat": -31.4, "lon": -64.2},
                                opacity=0.7,
                                labels={'Cantidad': 'Beneficiarios'}
                            )
                            
                            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Si el mapa anterior no funciona, intentar con un enfoque más simple
                            st.write("Intentando con un enfoque alternativo...")
                            
                            # Crear un mapa simple con Plotly Express
                            fig2 = px.choropleth(
                                df_mapa,
                                geojson=geojson_data,
                                locations=id_field,
                                featureidkey=featureidkey,
                                color='Cantidad',
                                color_continuous_scale="Blues",
                                scope="south america"
                            )
                            
                            fig2.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=600)
                            st.plotly_chart(fig2, use_container_width=True)
                            
                        except Exception as e:
                            st.error(f"Error al crear el mapa: {str(e)}")
                            
                            # Intentar un enfoque aún más simple
                            st.write("Intentando con un mapa básico...")
                            try:
                                # Crear un mapa básico sin mapbox
                                simple_fig = px.choropleth(
                                    df_mapa,
                                    geojson=geojson_data,
                                    locations=id_field,
                                    featureidkey=featureidkey,
                                    color='Cantidad',
                                    color_continuous_scale="Blues"
                                )
                                
                                simple_fig.update_layout(
                                    margin={"r":0,"t":0,"l":0,"b":0}, 
                                    height=600,
                                    geo=dict(
                                        showframe=False,
                                        showcoastlines=False,
                                        projection_type='mercator'
                                    )
                                )
                                st.plotly_chart(simple_fig, use_container_width=True)
                            except Exception as e2:
                                st.error(f"Error al crear el mapa básico: {str(e2)}")
                                
                                # Mostrar más información de diagnóstico
                                st.write("Información de diagnóstico adicional:")
                                st.write("Estructura del GeoJSON:")
                                if 'features' in geojson_data:
                                    st.write(f"Número de features: {len(geojson_data['features'])}")
                                    if geojson_data['features']:
                                        st.write("Primera feature:")
                                        st.json(geojson_data['features'][0])
                except Exception as e:
                    st.error(f"Error al crear el mapa: {str(e)}")
                    st.write("Intente verificar que los campos ID_DPTO y CODDEPTO contengan valores compatibles.")
        with tab_empresas:
            if has_empresas:
                show_companies(df_empresas, geojson_data)
            else:
                st.markdown("""
                    <div class="info-box status-warning">
                        <strong>Información:</strong> No hay datos de empresas disponibles.
                    </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error al procesar los datos: {str(e)}")

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