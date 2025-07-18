import streamlit as st
from PIL import Image
import datetime
import random
import string
import time
import os
from io import BytesIO

# Configuración inicial
def configurar_pagina():
    st.set_page_config(
        page_title="Escuela de Enfermería - Sistema Integral",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def cargar_estilos():
    st.markdown("""
    <style>
    :root {
        --color-primario: #003366;
        --color-secundario: #e74c3c;
        --color-exito: #28a745;
        --color-info: #17a2b8;
    }
    
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #333;
        line-height: 1.6;
    }
    
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    
    .sidebar-header {
        text-align: center;
        padding: 1rem;
        border-bottom: 1px solid #dee2e6;
    }
    
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #f5f9ff 0%, #e1ebfa 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .programa-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid var(--color-primario);
        transition: all 0.3s;
    }
    
    .programa-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.1);
    }
    
    .badge {
        display: inline-block;
        padding: 0.35em 0.65em;
        font-size: 0.75em;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 0.25rem;
    }
    
    .badge-primary {
        color: #fff;
        background-color: var(--color-primario);
    }
    
    .badge-secondary {
        color: #fff;
        background-color: #6c757d;
    }
    
    .badge-success {
        color: #fff;
        background-color: var(--color-exito);
    }
    
    .form-section {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    }
    
    .required-field::after {
        content: " *";
        color: var(--color-secundario);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)

# Funciones auxiliares
def generar_matricula():
    return 'MAT-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def validar_email(email):
    return '@' in email and '.' in email.split('@')[-1]

# Funciones principales
def mostrar_header():
    st.markdown("""
    <div class="main-header animate-fade">
        <h1>Escuela de Enfermería</h1>
        <h1>Instituto Nacional de Cardiología Ignacio Chávez</h1>
        <p class="lead">Formando profesionales de excelencia en el área de la salud</p>
    </div>
    """, unsafe_allow_html=True)

def mostrar_sidebar():
    with st.sidebar:
        try:
            logo = Image.open('escudo_COLOR.jpg')
            st.image(logo, use_container_width=True)
        except FileNotFoundError:
            st.warning("Logo no encontrado")
        
        st.markdown('<div class="sidebar-header"><h3>Menú Principal</h3></div>', unsafe_allow_html=True)
        
        if st.button("🏫 Oferta Educativa"):
            st.session_state.seccion_actual = "Oferta Educativa"
            st.rerun()
        
        if st.button("📝 Inscripción"):
            st.session_state.seccion_actual = "Inscripción"
            st.rerun()
        
        if st.button("📄 Documentación"):
            st.session_state.seccion_actual = "Documentación"
            st.rerun()
        
        if st.button("💳 Pagos"):
            st.session_state.seccion_actual = "Pagos"
            st.rerun()
        
        if st.button("📱 Contacto"):
            st.session_state.seccion_actual = "Contacto"
            st.rerun()

def mostrar_oferta_educativa():
    st.markdown("""
    <div class="animate-fade">
        <h2>Oferta Educativa 2025-2026</h2>
        <p>Explora nuestros programas académicos y encuentra el que mejor se adapte a tus metas profesionales.</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Licenciaturas", "Especialidades", "Maestrías", "Diplomados y Cursos"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="programa-card">
                <h3>Licenciatura en Enfermería</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">
                    <span class="badge badge-primary">4 años</span>
                    <span class="badge badge-secondary">Presencial</span>
                    <span class="badge badge-success">RVOE: ESL-2025-001</span>
                </div>
                <p>Formación integral de enfermeros generales con competencias para el cuidado de la salud en diferentes contextos.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Inscribirme", key="insc_lic1"):
                st.session_state.seccion_actual = "Inscripción"
                st.session_state.programa_seleccionado = "Licenciatura en Enfermería"
                st.rerun()
        
        with col2:
            st.markdown("""
            <div class="programa-card">
                <h3>Licenciatura en Enfermería Obstétrica</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">
                    <span class="badge badge-primary">4 años</span>
                    <span class="badge badge-secondary">Presencial</span>
                    <span class="badge badge-success">RVOE: ESL-2025-002</span>
                </div>
                <p>Especialización en el área de ginecología y obstetricia para atención durante el embarazo, parto y puerperio.</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Inscribirme", key="insc_lic2"):
                st.session_state.seccion_actual = "Inscripción"
                st.session_state.programa_seleccionado = "Licenciatura en Enfermería Obstétrica"
                st.rerun()
    
    with tab2:
        cols = st.columns(3)
        especialidades = [
            {
                "nombre": "Enfermería Cardiovascular",
                "duracion": "2 años",
                "modalidad": "Semipresencial",
                "desc": "Cuidado de pacientes con patologías cardiovasculares en unidades de terapia intensiva."
            },
            {
                "nombre": "Enfermería Nefrológica",
                "duracion": "2 años",
                "modalidad": "Semipresencial",
                "desc": "Especialización en el cuidado de pacientes con enfermedad renal crónica y aguda."
            },
            {
                "nombre": "Enfermería Pediátrica",
                "duracion": "2 años",
                "modalidad": "Presencial",
                "desc": "Atención especializada para pacientes neonatales, infantiles y adolescentes."
            }
        ]
        
        for i, esp in enumerate(especialidades):
            with cols[i]:
                st.markdown(f"""
                <div class="programa-card">
                    <h3>{esp['nombre']}</h3>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">
                        <span class="badge badge-primary">{esp['duracion']}</span>
                        <span class="badge badge-secondary">{esp['modalidad']}</span>
                        <span class="badge badge-success">Certificación CONACYT</span>
                    </div>
                    <p>{esp['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Inscribirme {i+1}", key=f"insc_esp{i}"):
                    st.session_state.seccion_actual = "Inscripción"
                    st.session_state.programa_seleccionado = f"Especialidad en {esp['nombre']}"
                    st.rerun()
    
    with tab3:
        st.markdown("""
        <div class="programa-card">
            <h3>Maestría en Administración de Servicios de Salud</h3>
            <div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">
                <span class="badge badge-primary">2 años</span>
                <span class="badge badge-secondary">En línea</span>
                <span class="badge badge-success">Grado académico</span>
            </div>
            <p>Formación en gestión y liderazgo para directivos de instituciones y servicios de salud.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Inscribirme", key="insc_maes"):
            st.session_state.seccion_actual = "Inscripción"
            st.session_state.programa_seleccionado = "Maestría en Administración de Servicios de Salud"
            st.rerun()
    
    with tab4:
        cursos = [
            {
                "nombre": "Diplomado en Cardiología",
                "duracion": "6 meses",
                "modalidad": "En línea",
                "desc": "Actualización en el manejo de pacientes con patologías cardiovasculares frecuentes."
            },
            {
                "nombre": "Curso de RCP Avanzado",
                "duracion": "3 meses",
                "modalidad": "Presencial",
                "desc": "Certificación en reanimación cardiopulmonar según estándares internacionales."
            }
        ]
        
        for i, curso in enumerate(cursos):
            st.markdown(f"""
            <div class="programa-card">
                <h3>{curso['nombre']}</h3>
                <div style="display: flex; gap: 10px; flex-wrap: wrap; margin: 10px 0;">
                    <span class="badge badge-primary">{curso['duracion']}</span>
                    <span class="badge badge-secondary">{curso['modalidad']}</span>
                    <span class="badge badge-success">Certificación</span>
                </div>
                <p>{curso['desc']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Inscribirme {i+1}", key=f"insc_curso{i}"):
                st.session_state.seccion_actual = "Inscripción"
                st.session_state.programa_seleccionado = curso['nombre']
                st.rerun()

def mostrar_inscripcion():
    st.markdown("""
    <div class="animate-fade">
        <h2>Formulario de Inscripción</h2>
        <p>Completa tus datos personales y sube los documentos requeridos para iniciar tu proceso de admisión.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'datos_inscripcion' not in st.session_state:
        st.session_state.datos_inscripcion = {
            'matricula': generar_matricula(),
            'programa': st.session_state.get('programa_seleccionado', ''),
            'nombre_completo': '',
            'fecha_nacimiento': None,
            'genero': '',
            'email': '',
            'telefono': '',
            'documentos': []
        }
    
    with st.form("form_inscripcion"):
        st.markdown(f"""
        <div style="background-color: #e9f7ff; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
            <h4>Número de Matrícula: <strong>{st.session_state.datos_inscripcion['matricula']}</strong></h4>
        </div>
        """, unsafe_allow_html=True)
        
        programas = [
            "Licenciatura en Enfermería",
            "Licenciatura en Enfermería Obstétrica",
            "Especialidad en Enfermería Cardiovascular",
            "Especialidad en Enfermería Nefrológica",
            "Especialidad en Enfermería Pediátrica",
            "Maestría en Administración de Servicios de Salud",
            "Diplomado en Cardiología",
            "Curso de RCP Avanzado"
        ]
        
        st.session_state.datos_inscripcion['programa'] = st.selectbox(
            "Programa al que desea inscribirse:",
            programas,
            index=programas.index(st.session_state.datos_inscripcion['programa']) if st.session_state.datos_inscripcion['programa'] in programas else 0
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.session_state.datos_inscripcion['nombre_completo'] = st.text_input(
                "Nombre completo:",
                value=st.session_state.datos_inscripcion['nombre_completo']
            )
            
            # Corregido: Manejo correcto de fechas (datetime.date vs string)
            fecha_actual = st.session_state.datos_inscripcion['fecha_nacimiento'] if st.session_state.datos_inscripcion['fecha_nacimiento'] else datetime.date(1990, 1, 1)
            st.session_state.datos_inscripcion['fecha_nacimiento'] = st.date_input(
                "Fecha de nacimiento:",
                value=fecha_actual
            )
            
            st.session_state.datos_inscripcion['genero'] = st.selectbox(
                "Género:",
                ["Masculino", "Femenino", "Otro", "Prefiero no decir"],
                index=["Masculino", "Femenino", "Otro", "Prefiero no decir"].index(st.session_state.datos_inscripcion['genero']) if st.session_state.datos_inscripcion['genero'] in ["Masculino", "Femenino", "Otro", "Prefiero no decir"] else 0
            )
        
        with col2:
            st.session_state.datos_inscripcion['email'] = st.text_input(
                "Correo electrónico:",
                value=st.session_state.datos_inscripcion['email']
            )
            
            st.session_state.datos_inscripcion['telefono'] = st.text_input(
                "Teléfono:",
                value=st.session_state.datos_inscripcion['telefono']
            )
        
        st.markdown("""
        <div style="margin: 2rem 0 1rem 0;">
            <h4>Documentos Requeridos</h4>
            <p>Sube los siguientes documentos en formato PDF:</p>
        </div>
        """, unsafe_allow_html=True)
        
        documentos_requeridos = {
            "Licenciatura": [
                "Acta de nacimiento (PDF)",
                "Certificado de bachillerato (PDF)",
                "CURP (PDF)",
                "Comprobante de domicilio (PDF)"
            ],
            "Especialidad": [
                "Título profesional (PDF)",
                "Cédula profesional (PDF)",
                "CV actualizado (PDF)",
                "Carta de motivos (PDF)"
            ],
            "Maestría": [
                "Título de licenciatura (PDF)",
                "CV actualizado (PDF)",
                "Carta de exposición de motivos (PDF)",
                "2 cartas de recomendación (PDF)"
            ],
            "Diplomado": [
                "Identificación oficial (PDF)",
                "Comprobante de estudios (PDF)",
                "Carta de exposición de motivos (PDF)"
            ]
        }
        
        if "Licenciatura" in st.session_state.datos_inscripcion['programa']:
            documentos = documentos_requeridos["Licenciatura"]
        elif "Especialidad" in st.session_state.datos_inscripcion['programa']:
            documentos = documentos_requeridos["Especialidad"]
        elif "Maestría" in st.session_state.datos_inscripcion['programa']:
            documentos = documentos_requeridos["Maestría"]
        else:
            documentos = documentos_requeridos["Diplomado"]
        
        documentos_subidos = []
        for i, doc in enumerate(documentos):
            archivo = st.file_uploader(
                f"Subir {doc}",
                type=['pdf'],
                key=f"doc_{i}"
            )
            if archivo:
                documentos_subidos.append({
                    "nombre": doc,
                    "archivo": archivo,
                    "tamaño": archivo.size,
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            guardar = st.form_submit_button("💾 Guardar Progreso")
        
        with col_btn2:
            enviar = st.form_submit_button("📤 Enviar Inscripción")
        
        if guardar or enviar:
            errores = []
            
            if not st.session_state.datos_inscripcion['nombre_completo']:
                errores.append("El nombre completo es obligatorio")
            
            if not st.session_state.datos_inscripcion['email']:
                errores.append("El correo electrónico es obligatorio")
            elif not validar_email(st.session_state.datos_inscripcion['email']):
                errores.append("Ingrese un correo electrónico válido")
            
            if enviar and len(documentos_subidos) < len(documentos):
                errores.append(f"Debe subir todos los documentos requeridos ({len(documentos)} en total)")
            
            if errores:
                for error in errores:
                    st.error(error)
            else:
                st.session_state.datos_inscripcion['documentos'] = documentos_subidos
                st.session_state.datos_inscripcion['fecha_inscripcion'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if enviar:
                    st.success("¡Inscripción enviada con éxito!")
                    st.balloons()
                    
                    st.markdown("### Resumen de tu inscripción")
                    st.json({
                        "Matrícula": st.session_state.datos_inscripcion['matricula'],
                        "Programa": st.session_state.datos_inscripcion['programa'],
                        "Nombre": st.session_state.datos_inscripcion['nombre_completo'],
                        "Documentos_subidos": [doc['nombre'] for doc in st.session_state.datos_inscripcion['documentos']],
                        "Fecha": st.session_state.datos_inscripcion['fecha_inscripcion']
                    })
                    
                    st.download_button(
                        label="📥 Descargar Comprobante",
                        data=BytesIO(str(st.session_state.datos_inscripcion).encode()),
                        file_name=f"comprobante_inscripcion_{st.session_state.datos_inscripcion['matricula']}.txt",
                        mime="text/plain"
                    )

def mostrar_documentacion():
    st.markdown("""
    <div class="animate-fade">
        <h2>Documentación Requerida</h2>
        <p>Revisa los documentos necesarios para completar tu inscripción.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'datos_inscripcion' not in st.session_state or not st.session_state.datos_inscripcion['programa']:
        st.warning("Por favor completa primero tus datos personales en la sección de Inscripción")
        return
    
    programas_docs = {
        "Licenciatura en Enfermería": [
            "Acta de nacimiento (original y copia)",
            "Certificado de bachillerato (original y copia)",
            "CURP (copia)",
            "4 fotografías tamaño infantil"
        ],
        "Especialidad en Enfermería Cardiovascular": [
            "Título profesional de licenciatura en enfermería (copia)",
            "Cédula profesional (copia)",
            "CV actualizado",
            "Carta de motivos"
        ],
        "Diplomado en Cardiología": [
            "Identificación oficial (copia)",
            "Comprobante de estudios",
            "Carta de exposición de motivos"
        ]
    }
    
    programa_actual = st.session_state.datos_inscripcion['programa']
    documentos = programas_docs.get(programa_actual, [
        "Identificación oficial (copia)",
        "Comprobante de estudios",
        "Comprobante de domicilio"
    ])
    
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px;">
        <h4>Documentos requeridos para: <strong>{programa_actual}</strong></h4>
        <ul style="margin-top: 1rem;">
    """, unsafe_allow_html=True)
    
    for doc in documentos:
        st.markdown(f"<li>{doc}</li>", unsafe_allow_html=True)
    
    st.markdown("""
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-top: 2rem;">
        <h4>Subir Documentos</h4>
        <p>Una vez que tengas todos los documentos requeridos, podrás subirlos en la sección de Inscripción.</p>
    </div>
    """, unsafe_allow_html=True)

def mostrar_pagos():
    st.markdown("""
    <div class="animate-fade">
        <h2>Información de Pagos</h2>
        <p>Detalles sobre costos y métodos de pago.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if 'datos_inscripcion' not in st.session_state or not st.session_state.datos_inscripcion['programa']:
        st.warning("Por favor completa primero tus datos personales en la sección de Inscripción")
        return
    
    programas_costos = {
        "Licenciatura en Enfermería": {
            "inscripción": "$2,500",
            "mensualidad": "$3,800",
            "duración": "8 semestres"
        },
        "Especialidad en Enfermería Cardiovascular": {
            "inscripción": "$3,200",
            "mensualidad": "$4,500",
            "duración": "4 semestres"
        },
        "Diplomado en Cardiología": {
            "inscripción": "$1,800",
            "costo_total": "$8,500",
            "duración": "6 meses"
        }
    }
    
    programa_actual = st.session_state.datos_inscripcion['programa']
    costos = programas_costos.get(programa_actual, {
        "inscripción": "$2,000",
        "mensualidad": "$3,500",
        "duración": "Consultar"
    })
    
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px;">
        <h4>Costos para: <strong>{programa_actual}</strong></h4>
        <div style="margin-top: 1rem;">
    """, unsafe_allow_html=True)
    
    for key, value in costos.items():
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid #eee;">
            <span style="font-weight: 500; text-transform: capitalize;">{key}:</span>
            <span style="font-weight: 700;">{value}</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-top: 2rem;">
        <h4>Métodos de Pago</h4>
        <p>Transferencia bancaria, tarjeta de crédito/débito o pago en efectivo en nuestras instalaciones.</p>
    </div>
    """, unsafe_allow_html=True)

def mostrar_contacto():
    st.markdown("""
    <div class="animate-fade">
        <h2>Contacto</h2>
        <p>¿Tienes dudas? Contáctanos a través de los siguientes medios.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; height: 100%;">
            <h4>Información de Contacto</h4>
            <div style="margin-top: 1rem;">
                <p>📧 <strong>Email:</strong> info@enfermeria.edu</p>
                <p>📞 <strong>Teléfono:</strong> (55) 1234 5678</p>
                <p>📱 <strong>WhatsApp:</strong> +52 1 55 9876 5432</p>
                <p>🏢 <strong>Dirección:</strong> Av. Universidad 123, Col. Centro, CDMX</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1.5rem; border-radius: 10px; height: 100%;">
            <h4>Horario de Atención</h4>
            <div style="margin-top: 1rem;">
                <p>🕘 <strong>Lunes a Viernes:</strong> 9:00 - 18:00 hrs</p>
                <p>🕙 <strong>Sábados:</strong> 10:00 - 14:00 hrs</p>
                <p>🚫 <strong>Domingos:</strong> Cerrado</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-top: 2rem;">
        <h4>Formulario de Contacto</h4>
        <p>Envíanos un mensaje directo y te responderemos a la brevedad.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("form_contacto"):
        nombre = st.text_input("Nombre completo")
        email = st.text_input("Correo electrónico")
        telefono = st.text_input("Teléfono (opcional)")
        mensaje = st.text_area("Mensaje", height=150)
        
        enviar = st.form_submit_button("Enviar Mensaje")
        
        if enviar:
            if not nombre or not email or not mensaje:
                st.error("Por favor completa los campos obligatorios")
            elif not validar_email(email):
                st.error("Ingresa un correo electrónico válido")
            else:
                st.success("Mensaje enviado correctamente. Nos pondremos en contacto contigo pronto.")

def main():
    configurar_pagina()
    cargar_estilos()
    
    if 'seccion_actual' not in st.session_state:
        st.session_state.seccion_actual = "Oferta Educativa"
    
    mostrar_sidebar()
    mostrar_header()
    
    opciones = {
        "Oferta Educativa": mostrar_oferta_educativa,
        "Inscripción": mostrar_inscripcion,
        "Documentación": mostrar_documentacion,
        "Pagos": mostrar_pagos,
        "Contacto": mostrar_contacto
    }
    
    opciones[st.session_state.seccion_actual]()

if __name__ == "__main__":
    main()
