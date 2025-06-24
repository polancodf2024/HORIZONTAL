import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import paramiko
import io
import os

# Configuración inicial
st.set_page_config(
    page_title="Gestión Hospitalaria",
    page_icon="🏥",
    layout="wide"
)

def cargar_configuracion():
    """Carga la configuración desde secrets.toml"""
    return {
        'sftp': {
            'host': st.secrets["sftp"]["host"],
            'user': st.secrets["sftp"]["user"],
            'password': st.secrets["sftp"]["password"],
            'port': st.secrets["sftp"]["port"],
            'remote_dir': st.secrets["sftp"]["dir"]
        },
        'archivos': {
            'enfermeras': st.secrets["archivos"]["enfermeras"],
            'transferencias': st.secrets["archivos"]["transferencias"],
            'pacientes': st.secrets["archivos"]["pacientes"],
            'servicios': st.secrets["archivos"]["servicios"]
        }
    }

def conectar_sftp():
    """Establece conexión SFTP"""
    transport = paramiko.Transport((config['sftp']['host'], config['sftp']['port']))
    transport.connect(username=config['sftp']['user'], password=config['sftp']['password'])
    return paramiko.SFTPClient.from_transport(transport)

def leer_archivo_remoto(nombre_archivo):
    """Lee un archivo directamente del servidor remoto"""
    try:
        with conectar_sftp() as sftp:
            remote_path = f"{config['sftp']['remote_dir']}/{config['archivos'][nombre_archivo]}"
            with sftp.file(remote_path, 'r') as remote_file:
                return pd.read_csv(io.StringIO(remote_file.read().decode('utf-8')))
    except Exception as e:
        st.error(f"Error al leer {nombre_archivo} del servidor: {str(e)}")
        return None

def guardar_archivo_remoto(df, nombre_archivo):
    """Guarda un archivo directamente en el servidor remoto"""
    try:
        with conectar_sftp() as sftp:
            remote_path = f"{config['sftp']['remote_dir']}/{config['archivos'][nombre_archivo]}"
            with sftp.file(remote_path, 'w') as remote_file:
                remote_file.write(df.to_csv(index=False))
        return True
    except Exception as e:
        st.error(f"Error al guardar {nombre_archivo} en el servidor: {str(e)}")
        return False

def inicializar_datos_remotos():
    """Inicializa archivos en el servidor remoto si no existen"""
    try:
        with conectar_sftp() as sftp:
            # Verificar y crear archivo de servicios
            servicios_path = f"{config['sftp']['remote_dir']}/{config['archivos']['servicios']}"
            try:
                sftp.stat(servicios_path)
            except FileNotFoundError:
                df = pd.DataFrame({
                    'Servicio': ['Urgencias', 'UCIC', 'Pediatría', 'Cirugía'],
                    'Camas_Utiles': [30, 20, 25, 15],
                    'Turno_Actual': ['Mañana', 'Mañana', 'Mañana', 'Mañana']
                })
                guardar_archivo_remoto(df, 'servicios')

            # Verificar y crear archivo de enfermeras
            enfermeras_path = f"{config['sftp']['remote_dir']}/{config['archivos']['enfermeras']}"
            try:
                sftp.stat(enfermeras_path)
            except FileNotFoundError:
                df = pd.DataFrame({
                    'ID': list(range(1001, 1017)),
                    'Nombre': ['Ana Pérez', 'Luis Gómez', 'Marta Ríos', 'Carlos López', 
                              'Sofía Martínez', 'Jorge Díaz', 'María Sánchez', 'Pedro Ruiz',
                              'Laura Fernández', 'David Jiménez', 'Elena Castro', 'Pablo Ortega',
                              'Isabel Mendoza', 'Andrés Navarro', 'Carmen Reyes', 'Ricardo Silva'],
                    'Tipo': ['Especialista', 'General', 'General', 'Especialista']*4,
                    'Servicio': ['Urgencias']*4 + ['UCIC']*4 + ['Pediatría']*4 + ['Cirugía']*4,
                    'Turno': ['Mañana', 'Tarde', 'Noche', 'Mañana']*4,
                    'Disponible': [True, True, False, True]*4
                })
                guardar_archivo_remoto(df, 'enfermeras')

            # Verificar y crear archivo de pacientes
            pacientes_path = f"{config['sftp']['remote_dir']}/{config['archivos']['pacientes']}"
            try:
                sftp.stat(pacientes_path)
            except FileNotFoundError:
                df = pd.DataFrame({
                    'Servicio': ['Urgencias', 'UCIC', 'Pediatría', 'Cirugía'],
                    'Pacientes_Actuales': [25, 18, 20, 12],
                    'Pacientes_Esperados': [8, 5, 3, 2],
                    'Prioridad': ['Alta', 'Alta', 'Media', 'Baja']
                })
                guardar_archivo_remoto(df, 'pacientes')

            # Verificar y crear archivo de transferencias
            transferencias_path = f"{config['sftp']['remote_dir']}/{config['archivos']['transferencias']}"
            try:
                sftp.stat(transferencias_path)
            except FileNotFoundError:
                df = pd.DataFrame(columns=[
                    'ID_Enfermera', 'Nombre_Enfermera', 'Servicio_Origen', 
                    'Servicio_Destino', 'Password_Cedente', 'Password_Aceptante',
                    'Estado', 'Fecha_Oferta', 'Fecha_Aceptacion'
                ])
                guardar_archivo_remoto(df, 'transferencias')
                
        return True
    except Exception as e:
        st.error(f"Error al inicializar datos remotos: {str(e)}")
        return False

@st.cache_data(ttl=10, max_entries=1)
def cargar_datos():
    """Carga todos los datos directamente del servidor remoto"""
    try:
        servicios = leer_archivo_remoto('servicios')
        enfermeras = leer_archivo_remoto('enfermeras')
        pacientes = leer_archivo_remoto('pacientes')
        transferencias = leer_archivo_remoto('transferencias')
        
        if servicios is None or enfermeras is None or pacientes is None or transferencias is None:
            raise Exception("Error al cargar uno o más archivos")
            
        enfermeras['Disponible'] = enfermeras['Disponible'].astype(bool)
        
        # Asegurar columnas en transferencias
        required_cols = ['ID_Enfermera', 'Nombre_Enfermera', 'Servicio_Origen', 
                        'Servicio_Destino', 'Estado']
        for col in required_cols:
            if col not in transferencias.columns:
                transferencias[col] = None
        
        transferencias['Fecha_Oferta'] = pd.to_datetime(transferencias['Fecha_Oferta'], errors='coerce')
        transferencias['Fecha_Aceptacion'] = pd.to_datetime(transferencias['Fecha_Aceptacion'], errors='coerce')
        
        return servicios, enfermeras, pacientes, transferencias
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        if inicializar_datos_remotos():
            return cargar_datos()
        else:
            st.stop()

def guardar_datos(servicios, enfermeras, pacientes, transferencias):
    """Guarda todos los datos en el servidor remoto"""
    try:
        if not all([
            guardar_archivo_remoto(servicios, 'servicios'),
            guardar_archivo_remoto(enfermeras, 'enfermeras'),
            guardar_archivo_remoto(pacientes, 'pacientes'),
            guardar_archivo_remoto(transferencias, 'transferencias')
        ]):
            raise Exception("Error al guardar uno o más archivos")
            
        cargar_datos.clear()
        st.success("Datos guardados correctamente en el servidor remoto")
        return True
    except Exception as e:
        st.error(f"Error al guardar datos: {str(e)}")
        return False

def mostrar_panel_principal():
    """Muestra el panel principal"""
    servicios, enfermeras, pacientes, _ = cargar_datos()
    
    st.title("📊 Panel Principal")
    cols = st.columns(3)
    cols[0].metric("Total Camas", servicios['Camas_Utiles'].sum())
    cols[1].metric("Total Pacientes", pacientes['Pacientes_Actuales'].sum())
    cols[2].metric("Total Enfermeras", len(enfermeras))
    
    st.subheader("Ocupación por Servicio")
    ocupacion = servicios.merge(pacientes, on='Servicio')
    ocupacion['% Ocupación'] = (ocupacion['Pacientes_Actuales'] / ocupacion['Camas_Utiles'] * 100).round(1)
    st.dataframe(
        ocupacion[['Servicio', 'Camas_Utiles', 'Pacientes_Actuales', '% Ocupación']]
        .style.background_gradient(cmap='YlOrRd', subset=['% Ocupación'])
    )

def mostrar_transferencias():
    """Interfaz para gestionar transferencias"""
    st.title("🔄 Transferencia de Enfermeras")
    
    if st.button("🔄 Actualizar Datos"):
        cargar_datos.clear()
        st.rerun()
    
    servicios, enfermeras, _, transferencias = cargar_datos()
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ofrecer Enfermera")
        with st.form("form_cedente", clear_on_submit=True):
            servicio_origen = st.selectbox("Servicio origen:", servicios['Servicio'].unique())
            turno = servicios.loc[servicios['Servicio'] == servicio_origen, 'Turno_Actual'].values[0]
            
            disponibles = enfermeras[
                (enfermeras['Servicio'] == servicio_origen) & 
                (enfermeras['Turno'] == turno) &
                enfermeras['Disponible']
            ]
            
            if not disponibles.empty:
                enfermera = st.selectbox(
                    "Enfermera:",
                    disponibles.apply(lambda x: f"{x['ID']} - {x['Nombre']}", axis=1)
                )
                servicio_destino = st.selectbox(
                    "Servicio destino:",
                    [s for s in servicios['Servicio'].unique() if s != servicio_origen]
                )
                password = st.text_input("Contraseña:", type="password")
                
                if st.form_submit_button("📤 Ofrecer"):
                    if password == "1234":
                        id_enfermera = int(enfermera.split(" - ")[0])
                        nueva = pd.DataFrame([{
                            'ID_Enfermera': id_enfermera,
                            'Nombre_Enfermera': enfermeras.loc[enfermeras['ID'] == id_enfermera, 'Nombre'].values[0],
                            'Servicio_Origen': servicio_origen,
                            'Servicio_Destino': servicio_destino,
                            'Password_Cedente': password,
                            'Estado': "Pendiente",
                            'Fecha_Oferta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        
                        # Actualizar y guardar
                        transferencias = pd.concat([transferencias, nueva], ignore_index=True)
                        if guardar_datos(servicios, enfermeras, pd.DataFrame(), transferencias):
                            st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
            else:
                st.warning(f"No hay enfermeras disponibles en {servicio_origen} (Turno {turno})")
                st.form_submit_button("Actualizar", disabled=True)

    with col2:
        st.subheader("Aceptar Transferencia")
        pendientes = transferencias[transferencias['Estado'] == "Pendiente"]
        
        if not pendientes.empty:
            with st.form("form_aceptante", clear_on_submit=True):
                transf = st.selectbox(
                    "Transferencias:",
                    pendientes.apply(lambda x: f"{x['Nombre_Enfermera']} de {x['Servicio_Origen']} a {x['Servicio_Destino']}", axis=1)
                )
                password = st.text_input("Contraseña:", type="password", key="pass_aceptante")
                
                if st.form_submit_button("✅ Aceptar"):
                    if password == "1234":
                        idx = pendientes.index[
                            pendientes.apply(
                                lambda x: f"{x['Nombre_Enfermera']} de {x['Servicio_Origen']} a {x['Servicio_Destino']}",
                                axis=1
                            ) == transf
                        ][0]
                        
                        # Actualizar transferencia
                        transferencias.at[idx, 'Estado'] = "Aceptada"
                        transferencias.at[idx, 'Password_Aceptante'] = password
                        transferencias.at[idx, 'Fecha_Aceptacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Actualizar enfermera
                        id_enfermera = transferencias.at[idx, 'ID_Enfermera']
                        enfermeras.loc[enfermeras['ID'] == id_enfermera, 'Servicio'] = transferencias.at[idx, 'Servicio_Destino']
                        
                        # Guardar cambios
                        if guardar_datos(servicios, enfermeras, pd.DataFrame(), transferencias):
                            st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
        else:
            st.info("No hay transferencias pendientes")
        
        st.subheader("Historial")
        if not transferencias.empty:
            st.dataframe(
                transferencias.sort_values('Fecha_Oferta', ascending=False)
                .drop(columns=['Password_Cedente', 'Password_Aceptante'])
                .style.apply(lambda x: ['background: lightgreen' if x['Estado'] == 'Aceptada' else 'background: lightyellow' for _ in x], axis=1)
            )

def main():
    """Función principal de la aplicación"""
    global config
    
    # Verificar secrets.toml
    secrets_path = Path(".streamlit/secrets.toml")
    if not secrets_path.exists():
        st.error("ERROR: No se encontró .streamlit/secrets.toml")
        st.stop()
    
    # Cargar configuración
    try:
        config = cargar_configuracion()
    except Exception as e:
        st.error(f"Error en configuración: {str(e)}")
        st.stop()
    
    # Inicializar datos remotos si es necesario
    if not inicializar_datos_remotos():
        st.error("No se pudieron inicializar los datos remotos")
        st.stop()
    
    # Menú de navegación
    pagina = st.sidebar.selectbox(
        "Seleccione página:", 
        ["Panel Principal", "Transferencia de Enfermeras"]
    )
    
    if pagina == "Panel Principal":
        mostrar_panel_principal()
    else:
        mostrar_transferencias()

if __name__ == "__main__":
    main()
