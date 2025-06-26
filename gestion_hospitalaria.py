import streamlit as st
import pandas as pd
from datetime import datetime
import paramiko
import io
import time
import logging
import socket
from typing import Optional, Dict, Any

# Configuración inicial
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de la página
st.set_page_config(
    page_title="Gestión Hospitalaria - Enfermería",
    page_icon="🏥",
    layout="wide"
)

class HospitalApp:
    def __init__(self):
        self._initialize_session_state()
        
    def _initialize_session_state(self):
        """Inicializa el estado de la aplicación"""
        defaults = {
            'app_initialized': False,
            'datos_cargados': False,
            'ultima_actualizacion': None,
            'sftp_connection': None,
            'config': None,
            'contenidos': {
                'servicios': None,
                'enfermeras': None,
                'pacientes': None,
                'transferencias': None,
                'usuarios': None
            },
            'datos_procesados': {
                'servicios': None,
                'enfermeras': None,
                'pacientes': None
            }
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def cargar_configuracion(self) -> bool:
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
                    'servicios': st.secrets["archivos"]["servicios"],
                    'usuarios': st.secrets["archivos"]["usuarios"]
                }
            }
            st.session_state.config = config
            return True
        except Exception as e:
            logger.error(f"Error en configuración: {str(e)}")
            st.error(f"Error crítico en configuración: {str(e)}")
            st.stop()
            return False

    def conectar_sftp(self):
        """Establece conexión SFTP con timeout"""
        try:
            if hasattr(st.session_state, 'sftp_connection') and st.session_state.sftp_connection:
                try:
                    st.session_state.sftp_connection.listdir()
                    return st.session_state.sftp_connection
                except:
                    if st.session_state.sftp_connection:
                        st.session_state.sftp_connection.close()
                    st.session_state.sftp_connection = None

            logger.info("Estableciendo nueva conexión SFTP...")
            transport = paramiko.Transport(
                (st.session_state.config['sftp']['host'], 
                st.session_state.config['sftp']['port'])
            )
            transport.connect(
                username=st.session_state.config['sftp']['user'], 
                password=st.session_state.config['sftp']['password']
            )
            
            transport.sock.settimeout(10)
            
            sftp = paramiko.SFTPClient.from_transport(transport)
            st.session_state.sftp_connection = sftp
            return sftp
        except Exception as e:
            logger.error(f"Error en conexión SFTP: {str(e)}")
            st.error(f"Error de conexión: {str(e)}")
            if 'sftp_connection' in st.session_state:
                st.session_state.sftp_connection = None
            return None

    def leer_contenido_archivo(self, nombre_archivo: str) -> Optional[str]:
        """Lee el contenido de un archivo remoto con timeout"""
        max_intentos = 3
        intento = 0
        
        while intento < max_intentos:
            try:
                sftp = self.conectar_sftp()  # <-- Nota cómo se llama ahora sin argumentos
                if not sftp:
                    raise ConnectionError("No se pudo establecer conexión SFTP")
                    
                transport = sftp.get_channel().get_transport()
                transport.sock.settimeout(10)
                
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
                    
            except socket.timeout:
                intento += 1
                logger.warning(f"Timeout en intento {intento} para {nombre_archivo}")
                if intento >= max_intentos:
                    st.error(f"Timeout al leer {nombre_archivo}. Verifique la conexión al servidor.")
                    return None
            except Exception as e:
                intento += 1
                logger.warning(f"Intento {intento} fallido para {nombre_archivo}: {str(e)}")
                if intento >= max_intentos:
                    logger.error(f"Error al leer {nombre_archivo}: {str(e)}")
                    st.error(f"Error al leer {nombre_archivo}: {str(e)}")
                    return None
                time.sleep(1)

    def procesar_datos(self, contenido: str, tipo: str) -> pd.DataFrame:
        """Convierte el contenido en DataFrame adaptado a los archivos"""
        try:
            if not contenido.strip():
                return pd.DataFrame()

            df = pd.read_csv(io.StringIO(contenido), sep=',')
            df.columns = df.columns.str.strip().str.replace(' ', '_')

            logger.info(f"Columnas en archivo {tipo}: {df.columns.tolist()}")

            if tipo == 'enfermeras':
                if 'Presente' in df.columns:
                    df['Presente'] = df['Presente'].astype(bool)
                else:
                    df['Presente'] = True

            elif tipo == 'servicios':
                columnas_reales = df.columns.tolist()
                logger.info(f"Columnas reales en servicios: {columnas_reales}")

                mapeo_columnas = {
                    'plantilla_manana': 'Plantilla_Manana',
                    'turno_manana': 'Turno_Manana',
                    'plantilla_tarde': 'Plantilla_Tarde',
                    'turno_tarde': 'Turno_Tarde',
                    'plantilla_noche': 'Plantilla_Noche',
                    'turno_noche': 'Turno_Noche'
                }

                for original, nuevo in mapeo_columnas.items():
                    if original in df.columns and nuevo not in df.columns:
                        df.rename(columns={original: nuevo}, inplace=True)

                required_columns = ['Plantilla_Manana', 'Turno_Manana',
                                   'Plantilla_Tarde', 'Turno_Tarde',
                                   'Plantilla_Noche', 'Turno_Noche']

                for col in required_columns:
                    if col not in df.columns:
                        st.error(f"Falta columna requerida: {col}")
                        return pd.DataFrame()

                for col in ['Plantilla_Manana', 'Plantilla_Tarde', 'Plantilla_Noche']:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            return df

        except Exception as e:
            logger.error(f"Error al procesar {tipo}: {str(e)}")
            return pd.DataFrame()

    def validar_credenciales(self, servicio: str, password: str) -> bool:
        """Valida las credenciales contra el archivo de usuarios"""
        try:
            if 'usuarios' not in st.session_state.contenidos or not st.session_state.contenidos['usuarios']:
                st.error("No se ha cargado el archivo de usuarios")
                return False
                
            df_usuarios = pd.read_csv(io.StringIO(st.session_state.contenidos['usuarios']))
            usuario_valido = df_usuarios[
                (df_usuarios['Servicio'] == servicio) & 
                (df_usuarios['Password'] == password)
            ]
            
            return not usuario_valido.empty
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            st.error(f"Error al validar credenciales: {str(e)}")
            return False

    def cargar_datos_completos(self) -> bool:
        """Carga y procesa todos los datos con forzado de recarga"""
        try:
            st.session_state.datos_cargados = False
            st.session_state.contenidos = {k: None for k in st.session_state.contenidos}
            st.session_state.datos_procesados = {k: None for k in st.session_state.datos_procesados}

            if not st.session_state.config:
                self.cargar_configuracion()

            archivos_esenciales = ['servicios', 'enfermeras', 'pacientes', 'usuarios']
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, archivo in enumerate(archivos_esenciales):
                status_text.text(f"Cargando {archivo}...")
                contenido = self.leer_contenido_archivo(archivo)
                if contenido is None:
                    raise ValueError(f"No se pudo cargar {archivo}")
                
                st.session_state.contenidos[archivo] = contenido
                if archivo in ['servicios', 'enfermeras', 'pacientes']:
                    st.session_state.datos_procesados[archivo] = self.procesar_datos(contenido, archivo)
                
                progress_bar.progress((i + 1) / len(archivos_esenciales))

            transferencias = self.leer_contenido_archivo('transferencias')
            if transferencias is not None:
                st.session_state.contenidos['transferencias'] = transferencias

            if (st.session_state.datos_procesados['enfermeras'] is None or 
                st.session_state.datos_procesados['servicios'] is None):
                raise ValueError("Datos esenciales no cargados correctamente")

            st.session_state.datos_cargados = True
            st.session_state.ultima_actualizacion = datetime.now()
            
            progress_bar.empty()
            status_text.success("✅ Datos cargados correctamente")
            return True

        except Exception as e:
            logger.error(f"Error en carga completa: {str(e)}")
            st.error(f"Error al cargar datos: {str(e)}")
            if 'progress_bar' in locals():
                progress_bar.empty()
            if 'status_text' in locals():
                status_text.error("❌ Error al cargar datos")
            return False

    def calcular_ausentismo(self) -> pd.DataFrame:
        """Calcula el ausentismo por servicio y turno"""
        try:
            enfermeras = st.session_state.datos_procesados['enfermeras']
            servicios = st.session_state.datos_procesados['servicios']

            if enfermeras.empty or servicios.empty:
                st.warning("Datos insuficientes para calcular el ausentismo")
                return pd.DataFrame()

            enfermeras = enfermeras[enfermeras['Presente'] == True].copy()
            enfermeras['Turno'] = enfermeras['Turno'].str.strip().str.upper()

            turno_map = {
                'MAÑANA': 'M', 'MANANA': 'M', 'AM': 'M', 'M': 'M',
                'TARDE': 'T', 'PM': 'T', 'T': 'T',
                'NOCHE': 'N', 'NOCTURNO': 'N', 'N': 'N'
            }
            enfermeras['Turno'] = enfermeras['Turno'].map(turno_map).fillna('')

            enfermeras_presentes = enfermeras.groupby(
                ['Servicio', 'Turno']).size().reset_index(name='Presentes')

            datos_ausentismo = []
            for _, servicio in servicios.iterrows():
                servicio_nombre = servicio['Servicio']

                plantillas = {
                    'M': int(servicio['Plantilla_Manana']),
                    'T': int(servicio['Plantilla_Tarde']),
                    'N': int(servicio['Plantilla_Noche'])
                }

                for turno_cod, turno_nombre in [('M', 'Mañana'), ('T', 'Tarde'), ('N', 'Noche')]:
                    presentes = enfermeras_presentes[
                        (enfermeras_presentes['Servicio'] == servicio_nombre) &
                        (enfermeras_presentes['Turno'] == turno_cod)
                    ]['Presentes'].sum()

                    datos_ausentismo.append({
                        'Servicio': servicio_nombre,
                        'Turno': turno_nombre,
                        'Plantilla': plantillas[turno_cod],
                        'Presentes': presentes,
                        'Ausentismo': plantillas[turno_cod] - presentes
                    })

            return pd.DataFrame(datos_ausentismo)

        except Exception as e:
            logger.error(f"Error al calcular ausentismo: {str(e)}")
            st.error(f"Error al calcular ausentismo: {str(e)}")
            return pd.DataFrame()

    def guardar_archivo_remoto(self, df: pd.DataFrame, nombre_archivo: str) -> bool:
        """Guarda un DataFrame en el servidor remoto"""
        try:
            sftp = self.conectar_sftp()
            if not sftp:
                raise ConnectionError("No se pudo establecer conexión SFTP")

            remote_path = f"{st.session_state.config['sftp']['remote_dir']}/{st.session_state.config['archivos'][nombre_archivo]}"

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()

            with sftp.file(remote_path, 'w') as remote_file:
                remote_file.write(csv_content)

            logger.info(f"Archivo {nombre_archivo} guardado exitosamente")

            if nombre_archivo == 'enfermeras':
                st.session_state.datos_procesados['enfermeras'] = df
                st.session_state.contenidos['enfermeras'] = csv_content
            elif nombre_archivo == 'transferencias':
                st.session_state.contenidos['transferencias'] = csv_content
            elif nombre_archivo == 'servicios':
                st.session_state.datos_procesados['servicios'] = df
                st.session_state.contenidos['servicios'] = csv_content

            return True

        except Exception as e:
            logger.error(f"Error al guardar {nombre_archivo}: {str(e)}")
            st.error(f"Error al guardar {nombre_archivo}: {str(e)}")
            return False

    def mostrar_panel_principal(self):
        """Muestra el panel principal de la aplicación"""
        st.title("🏥 Sistema de Gestión de Enfermería")
        st.write("""
        Bienvenido al sistema de gestión de enfermería. Esta herramienta permite:
        - Visualizar el ausentismo de enfermeras por servicio
        - Gestionar transferencias de personal entre servicios
        """)

        if st.session_state.datos_cargados:
            st.success("✅ Datos cargados correctamente")
            st.write(f"Última actualización: {st.session_state.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("⚠️ Los datos no han sido cargados todavía")
            if st.button("Cargar Datos"):
                if self.cargar_datos_completos():
                    st.rerun()

    def mostrar_contenidos(self):
        """Muestra los contenidos de los archivos en pestañas separadas"""
        try:
            if not st.session_state.datos_cargados:
                with st.spinner("Cargando datos del hospital..."):
                    if not self.cargar_datos_completos():
                        st.error("No se pudieron cargar los datos. Intente recargar la página.")
                        return
                    st.rerun()
            
            st.title("📋 Contenido de Archivos Remotos")
            
            tabs = st.tabs(["Servicios", "Enfermeras", "Pacientes", "Transferencias", "Usuarios"])
            for i, tipo in enumerate(['servicios', 'enfermeras', 'pacientes', 'transferencias', 'usuarios']):
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

    def mostrar_panel_ausentismo(self):
        """Muestra el panel de análisis de ausentismo"""
        try:
            if not st.session_state.datos_cargados:
                with st.spinner("Cargando datos del hospital..."):
                    if not self.cargar_datos_completos():
                        st.error("No se pudieron cargar los datos. Intente recargar la página.")
                        return
                    st.rerun()

            st.title("📊 Situación de Enfermería por Servicio y Turno")

            if st.button("🔄 Actualizar Datos"):
                with st.spinner("Recalculando..."):
                    st.session_state.datos_cargados = False
                    self.cargar_datos_completos()
                    st.rerun()

            resultado = self.calcular_ausentismo()

            if resultado.empty:
                st.warning("No hay datos suficientes para mostrar el análisis")
                return

            datos_mostrar = []
            servicios_unicos = resultado['Servicio'].unique()

            for servicio in servicios_unicos:
                fila = {'Servicio': servicio}
                for turno in ['Mañana', 'Tarde', 'Noche']:
                    datos_turno = resultado[(resultado['Servicio'] == servicio) &
                                          (resultado['Turno'] == turno)]
                    if not datos_turno.empty:
                        fila[f'Plantilla {turno}'] = datos_turno['Plantilla'].values[0]
                        fila[f'Presentes {turno}'] = datos_turno['Presentes'].values[0]
                datos_mostrar.append(fila)

            df_mostrar = pd.DataFrame(datos_mostrar).set_index('Servicio')

            def color_row(row):
                styles = []
                for turno in ['Mañana', 'Tarde', 'Noche']:
                    plantilla = row.get(f'Plantilla {turno}', 0)
                    presentes = row.get(f'Presentes {turno}', 0)
                    ausentismo = plantilla - presentes

                    if ausentismo > 0:
                        intensity = min(1.0, ausentismo / 5.0)
                        color = f'rgba(255, {int(200*(1-intensity))}, {int(200*(1-intensity))})'
                    else:
                        color = 'rgba(200, 255, 200)'

                    styles.extend([f'background-color: {color}'] * 2)

                return styles

            column_order = []
            for turno in ['Mañana', 'Tarde', 'Noche']:
                column_order.extend([f'Plantilla {turno}', f'Presentes {turno}'])

            st.dataframe(
                df_mostrar[column_order].style.apply(color_row, axis=1),
                height=min(400, 50 + len(df_mostrar) * 35),
                column_config={
                    f"Plantilla {turno}": st.column_config.NumberColumn(
                        f"Plantilla {turno}",
                        format="%d"
                    ) for turno in ['Mañana', 'Tarde', 'Noche']
                }
            )

            st.caption(f"Última actualización: {st.session_state.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            logger.error(f"Error en panel de ausentismo: {str(e)}")
            st.error(f"Error al mostrar análisis: {str(e)}")

    def mostrar_transferencias(self):
        """Interfaz completa para transferencias"""
        try:
            if not st.session_state.datos_cargados:
                with st.spinner("Cargando datos del hospital..."):
                    if not self.cargar_datos_completos():
                        st.error("Error al cargar datos. Intente recargar la página.")
                        return
                    st.rerun()

            st.title("🔄 Transferencia de Enfermeras")

            servicios = st.session_state.datos_procesados['servicios']
            enfermeras = st.session_state.datos_procesados['enfermeras']
            transferencias_contenido = st.session_state.contenidos['transferencias']

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📤 Ofrecer Enfermera")
                with st.form("form_servicio"):
                    servicio_origen = st.selectbox(
                        "Seleccione servicio de origen:",
                        sorted(servicios['Servicio'].unique()),
                        key="servicio_origen_select"
                    )

                    if st.form_submit_button("🔃 Cargar Enfermeras del Servicio"):
                        st.session_state.servicio_seleccionado = servicio_origen
                        st.rerun()

                if hasattr(st.session_state, 'servicio_seleccionado'):
                    servicio_actual = st.session_state.servicio_seleccionado
                    st.markdown(f"**Servicio seleccionado:** {servicio_actual}")

                    enfermeras_filtradas = enfermeras[
                        (enfermeras['Servicio'] == servicio_actual) &
                        (enfermeras['Presente'] == True) &
                        (enfermeras['Disponible'] == True)
                    ].copy()

                    if transferencias_contenido:
                        try:
                            df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                            df_transferencias = df_transferencias.rename(columns={
                                'Tumo_Origen': 'Turno_Origen',
                                'Tumo_Destino': 'Turno_Destino'
                            })
                            transferencias_pendientes = df_transferencias[df_transferencias['Estado'] == "Pendiente"]
                            enfermeras_en_transferencia = transferencias_pendientes['ID_Enfermera'].unique()
                            enfermeras_filtradas = enfermeras_filtradas[~enfermeras_filtradas['ID'].isin(enfermeras_en_transferencia)]
                        except Exception as e:
                            logger.warning(f"Error al leer transferencias: {str(e)}")

                    with st.form("form_oferta"):
                        if not enfermeras_filtradas.empty:
                            opciones_enfermeras = [
                                f"{row['ID']} - {row['Nombre']} ({row['Turno']})"
                                for _, row in enfermeras_filtradas.iterrows()
                            ]

                            enfermera_seleccionada = st.selectbox(
                                "Enfermeras disponibles:",
                                opciones_enfermeras,
                                key=f"enfermeras_disponibles_{servicio_actual}"
                            )

                            servicios_destino = [s for s in sorted(servicios['Servicio'].unique())
                                           if s != servicio_actual]
                            servicio_destino = st.selectbox(
                                "Seleccione servicio destino:",
                                servicios_destino,
                                key="servicio_destino_select"
                            )

                            turnos_destino = ['Mañana', 'Tarde', 'Noche']
                            turno_destino = st.selectbox(
                                "Seleccione turno destino:",
                                turnos_destino,
                                key="turno_destino_select"
                            )

                            password = st.text_input(
                                f"Contraseña para {servicio_actual}:",
                                type="password",
                                key="password_oferta"
                            )

                            if st.form_submit_button("📤 Ofrecer Transferencia"):
                                if self.validar_credenciales(servicio_actual, password):
                                    id_enfermera = int(enfermera_seleccionada.split(" - ")[0])
                                    enfermera_data = enfermeras[enfermeras['ID'] == id_enfermera].iloc[0]

                                    nueva_transferencia = {
                                        'ID_Enfermera': id_enfermera,
                                        'Nombre_Enfermera': enfermera_data['Nombre'],
                                        'Servicio_Origen': servicio_actual,
                                        'Turno_Origen': enfermera_data['Turno'],
                                        'Servicio_Destino': servicio_destino,
                                        'Turno_Destino': turno_destino,
                                        'Estado': "Pendiente",
                                        'Fecha_Oferta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    }

                                    if transferencias_contenido:
                                        try:
                                            df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                                            df_transferencias = df_transferencias.rename(columns={
                                                'Tumo_Origen': 'Turno_Origen',
                                                'Tumo_Destino': 'Turno_Destino'
                                            })
                                        except:
                                            df_transferencias = pd.DataFrame(columns=[
                                                'ID_Enfermera', 'Nombre_Enfermera', 'Servicio_Origen',
                                                'Turno_Origen', 'Servicio_Destino', 'Turno_Destino',
                                                'Estado', 'Fecha_Oferta'
                                            ])
                                    else:
                                        df_transferencias = pd.DataFrame(columns=[
                                            'ID_Enfermera', 'Nombre_Enfermera', 'Servicio_Origen',
                                            'Turno_Origen', 'Servicio_Destino', 'Turno_Destino',
                                            'Estado', 'Fecha_Oferta'
                                        ])

                                    df_transferencias = pd.concat(
                                        [df_transferencias, pd.DataFrame([nueva_transferencia])],
                                        ignore_index=True
                                    )

                                    if self.guardar_archivo_remoto(df_transferencias, 'transferencias'):
                                        st.success("✅ Transferencia ofrecida exitosamente!")
                                        time.sleep(1)
                                        st.rerun()
                                else:
                                    st.error("❌ Contraseña incorrecta para este servicio")
                        else:
                            st.warning(f"⚠️ No hay enfermeras disponibles en {servicio_actual}")

            with col2:
                st.subheader("✅ Aceptar Transferencia")

                if transferencias_contenido:
                    try:
                        df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                        df_transferencias = df_transferencias.rename(columns={
                            'Tumo_Origen': 'Turno_Origen',
                            'Tumo_Destino': 'Turno_Destino'
                        })

                        transferencias_pendientes = df_transferencias[df_transferencias['Estado'] == "Pendiente"]

                        if not transferencias_pendientes.empty:
                            with st.form("form_seleccion_transferencia"):
                                transferencia_seleccionada = st.selectbox(
                                    "Transferencias pendientes:",
                                    transferencias_pendientes.apply(
                                        lambda x: f"{x['Nombre_Enfermera']} ({x['Turno_Origen']}) de {x['Servicio_Origen']} a {x['Servicio_Destino']} ({x['Turno_Destino']})",
                                        axis=1
                                    ),
                                    key="transferencia_select"
                                )

                                if st.form_submit_button("🔍 Cargar Detalles"):
                                    st.session_state.transferencia_seleccionada = transferencia_seleccionada
                                    st.rerun()

                            if hasattr(st.session_state, 'transferencia_seleccionada'):
                                idx = transferencias_pendientes.index[
                                    transferencias_pendientes.apply(
                                        lambda x: f"{x['Nombre_Enfermera']} ({x['Turno_Origen']}) de {x['Servicio_Origen']} a {x['Servicio_Destino']} ({x['Turno_Destino']})",
                                        axis=1
                                    ) == st.session_state.transferencia_seleccionada
                                ][0]

                                transferencia = df_transferencias.iloc[idx]
                                servicio_destino = transferencia['Servicio_Destino']
                                turno_destino = transferencia['Turno_Destino']
                                id_enfermera = transferencia['ID_Enfermera']

                                with st.form("form_aceptacion"):
                                    st.markdown(f"**Transferencia seleccionada:** {st.session_state.transferencia_seleccionada}")

                                    password = st.text_input(
                                        f"Contraseña para {servicio_destino}:",
                                        type="password",
                                        key="password_aceptacion"
                                    )

                                    if st.form_submit_button("✅ Aceptar Transferencia"):
                                        if self.validar_credenciales(servicio_destino, password):
                                            df_transferencias.at[idx, 'Estado'] = "Aceptada"
                                            df_transferencias.at[idx, 'Fecha_Aceptacion'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                                            enfermeras.loc[
                                                enfermeras['ID'] == id_enfermera,
                                                ['Servicio', 'Turno']
                                            ] = [servicio_destino, turno_destino]

                                            if (self.guardar_archivo_remoto(df_transferencias, 'transferencias') and
                                                self.guardar_archivo_remoto(enfermeras, 'enfermeras')):
                                                with st.spinner("Actualizando datos..."):
                                                    st.session_state.datos_cargados = False
                                                    if self.cargar_datos_completos():
                                                        st.success("✅ Transferencia aceptada exitosamente!")
                                                        if hasattr(st.session_state, 'transferencia_seleccionada'):
                                                            del st.session_state.transferencia_seleccionada
                                                        time.sleep(1)
                                                        st.rerun()
                                        else:
                                            st.error("❌ Contraseña incorrecta para este servicio")
                    except Exception as e:
                        st.error(f"Error al procesar transferencias: {str(e)}")

                st.subheader("📜 Historial Reciente (Últimas 10 transferencias)")
                if transferencias_contenido:
                    try:
                        df_transferencias = pd.read_csv(io.StringIO(transferencias_contenido))
                        df_transferencias = df_transferencias.rename(columns={
                            'Tumo_Origen': 'Turno_Origen',
                            'Tumo_Destino': 'Turno_Destino'
                        })

                        required_cols = ['Fecha_Oferta', 'Servicio_Origen', 'Turno_Origen',
                                       'Servicio_Destino', 'Turno_Destino', 'Nombre_Enfermera', 'Estado']

                        if all(col in df_transferencias.columns for col in required_cols):
                            historial = df_transferencias[
                                df_transferencias['Estado'] == "Aceptada"
                            ].sort_values('Fecha_Oferta', ascending=False).head(10)

                            if not historial.empty:
                                st.dataframe(
                                    historial[required_cols].rename(columns={
                                        'Fecha_Oferta': 'Fecha',
                                        'Servicio_Origen': 'Origen',
                                        'Turno_Origen': 'Turno Origen',
                                        'Servicio_Destino': 'Destino',
                                        'Turno_Destino': 'Turno Destino',
                                        'Nombre_Enfermera': 'Enfermera'
                                    }),
                                    height=400,
                                    column_config={
                                        "Fecha": st.column_config.DatetimeColumn(
                                            "Fecha",
                                            format="YYYY-MM-DD HH:mm:ss"
                                        ),
                                        "Origen": "Servicio Origen",
                                        "Turno Origen": "Turno Origen",
                                        "Destino": "Servicio Destino",
                                        "Turno Destino": "Turno Destino",
                                        "Enfermera": "Enfermera Transferida",
                                        "Estado": "Estado"
                                    }
                                )
                            else:
                                st.info("No hay historial de transferencias completadas")
                        else:
                            st.error("El archivo de transferencias no tiene el formato correcto")
                            st.write("Columnas encontradas:", df_transferencias.columns.tolist())
                    except Exception as e:
                        st.error(f"Error al cargar historial: {str(e)}")
                else:
                    st.info("No hay datos de transferencias cargados")

        except Exception as e:
            logger.error(f"Error en transferencias: {str(e)}")
            st.error(f"Error crítico: {str(e)}")

    def run(self):
        """Función principal de la aplicación"""
        if not st.session_state.app_initialized:
            self.cargar_configuracion()
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
            st.sidebar.write(st.session_state.ultima_actualizacion.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            st.sidebar.write("No disponible")

        if st.sidebar.button("🔄 Recargar Datos"):
            with st.spinner("Actualizando datos..."):
                if self.cargar_datos_completos():
                    st.rerun()

        if pagina == "Panel Principal":
            self.mostrar_panel_principal()
        elif pagina == "Contenidos":
            self.mostrar_contenidos()
        elif pagina == "Situación Enfermería":
            self.mostrar_panel_ausentismo()
        elif pagina == "Transferencias":
            self.mostrar_transferencias()

        st.sidebar.markdown("---")
        st.sidebar.caption("Sistema de Gestión Hospitalaria v2.1")

if __name__ == "__main__":
    app = HospitalApp()
    app.run()
