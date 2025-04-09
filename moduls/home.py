import streamlit as st
import os
import sys
from bco_gente import show_bco_gente_dashboard
from empleo import show_empleo_dashboard

def apply_custom_styles():
    """Apply custom CSS styles to improve the appearance of the home page."""
    st.markdown("""
        <style>
        /* General styles */
        .main {
            background-color: #f8f9fa;
            padding: 1rem;
        }
        
        /* Header styles */
        .header {
            padding: 20px;
            background: linear-gradient(90deg, #1976d2, #64b5f6);
            border-radius: 10px;
            margin-bottom: 30px;
            color: white;
            text-align: center;
        }
        
        /* Card styles */
        .report-card {
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
            border-left: 5px solid #1976d2;
        }
        
        .report-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .report-card h3 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        
        .report-card p {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .report-icon {
            font-size: 2.5rem;
            color: #1976d2;
            margin-bottom: 15px;
        }
        
        /* Footer styles */
        .footer {
            text-align: center;
            padding: 20px;
            color: #6c757d;
            font-size: 0.8rem;
            margin-top: 30px;
        }
        </style>
    """, unsafe_allow_html=True)

def show_home():
    """Display the home page with navigation to different reports."""
    apply_custom_styles()
    
    # Header
    st.markdown("""
        <div class="header">
            <h1>Tablero General de Reportes</h1>
            <p>Dirección de Tecnología y Análisis de Datos</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    st.markdown("""
        Bienvenido al Tablero General de Reportes. Seleccione uno de los siguientes reportes para visualizar:
    """)
    
    # Create a 2-column layout for report cards
    col1, col2 = st.columns(2)
    
    # Banco de la Gente Report Card
    with col1:
        st.markdown("""
            <div class="report-card" id="bco-gente-card">
                <div class="report-icon">💰</div>
                <h3>Banco de la Gente</h3>
                <p>Visualización de métricas clave y tendencias de formularios procesados, recupero y estado de deudas.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Add a button that will be clicked
        if st.button("Ir a Banco de la Gente", key="btn_bco_gente"):
            st.session_state.current_report = "bco_gente"
            st.experimental_rerun()
    
    # Empleo Report Card
    with col2:
        st.markdown("""
            <div class="report-card" id="empleo-card">
                <div class="report-icon">👔</div>
                <h3>Empleo</h3>
                <p>Análisis de datos de empleo, postulaciones, inscripciones y distribución geográfica.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Add a button that will be clicked
        if st.button("Ir a Empleo", key="btn_empleo"):
            st.session_state.current_report = "empleo"
            st.experimental_rerun()
    
    # Footer
    st.markdown("""
        <div class="footer">
            <p>© 2023 Gobierno de la Provincia de Córdoba - Todos los derechos reservados</p>
        </div>
    """, unsafe_allow_html=True)

def main():
    """Main function to run the application."""
    # Initialize session state for navigation
    if 'current_report' not in st.session_state:
        st.session_state.current_report = "home"
    
    # Get data from session state
    data = st.session_state.get('data', {})
    dates = st.session_state.get('dates', {})
    
    # Navigation logic
    if st.session_state.current_report == "home":
        show_home()
    elif st.session_state.current_report == "bco_gente":
        # Add a back button
        if st.button("← Volver al Inicio"):
            st.session_state.current_report = "home"
            st.experimental_rerun()
        
        try:
            # Show the Banco de la Gente dashboard with proper error handling
            show_bco_gente_dashboard(data, dates)
        except TypeError as e:
            st.error(f"Error al cargar el dashboard de Banco de la Gente: {str(e)}")
            st.info("Revise los parámetros de la función mostrar_global en bco_gente.py")
            
    elif st.session_state.current_report == "empleo":
        # Add a back button
        if st.button("← Volver al Inicio"):
            st.session_state.current_report = "home"
            st.experimental_rerun()
        
        try:
            # Show the Empleo dashboard with proper error handling
            show_empleo_dashboard(data, dates)
        except TypeError as e:
            st.error(f"Error al cargar el dashboard de Empleo: {str(e)}")
            st.info("Revise la configuración de los gráficos Altair en empleo.py")
    
    # Add more report options as needed