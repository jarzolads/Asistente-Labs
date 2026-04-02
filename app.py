import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai

# 1. Configuración inicial de la página
st.set_page_config(
    page_title="Inventario Químico - UT Tehuacán", 
    page_icon="🧪",
    layout="wide"
)

# 2. Configuración de la IA (Gemini)
# El bloque try/except evita que la app falle si aún no pones la clave
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Utilizamos la versión flash, ideal para respuestas rápidas de texto
    model = genai.GenerativeModel('gemini-1.5-flash') 
    ia_activa = True
except Exception as e:
    ia_activa = False
    st.sidebar.warning("⚠️ IA Desactivada. Configura GEMINI_API_KEY en los secretos para activar el Asistente de Seguridad.")

# Encabezado principal
st.title("🔬 Gestión Centralizada de Reactivos")
st.markdown("**Universidad Tecnológica de Tehuacán** | Consulta de disponibilidad y análisis de seguridad (IA).")

# 3. Configuración de Laboratorios (Reemplaza con tus URLs de prueba)
LABS = {
    "Laboratorio de Química Orgánica": "https://docs.google.com/spreadsheets/d/14zJKq0Vz4DysPnxCuHziEY1gXmEfDNobmtWiVjeK22M/edit?usp=sharing",
    "Laboratorio de Operaciones Unitarias": "https://docs.google.com/spreadsheets/d/1KN_BtaMVfclW-F6GfymrvhPRD6looPiqzNcqTWw8kJE/edit?usp=sharing",
    "Laboratorio de Análisis Instrumental": "https://docs.google.com/spreadsheets/d/1f6yGcIZsUUr_Qp8Vxv2ONKEYzZND5bNr5reBEhalJP8/edit?usp=sharing"
}

# 4. Interfaz Lateral (Sidebar)
st.sidebar.header("Navegación")
lab_seleccionado = st.sidebar.selectbox("Seleccione el Laboratorio:", list(LABS.keys()))

st.sidebar.divider()
st.sidebar.info("💡 **Instrucciones:**\n1. Seleccione un laboratorio.\n2. Busque el reactivo por nombre o CAS.\n3. Utilice el asistente al final de la página para leer la Hoja de Seguridad resumida.")

# 5. Conexión a Google Sheets y Visualización
url_sheet = LABS[lab_seleccionado]
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Leemos los datos de la hoja correspondiente
    df = conn.read(spreadsheet=url_sheet)
    
    # Limpieza básica: quitar filas completamente vacías
    df = df.dropna(how="all")
    
    st.subheader(f"📦 Inventario actual: {lab_seleccionado}")
    
    # Motor de búsqueda
    busqueda = st.text_input("🔍 Buscar reactivo por nombre o CAS:", "")
    
    # Filtrado del DataFrame
    if busqueda:
        df_filtered = df[df['Nombre'].str.contains(busqueda, case=False, na=False) | 
                         df['CAS'].str.contains(busqueda, case=False, na=False)]
    else:
        df_filtered = df

    # Mostrar la tabla sin el índice de pandas
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)

    # 6. Módulo del Asistente Técnico y de Seguridad
    if not df_filtered.empty and ia_activa:
        st.divider()
        st.subheader("🛡️ Asistente Técnico y de Seguridad (IA)")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            sustancia_analisis = st.selectbox(
                "Seleccione un reactivo para consultar su Hoja de Seguridad:", 
                df_filtered['Nombre'].unique()
            )
            analizar_btn = st.button("Analizar con Gemini", type="primary", use_container_width=True)
            
        with col2:
            if analizar_btn:
                with st.spinner(f"Analizando propiedades químicas y de seguridad para: {sustancia_analisis}..."):
                    # Prompt de ingeniería estructurado para obtener respuestas precisas
                    prompt = f"""
                    Actúa como un ingeniero químico experto en seguridad de laboratorios e higiene industrial.
                    Proporciona un resumen técnico y de seguridad sobre la sustancia '{sustancia_analisis}'.
                    Estructura tu respuesta estrictamente con los siguientes encabezados:
                    
                    * **Clasificación de Peligros (SGA/GHS):** (Menciona los riesgos principales).
                    * **Primeros Auxilios Básicos:** (Qué hacer en caso de contacto o inhalación).
                    * **Equipo de Protección Personal (EPP):** (Guantes recomendados, tipo de mascarilla, etc.).
                    * **Aplicaciones en Ingeniería Química:** (Usos comunes en prácticas universitarias o industria).
                    
                    Sé conciso, profesional y utiliza viñetas.
                    """
                    try:
                        respuesta = model.generate_content(prompt)
                        st.info(respuesta.text)
                    except Exception as e:
                        st.error("Hubo un problema de conexión con la IA. Intenta de nuevo más tarde.")

except Exception as e:
    st.error(f"❌ Error al conectar con la base de datos de {lab_seleccionado}.")
    st.warning("Verifica que el enlace de Google Sheets sea correcto, esté público como 'Lector' y contenga datos.")
