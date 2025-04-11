import pandas as pd
import geopandas as gpd
import requests
import streamlit as st
import io
import time
import datetime
import numpy as np
import subprocess
import sys

def obtener_archivo_gitlab(repo_id, file_path, branch='main', token=None):
    """Obtiene un archivo de GitLab"""
    if not token:
        st.error("Token de GitLab no proporcionado")
        return None
        
    # Asegurar que el repo_id esté correctamente formateado
    repo_id_encoded = requests.utils.quote(str(repo_id), safe='')
    
    # Asegurar que el file_path esté correctamente formateado
    file_path_encoded = requests.utils.quote(file_path, safe='')
    
    url = f'https://gitlab.com/api/v4/projects/{repo_id_encoded}/repository/files/{file_path_encoded}/raw'
    headers = {'PRIVATE-TOKEN': token}
    params = {'ref': branch}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.content
        else:
            st.error(f"Error al obtener archivo {file_path}: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

def obtener_lista_archivos(repo_id, branch='main', token=None):
    """Obtiene la lista de archivos del repositorio"""
    if not token:
        st.error("Token de GitLab no proporcionado")
        return []
    
    # Probar diferentes formatos de ID
    formatos_id = [
        repo_id,
        requests.utils.quote(repo_id, safe=''),
        repo_id.replace('/', '%2F')
    ]
    
    for id_formato in formatos_id:
        url = f'https://gitlab.com/api/v4/projects/{id_formato}/repository/tree'
        headers = {'PRIVATE-TOKEN': token}
        params = {'ref': branch, 'recursive': True}
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                items = response.json()
                archivos = [item['path'] for item in items if item['type'] == 'blob']
                return archivos
        except Exception as e:
            st.error(f"Error al obtener lista de archivos: {str(e)}")
            continue
    
    # Intentar listar proyectos disponibles para ayudar al diagnóstico
    try:
        st.info("Verificando proyectos accesibles con tu token...")
        url = 'https://gitlab.com/api/v4/projects?membership=true&per_page=5'
        headers = {'PRIVATE-TOKEN': token}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            projects = response.json()
            if projects:
                st.info("Proyectos disponibles con tu token:")
                for p in projects:
                    st.info(f"ID: {p['id']}, Path: {p['path_with_namespace']}")
            else:
                st.error("No tienes acceso a ningún proyecto con este token")
        else:
            st.error(f"Error al verificar proyectos: {response.status_code}")
    except Exception as e:
        st.error(f"Error al listar proyectos: {str(e)}")
    
    return []

def convert_numpy_types(df):
    """
    Convierte tipos de datos numpy a tipos Python nativos en un DataFrame.
    Esto ayuda a evitar errores como 'Python value of type numpy.int64 not supported'.

    Args:
        df: DataFrame a convertir

    Returns:
        DataFrame con tipos de datos Python nativos
    """
    if df is None or df.empty:
        return df

    # Función para convertir valores numpy a Python nativos
    def convert_value(val):
        if isinstance(val, np.integer):
            return int(val)
        elif isinstance(val, np.floating):
            return float(val)
        elif isinstance(val, np.ndarray):
            return val.tolist()
        elif isinstance(val, np.bool_):
            return bool(val)
        else:
            return val

    # Aplicar la conversión a todo el DataFrame
    for col in df.columns:
        if df[col].dtype.kind in 'iufc':  # integers, unsigned integers, floats, complex
            df[col] = df[col].apply(convert_value)

    return df

def load_data_from_gitlab(repo_id, branch='main', token=None):
    """Carga todos los archivos del repositorio"""
    try:
        # Obtener lista de archivos
        archivos = obtener_lista_archivos(repo_id, branch, token)

        if not archivos:
            return {}, {}

        # Filtrar por extensiones soportadas
        extensiones = ['.parquet', '.csv', '.geojson', '.txt']
        archivos_filtrados = [a for a in archivos if any(a.endswith(ext) for ext in extensiones)]

        # Diccionarios para datos y fechas
        all_data = {}
        all_dates = {}

        # Barra de progreso
        progress = st.progress(0)
        total = len(archivos_filtrados)

        # Cargar cada archivo
        for i, archivo in enumerate(archivos_filtrados):
            try:
                # Actualizar progreso
                progress.progress((i + 1) / total)

                # Obtener contenido
                contenido = obtener_archivo_gitlab(repo_id, archivo, branch, token)
                if contenido is None:
                    continue

                # Extraer nombre de archivo
                nombre = archivo.split('/')[-1]

                # Cargar según extensión
                if archivo.endswith('.parquet'):
                    try:
                        # Usar pyarrow directamente para todos los archivos Parquet
                        # para evitar problemas de conversión de timestamp
                        try:
                            import pyarrow.parquet as pq
                        except ImportError:
                            # Install pyarrow if not present
                            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyarrow"])
                            import pyarrow.parquet as pq
                            
                        table = pq.read_table(io.BytesIO(contenido))
                        # Convertir a pandas con opción para ignorar conversión de timestamp
                        df = table.to_pandas(timestamp_as_object=True)

                        # Ajustar la precisión de las marcas de tiempo a microsegundos
                        for col in df.columns:
                            if pd.api.types.is_datetime64_any_dtype(df[col]):
                                df[col] = df[col].dt.round('us')

                        # Simplificación del manejo de fechas
                        for col in df.columns:
                            # Verificar si la columna parece contener fechas
                            if df[col].dtype == 'object' and df[col].notna().any():
                                sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                                if isinstance(sample, (datetime.datetime, datetime.date)):
                                    try:
                                        # Enfoque simplificado: usar pd.to_datetime con errores='coerce'
                                        # Esto convertirá fechas inválidas a NaT en lugar de generar errores
                                        df[col] = pd.to_datetime(df[col], errors='coerce')
                                    except:
                                        # Si hay algún otro error, dejar como object
                                        pass


                        # Convertir tipos numpy a tipos Python nativos
                        df = convert_numpy_types(df)
                    except Exception as e:
                        st.warning(f"Error al procesar {nombre} con PyArrow: {str(e)}")
                        # Intentar con pandas directamente como último recurso
                        try:
                            df = pd.read_parquet(io.BytesIO(contenido))
                        except Exception as e2:
                            st.error(f"No se pudo cargar {nombre} después de múltiples intentos: {str(e2)}")
                            continue
                elif archivo.endswith('.csv'):
                    df = pd.read_csv(io.BytesIO(contenido))
                elif archivo.endswith('.geojson'):
                    df = gpd.read_file(io.BytesIO(contenido))
                elif archivo.endswith('.txt'):
                    # Handle text files properly
                    df = pd.read_csv(io.BytesIO(contenido), sep='\t', encoding='utf-8')
                else:
                    continue

                # Convertir tipos numpy a tipos Python nativos
                df = convert_numpy_types(df)

                # Guardar en diccionarios - check if df is not empty
                if df is not None and not df.empty:
                    all_data[nombre] = df
                    all_dates[nombre] = time.strftime("%Y-%m-%d")
                else:
                    st.warning(f"Archivo vacío: {nombre}")

            except Exception as e:
                st.warning(f"Error al procesar {archivo}: {str(e)}")
                continue

        # Limpiar barra de progreso
        progress.empty()
        
        return all_data, all_dates

    except Exception as e:
        st.error(f"Error general: {str(e)}")
        return {}, {}