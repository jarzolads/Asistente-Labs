import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import google.generativeai as genai

# 1. Configuración de la página
st.set_page_config(page_title="Inventario Global UT Tehuacán", page_icon="🧪", layout="wide")

# 2. Configuración de IA
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') 
    ia_activa = True
except Exception:
    ia_activa = False

st.title("🔬 Sistema de Búsqueda Global de Reactivos")
st.markdown("Busca en todos los laboratorios de la universidad para optimizar el uso de sustancias químicas.")

# 3. Definición de Laboratorios (Sustituye por tus links reales)
LABS = {
    "Laboratorio de Química Orgánica": "https://docs.google.com/spreadsheets/d/14zJKq0Vz4DysPnxCuHziEY1gXmEfDNobmtWiVjeK22M/edit?usp=sharing",
    "Laboratorio de Operaciones Unitarias": "https://docs.google.com/spreadsheets/d/1KN_BtaMVfclW-F6GfymrvhPRD6looPiqzNcqTWw8kJE/edit?usp=sharing",
    "Laboratorio de Análisis Instrumental": "https://docs.google.com/spreadsheets/d/1f6yGcIZsUUr_Qp8Vxv2ONKEYzZND5bNr5reBEhalJP8/edit?usp=sharing"
}

# 4. Función para cargar y consolidar todos los datos
@st.cache_data(ttl=600) # Caché de 10 minutos para no saturar las conexiones
def cargar_inventario_maestro():
    conn = st.connection("gsheets", type=GSheetsConnection)
    lista_dfs = []
    
    for nombre_lab, url in LABS.items():
        try:
            # Leer cada hoja
            df_temp = conn.read(spreadsheet=url)
            df_temp = df_temp.dropna(how="all")
            # Forzamos que la columna 'Laboratorio' indique de dónde viene el dato
            df_temp['Ubicación Actual'] = nombre_lab
            lista_dfs.append(df_temp)
        except Exception as e:
            st.error(f"Error al leer {nombre_lab}: {e}")
            
    if lista_dfs:
        return pd.concat(lista_dfs, ignore_index=True)
    return pd.DataFrame()

# Carga inicial de datos
with st.spinner("Consolidando inventarios de todos los laboratorios..."):
    df_maestro = cargar_inventario_maestro()

# 5. Interfaz de Búsqueda Global
if not df_maestro.empty:
    st.sidebar.header("Filtros de Búsqueda")
    
    # Buscador central
    busqueda = st.text_input("🔍 Ingrese Nombre de la Sustancia o Número CAS:", placeholder="Ej: Acetona o 67-64-1")
    
    # Filtro opcional por laboratorio en el sidebar
    lab_filter = st.sidebar.multiselect("Filtrar por Laboratorios específicos:", options=df_maestro['Ubicación Actual'].unique())

    # Aplicar filtros
    df_final = df_maestro.copy()
    
    if busqueda:
        df_final = df_final[
            df_final['Nombre'].str.contains(busqueda, case=False, na=False) | 
            df_final['CAS'].str.contains(busqueda, case=False, na=False)
        ]
    
    if lab_filter:
        df_final = df_final[df_final['Ubicación Actual'].isin(lab_filter)]

    # Mostrar resultados
    st.subheader(f"Resultados encontrados: {len(df_final)}")
    st.dataframe(df_final, use_container_width=True, hide_index=True)

    # 6. Análisis de Seguridad con IA
    if not df_final.empty and ia_activa:
        st.divider()
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("🛡️ Consultar Seguridad")
            sustancia_sel = st.selectbox("Seleccione para analizar:", df_final['Nombre'].unique())
            if st.button("Explicar con IA", type="primary"):
                with st.spinner("Consultando protocolos..."):
                    prompt = f"""
                    Como experto en seguridad química, analiza la sustancia: {sustancia_sel}.
                    Detalla: 1. Peligros GHS. 2. EPP necesario. 3. Qué laboratorios suelen usarla y para qué.
                    Responde de forma ejecutiva para un entorno universitario.
                    """
                    res = model.generate_content(prompt)
                    st.session_state['res_ia'] = res.text

        with col2:
            if 'res_ia' in st.session_state:
                st.info(st.session_state['res_ia'])
else:
    st.warning("No se encontraron datos. Verifica las URLs y permisos de Google Sheets.")

