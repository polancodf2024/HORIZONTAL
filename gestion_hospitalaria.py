import streamlit as st
import pandas as pd
from datetime import datetime
import paramiko
import io
import time
import logging

# Configuración inicial
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Gestión Hospitalaria - Enfermería",
    page_icon="🏥",
    layout="wide"
)

# Estado de la aplicación
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = False
if 'datos_cargados' not in st.session_state:
    st.session_state.datos_cargados = False
if 'ultima_actualizacion' not in st.session_state:
    st.session_state.ultima_actualizacion = None
if 'sftp_connection' not in st.session_state:
    st.session_state.sftp_connection = None
if 'config' not in st.session_state:
    st.session_state.config = None
if 'contenidos' not in st.session_state:
    st.session_state.contenidos = {
        'servicios': None,
        'enfermeras': None,
        'pacientes': None,
        'transferencias': None
    }
if 'datos_procesados' not in st.session_state:
    st.session_state.datos_procesados = {
        'servicios': None,
        'enfermeras': None,
        'pacientes': None
    }


def color_row(row):
    """Función para aplicar colores condicionales a las filas del DataFrame con lógica corregida"""
    if row['Diferencia'] > 0:  # Déficit (antes Superávit)
        intensity = min(1.0, row['Diferencia'] / 5.0)  # Normalizar a 0-1
        return [f'background-color: rgba(255, {int(200*(1-intensity))}, {int(200*(1-intensity))})'] * len(row)
    elif row['Diferencia'] < 0:  # Superávit (antes Déficit)
        intensity = min(1.0, abs(row['Diferencia']) / 5.0)  # Normalizar a 0-1
        return [f'background-color: rgba({int(200*(1-intensity))}, 255, {int(200*(1-intensity))})'] * len(row)
    else:  # Equilibrio
        return ['background-color: #ffffcc'] * len(row)

def cargar_configuracion():
    """Carga y valida la configuración desde secrets.toml"""
    try:
        config = {
            'sftp': {
                'host': st.secrets["sftp"]["host"],
                'user': st.secrets["sftp"]["user"],
                'password': st.secrets["sftp"]["password"],
                'port': int(st.secrets["sftp"]["port"]),
                'remote_dir': st.secrets["sftp"]["dir"]
            },
            'archivos': {
                'enfermeras': st.secrets["archivos"]["enfermeras"],
                'transferencias': st.secrets["archivos"]["transferencias"],
                'pacientes': st.secrets["archivos"]["pacientes"],
                'servicios': st.secrets["archivos"]["servicios"]
            }
        }
        st.session_state.config = config
        return config
    except Exception as e:
        logger.error(f"Error en configuración: {str(e)}")
        st.error(f"Error crítico en configuración: {str(e)}")
        st.stop()

def conectar_sftp():
    """Establece conexión SFTP con manejo de errores"""
    try:
        if st.session_state.sftp_connection:
            try:
                st.session_state.sftp_connection.listdir()
                return st.session_state.sftp_connection
            except:
                st.session_state.sftp_connection.close()

        logger.info("Estableciendo nueva conexión SFTP...")
        transport = paramiko.Transport((st.session_state.config['sftp']['host'], 
                                      st.session_state.config['sftp']['port']))
        transport.connect(username=st.session_state.config['sftp']['user'], 
                         password=st.session_state.config['sftp']['password'])

        sftp = paramiko.SFTPClient.from_transport(transport)
        st.session_state.sftp_connection = sftp
        return sftp
    except Exception as e:
        logger.error(f"Error en conexión SFTP: {str(e)}")
        st.error(f"Error de conexión: {str(e)}")
        st.session_state.sftp_connection = None
        return None

def leer_contenido_archivo(nombre_archivo):
    """Lee el contenido de un archivo remoto y lo devuelve como texto"""
    max_intentos = 3
    intento = 0
    
    while intento < max_intentos:
        try:
            sftp = conectar_sftp()
            if not sftp:
                raise ConnectionError("No se pudo establecer conexión SFTP")
                
            remote_path = f"{st.session_state.config['sftp']['remote_dir']}/{st.session_state.config['archivos'][nombre_archivo]}"
            
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                logger.error(f"Archivo no encontrado: {remote_path}")
                st.error(f"Archivo {nombre_archivo} no encontrado en el servidor")
                return None
                
            with sftp.file(remote_path, 'r') as remote_file:
                contenido = remote_file.read().decode('utf-8-sig')
                return contenido
                
        except Exception as e:
            intento += 1
            logger.warning(f"Intento {intento} fallido para {nombre_archivo}: {str(e)}")
            if intento < max_intentos:
                time.sleep(1)
            else:
                logger.error(f"Error al leer {nombre_archivo}: {str(e)}")
                st.error(f"Error al leer {nombre_archivo}: {str(e)}")
                return None

def procesar_datos(contenido, tipo):
    """Convierte el contenido en DataFrame adaptado a tus archivos"""
    try:
        if not contenido.strip():
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(contenido), sep=',')
        df.columns = df.columns.str.strip().str.replace(' ', '_')

        if tipo == 'enfermeras':
            if 'Disponible' in df.columns:
                df['Disponible'] = df['Disponible'].astype(bool)

        elif tipo == 'pacientes':
            if 'Servicio' in df.columns:
                return df.groupby('Servicio').size().reset_index(name='Pacientes_Actuales')
            else:
                st.error("El archivo de pacientes no tiene columna 'Servicio'")
                return pd.DataFrame()

        elif tipo == 'servicios':
            if 'Camas_Utiles' in df.columns:
                df['Camas_Utiles'] = pd.to_numeric(df['Camas_Utiles'], errors='coerce').fillna(0)
            if 'Enfermeras_Requeridas' not in df.columns:
                if 'Pacientes_Actuales' in df.columns:
                    df['Enfermeras_Requeridas'] = (df['Pacientes_Actuales'] / 5).apply(lambda x: max(1, round(x)))

        return df

    except Exception as e:
        logger.error(f"Error al procesar {tipo}: {str(e)}")
        return pd.DataFrame()

def cargar_datos_completos():
    """Carga y procesa todos los datos"""
    try:
        start_time = time.time()
        logger.info("Iniciando carga completa de datos...")

        servicios = leer_contenido_archivo('servicios')
        enfermeras = leer_contenido_archivo('enfermeras')
        pacientes = leer_contenido_archivo('pacientes')
        transferencias = leer_contenido_archivo('transferencias')

        if any(contenido is None for contenido in [servicios, enfermeras, pacientes]):
            raise ValueError("Uno o más archivos esenciales no se pudieron cargar")

        df_servicios = procesar_datos(servicios, 'servicios')
        df_enfermeras = procesar_datos(enfermeras, 'enfermeras')
        df_pacientes = procesar_datos(pacientes, 'pacientes')

        if df_pacientes.empty or 'Servicio' not in df_pacientes.columns:
            raise ValueError("El archivo de pacientes no contiene datos válidos")
        if df_enfermeras.empty or 'Servicio' not in df_enfermeras.columns:
            raise ValueError("El archivo de enfermeras no contiene datos válidos")
        if df_servicios.empty or 'Servicio' not in df_servicios.columns:
            raise ValueError("El archivo de servicios no contiene datos válidos")

        st.session_state.contenidos = {
            'servicios': servicios,
            'enfermeras': enfermeras,
            'pacientes': pacientes,
            'transferencias': transferencias
        }

        st.session_state.datos_procesados = {
            'servicios': df_servicios,
            'enfermeras': df_enfermeras,
            'pacientes': df_pacientes
        }

        st.session_state.datos_cargados = True
        st.session_state.ultima_actualizacion = datetime.now()

        logger.info(f"Datos cargados y procesados en {time.time() - start_time:.2f} segundos")
        return True

    except Exception as e:
        logger.error(f"Error en carga completa de datos: {str(e)}")
        st.error(f"Error al cargar datos: {str(e)}")
        st.session_state.datos_cargados = False
        return False

def calcular_ausentismo():
    """Calcula el déficit/superávit de enfermeras con lógica corregida"""
    try:
        enfermeras = st.session_state.datos_procesados['enfermeras']
        servicios = st.session_state.datos_procesados['servicios']
        pacientes = st.session_state.datos_procesados['pacientes']

        if enfermeras.empty or servicios.empty or pacientes.empty:
            st.warning("Datos insuficientes para calcular el ausentismo")
            return pd.DataFrame()

        # Calcular enfermeras por servicio
        enfermeras_por_servicio = enfermeras.groupby('Servicio').agg(
            Total_Enfermeras=('ID', 'count'),
            Enfermeras_Disponibles=('Disponible', 'sum')
        ).reset_index()

        enfermeras_por_servicio = enfermeras_por_servicio[enfermeras_por_servicio['Total_Enfermeras'] > 0]

        # Calcular requerimientos (1 enfermera cada 5 pacientes)
        ocupacion = pd.merge(servicios, pacientes, on='Servicio', how='left')
        ocupacion['Pacientes_Actuales'] = ocupacion['Pacientes_Actuales'].fillna(0)
        if 'Enfermeras_Requeridas' not in ocupacion.columns:
            ocupacion['Enfermeras_Requeridas'] = (ocupacion['Pacientes_Actuales'] / 5).apply(lambda x: max(1, round(x)))

        # Combinar resultados
        resultado = pd.merge(
            enfermeras_por_servicio,
            ocupacion[['Servicio', 'Enfermeras_Requeridas']],
            on='Servicio',
            how='left'
        ).fillna({'Enfermeras_Requeridas': 0})

        # Calcular diferencia (Enfermeras_Disponibles - Enfermeras_Requeridas)
        resultado['Diferencia'] = resultado['Enfermeras_Disponibles'] - resultado['Enfermeras_Requeridas']

        # Calcular porcentaje de cobertura CORREGIDO (Enfermeras_Disponibles / Enfermeras_Requeridas * 10)
        resultado['Cobertura'] = (resultado['Enfermeras_Disponibles'] / resultado['Enfermeras_Requeridas'] * 10).round(1)

        # Definir estado según la nueva lógica CORREGIDA
        resultado['Estado'] = resultado['Diferencia'].apply(
            lambda x: "Superávit" if x < 0 else ("Déficit" if x > 0 else "Equilibrio")
        )

        return resultado.sort_values('Diferencia')

    except Exception as e:
        logger.error(f"Error al calcular ausentismo: {str(e)}")
        st.error(f"Error en cálculo de ausentismo: {str(e)}")
        return pd.DataFrame()


def mostrar_panel_principal():
    """Muestra el panel principal de la aplicación"""
    st.title("🏥 Sistema de Gestión de Enfermería")
    st.write("""
    Bienvenido al sistema de gestión de enfermería. Esta herramienta permite:
    - Visualizar el déficit/superávit de enfermeras por servicio
    - Gestionar transferencias de personal entre servicios
    - Analizar la cobertura de personal
    """)
    
    if st.session_state.datos_cargados:
        st.success("✅ Datos cargados correctamente")
        st.write(f"Última actualización: {st.session_state.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("⚠️ Los datos no han sido cargados todavía")
        if st.button("Cargar Datos"):
            if cargar_datos_completos():
                st.rerun()

def mostrar_contenidos():
    """Muestra los contenidos de los archivos en pestañas separadas"""
    try:
        if not st.session_state.datos_cargados:
            with st.spinner("Cargando datos del hospital..."):
                if not cargar_datos_completos():
                    st.error("No se pudieron cargar los datos. Intente recargar la página.")
                    return
                st.rerun()
        
        st.title("📋 Contenido de Archivos Remotos")
        
        tabs = st.tabs(["Servicios", "Enfermeras", "Pacientes", "Transferencias"])
        for i, tipo in enumerate(['servicios', 'enfermeras', 'pacientes', 'transferencias']):
            with tabs[i]:
                st.subheader(f"📂 Archivo de {tipo.capitalize()}")
                if st.session_state.contenidos[tipo]:
                    st.text_area(
                        "Contenido", 
                        st.session_state.contenidos[tipo], 
                        height=300,
                        key=f"{tipo}_content"
                    )
                else:
                    st.warning("No hay contenido disponible")
        
        st.caption(f"Última actualización: {st.session_state.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"Error al mostrar contenidos: {str(e)}")
        st.error(f"Error al mostrar contenidos: {str(e)}")

def mostrar_panel_ausentismo():
    """Muestra el panel de análisis de cobertura de enfermeras"""
    try:
        if not st.session_state.datos_cargados:
            with st.spinner("Cargando datos del hospital..."):
                if not cargar_datos_completos():
                    st.error("No se pudieron cargar los datos. Intente recargar la página.")
                    return
                st.rerun()

        st.title("📊 Situación de Enfermería por Servicio")

        resultado = calcular_ausentismo()

        if resultado.empty:
            st.warning("No hay datos suficientes para mostrar el análisis")
            return

        # Mostrar métricas clave en columnas (CORREGIDO: TÍTULOS)
        col1, col2, col3 = st.columns(3)
        col1.metric("Servicios con Superávit", len(resultado[resultado['Estado'] == "Déficit"]))
        col2.metric("Servicios en Equilibrio", len(resultado[resultado['Estado'] == "Equilibrio"]))
        col3.metric("Servicios con Déficit", len(resultado[resultado['Estado'] == "Superávit"]))

        # Columnas a mostrar
        columns_to_show = ['Servicio', 'Total_Enfermeras', 'Enfermeras_Disponibles',
                           'Enfermeras_Requeridas', 'Diferencia', 'Cobertura', 'Estado']

        # Aplicar formato y estilos
        styled_df = (
            resultado[columns_to_show]
            .style
            .format({
                'Cobertura': '{:.1f}%',
                'Diferencia': '{:.0f}'
            })
            .apply(color_row, axis=1)
        )

        # Mostrar el DataFrame con estilo
        st.dataframe(styled_df)

        st.caption(f"Última actualización: {st.session_state.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        logger.error(f"Error en panel de ausentismo: {str(e)}")
        st.error(f"Error al mostrar el análisis: {str(e)}")

def guardar_archivo_remoto(df, nombre_archivo):
    """Guarda un DataFrame en el servidor remoto"""
    try:
        sftp = conectar_sftp()
        if not sftp:
            raise ConnectionError("No se pudo establecer conexión SFTP")
            
        remote_path = f"{st.session_state.config['sftp']['remote_dir']}/{st.session_state.config['archivos'][nombre_archivo]}"
        
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        with sftp.file(remote_path, 'w') as remote_file:
            remote_file.write(csv_content)
            
        logger.info(f"Archivo {nombre_archivo} guardado exitosamente")
        return True
        
    except Exception as e:
        logger.error(f"Error al guardar {nombre_archivo}: {str(e)}")
        st.error(f"Error al guardar {nombre_archivo}: {str(e)}")
        return False

def mostrar_transferencias():
    """Interfaz completa para transferencias con filtrado manual por servicio"""
    try:
        # Verificar carga de datos
        if not st.session_state.datos_cargados:
            with st.spinner("Cargando datos del hospital..."):
                if not cargar_datos_completos():
                    st.error("Error al cargar datos. Intente recargar la página.")
                    return
                st.rerun()

        st.title("🔄 Transferencia de Enfermeras")

        # Obtener datos
        servicios = st.session_state.datos_procesados['servicios']
        enfermeras = st.session_state.datos_procesados['enfermeras']
        transferencias_contenido = st.session_state.contenidos['transferencias']

        # Dividir en dos columnas
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📤 Ofrecer Enfermera")
            with st.form("form_servicio"):
                # 1. Selección de servicio de origen
                servicio_origen = st.selectbox(
                    "Seleccione servicio de origen:",
                    sorted(servicios['Servicio'].unique()),
                    key="servicio_origen_select"
                )

                # Botón para cargar enfermeras del servicio seleccionado
                if st.form_submit_button("🔃 Cargar Enfermeras del Servicio"):
                    st.session_state.servicio_seleccionado = servicio_origen
                    st.rerun()

            # Solo mostrar el resto del formulario si se ha seleccionado un servicio
            if hasattr(st.session_state, 'servicio_seleccionado'):
                servicio_actual = st.session_state.servicio_seleccionado
                st.markdown(f"**Servicio seleccionado:** {servicio_actual}")

                with st.form("form_oferta"):
                    # 2. Filtrar enfermeras del servicio seleccionado que estén disponibles
                    enfermeras_filtradas = enfermeras[
                        (enfermeras['Servicio'] == servicio_actual) &
                        (enfermeras['Disponible'] == True)
                    ].copy()

                    # 3. Mostrar TODAS las enfermeras disponibles del servicio seleccionado
                    if not enfermeras_filtradas.empty:
                        # Formato completo: "ID - Nombre - Servicio (Turno)"
                        opciones_enfermeras = [
                            f"{row['ID']} - {row['Nombre']} - {row['Servicio']} ({row['Turno']})"
                            for _, row in enfermeras_filtradas.iterrows()
                        ]

                        enfermera_seleccionada = st.selectbox(
                            "Enfermeras disponibles:",
                            opciones_enfermeras,
                            key=f"enfermeras_disponibles_{servicio_actual}"
                        )

                        # 4. Selección de servicio destino (excluyendo el origen)
                        servicios_destino = [s for s in sorted(servicios['Servicio'].unique())
                                          if s != servicio_actual]
                        servicio_destino = st.selectbox(
                            "Seleccione servicio destino:",
                            servicios_destino,
                            key="servicio_destino_select"
                        )

                        # 5. Confirmación con contraseña
                        password = st.text_input(
                            "Ingrese contraseña de confirmación:",
                            type="password",
                            key="password_oferta"
                        )

                        if st.form_submit_button("📤 Ofrecer Transferencia"):
                            if password == "1234":
                                # Extraer ID de la enfermera seleccionada
                                id_enfermera = int(enfermera_seleccionada.split(" - ")[0])

                                # Crear registro de transferencia
                                nueva_transferencia = {
                                    'ID_Enfermera': id_enfermera,
                                    'Nombre_Enfermera': enfermeras.loc[
                                        enfermeras['ID'] == id_enfermera, 'Nombre'].values[0],
                                    'Servicio_Origen': servicio_actual,
                                    'Servicio_Destino': servicio_destino,
                                    'Estado': "Pendiente",
                                    'Fecha_Oferta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }

                                # Cargar o crear dataframe de transferencias
                                if transferencias_contenido:
                                    try:
                                        df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                                    except:
                                        df_transferencias = pd.DataFrame(columns=[
                                            'ID_Enfermera', 'Nombre_Enfermera', 'Servicio_Origen',
                                            'Servicio_Destino', 'Estado', 'Fecha_Oferta'
                                        ])
                                else:
                                    df_transferencias = pd.DataFrame(columns=[
                                        'ID_Enfermera', 'Nombre_Enfermera', 'Servicio_Origen',
                                        'Servicio_Destino', 'Estado', 'Fecha_Oferta'
                                    ])

                                # Añadir nueva transferencia
                                df_transferencias = pd.concat(
                                    [df_transferencias, pd.DataFrame([nueva_transferencia])],
                                    ignore_index=True
                                )

                                # Guardar cambios
                                if guardar_archivo_remoto(df_transferencias, 'transferencias'):
                                    st.success("✅ Transferencia ofrecida exitosamente!")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error("❌ Contraseña incorrecta")
                    else:
                        st.warning(f"⚠️ No hay enfermeras disponibles en {servicio_actual}")

        with col2:
            st.subheader("✅ Aceptar Transferencia")

            if transferencias_contenido:
                try:
                    df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                    transferencias_pendientes = df_transferencias[df_transferencias['Estado'] == "Pendiente"]

                    if not transferencias_pendientes.empty:
                        with st.form("form_aceptacion"):
                            # Mostrar transferencias pendientes
                            transferencia_seleccionada = st.selectbox(
                                "Transferencias pendientes:",
                                transferencias_pendientes.apply(
                                    lambda x: f"{x['Nombre_Enfermera']} de {x['Servicio_Origen']} a {x['Servicio_Destino']}",
                                    axis=1
                                ),
                                key="transferencia_select"
                            )

                            # Confirmación con contraseña
                            password = st.text_input(
                                "Ingrese contraseña de confirmación:",
                                type="password",
                                key="password_aceptacion"
                            )

                            if st.form_submit_button("✅ Aceptar Transferencia"):
                                if password == "1234":
                                    # Procesar la transferencia seleccionada
                                    idx = transferencias_pendientes.index[
                                        transferencias_pendientes.apply(
                                            lambda x: f"{x['Nombre_Enfermera']} de {x['Servicio_Origen']} a {x['Servicio_Destino']}",
                                            axis=1
                                        ) == transferencia_seleccionada
                                    ][0]

                                    # Actualizar estado
                                    df_transferencias.at[idx, 'Estado'] = "Aceptada"
                                    df_transferencias.at[idx, 'Fecha_Aceptacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                    # Actualizar servicio de la enfermera
                                    id_enfermera = df_transferencias.at[idx, 'ID_Enfermera']
                                    enfermeras.loc[
                                        enfermeras['ID'] == id_enfermera,
                                        'Servicio'
                                    ] = df_transferencias.at[idx, 'Servicio_Destino']

                                    # Guardar cambios
                                    if (guardar_archivo_remoto(df_transferencias, 'transferencias') and
                                        guardar_archivo_remoto(enfermeras, 'enfermeras')):
                                        st.success("✅ Transferencia aceptada exitosamente!")
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.error("❌ Contraseña incorrecta")
                    else:
                        st.info("ℹ️ No hay transferencias pendientes")
                except Exception as e:
                    st.error(f"Error al leer transferencias: {str(e)}")

            # Mostrar historial reciente
            st.subheader("📜 Historial Reciente")
            if transferencias_contenido:
                try:
                    df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                    st.dataframe(
                        df_transferencias.sort_values('Fecha_Oferta', ascending=False).head(5),
                        height=250
                    )
                except:
                    st.info("No se pudo cargar el historial de transferencias")
            else:
                st.info("No hay historial de transferencias disponible")

    except Exception as e:
        logger.error(f"Error en transferencias: {str(e)}")
        st.error(f"Error crítico: {str(e)}")

def main():
    """Función principal de la aplicación"""
    if not st.session_state.app_initialized:
        cargar_configuracion()
        st.session_state.app_initialized = True

    st.sidebar.title("🏥 Gestión de Enfermería")
    st.sidebar.write(f"**Usuario:** {st.session_state.config['sftp']['user']}")

    pagina = st.sidebar.radio(
        "Navegación:",
        ["Panel Principal", "Contenidos", "Situación Enfermería", "Transferencias"],
        index=0
    )

    st.sidebar.markdown("---")
    st.sidebar.write("**Última actualización:**")
    if st.session_state.ultima_actualizacion:
        st.sidebar.write(st.session_state.ultima_actualizacion.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        st.sidebar.write("No disponible")

    if st.sidebar.button("🔄 Recargar Datos"):
        with st.spinner("Actualizando datos..."):
            if cargar_datos_completos():
                st.rerun()

    if pagina == "Panel Principal":
        mostrar_panel_principal()
    elif pagina == "Contenidos":
        mostrar_contenidos()
    elif pagina == "Situación Enfermería":
        mostrar_panel_ausentismo()
    elif pagina == "Transferencias":
        mostrar_transferencias()

    st.sidebar.markdown("---")
    st.sidebar.caption("Sistema de Gestión Hospitalaria v2.1")

if __name__ == "__main__":
    main()
