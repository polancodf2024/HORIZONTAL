import streamlit as st
from datetime import datetime, time
import pandas as pd
import os
from PIL import Image
import tempfile

def setup_page():
    """Configura la página de Streamlit"""
    st.set_page_config(
        page_title="🚨 Reporte de Eventos Graves y Adversos",
        layout="wide",
        page_icon="❤️"
    )
    st.title("❤️‍🩹 Reporte de Eventos Adversos y Graves")

def show_event_context():
    """Muestra la sección de contexto del evento"""
    with st.expander("📌 Contexto del Evento", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_evento = st.date_input("📅 Fecha del evento", datetime.today())
            turno = st.radio("🕒 Turno", [
                "Matutino (6:00-14:00)", 
                "Vespertino (14:00-22:00)", 
                "Nocturno (22:00-6:00)"
            ], horizontal=True)
        with col2:
            ubicacion = st.selectbox("🏥 Área donde ocurrió", [
                "UCIC (Unidad Coronaria)", 
                "UCIN (Unidad Cardíaca Intensiva Neonatal)", 
                "Hemodinamia", 
                "Quirófano Cardiovascular", 
                "Hospitalización Cardiológica", 
                "Urgencias Cardiológicas"
            ])
            procedimiento_asociado = st.selectbox("🩺 Procedimiento relacionado (si aplica)", [
                "",
                "Cateterismo Cardiaco",
                "Angioplastia/Stent",
                "Ablación",
                "Implante de Marcapasos/DAI",
                "Cirugía de Bypass",
                "Valvuloplastía",
                "ECMO",
                "Otro"
            ])
    return {
        "fecha_evento": fecha_evento,
        "turno": turno,
        "ubicacion": ubicacion,
        "procedimiento_asociado": procedimiento_asociado
    }

def show_event_classification():
    """Muestra la clasificación del evento grave o adverso"""
    with st.expander("⚠️ Clasificación del Evento Grave o  Adverso", expanded=True):
        categoria_principal = st.selectbox("🔍 Tipo principal de evento", [
            "",
            "Complicación Isquémica",
            "Arritmia",  
            "Complicación Hemodinámica",
            "Complicación Vascular",
            "Evento Tromboembólico",  
            "Reacción a Medios de Contraste",
            "Infección Asociada",
            "Falla de Equipo Crítico",
            "Error en Medicación Cardiovascular"
        ])

        subcategorias_cardio = {
            "Complicación Isquémica": [
                "Reinfarto post-procedimiento",
                "Oclusión aguda de stent",
                "Espasmo coronario",
                "Disección coronaria"
            ],
            "Arritmia": [
                "Fibrilación Ventricular",
                "Taquicardia Ventricular Sostenida",
                "Bradiarritmia severa",
                "Bloqueo AV completo"
            ],
            "Complicación Hemodinámica": [
                "Shock cardiogénico",
                "Taponamiento cardíaco",
                "Insuficiencia cardíaca aguda",
                "Hipotensión refractaria"
            ],
            "Complicación Vascular": [
                "Hematoma acceso vascular",
                "Pseudoaneurisma",
                "Fístula arteriovenosa",
                "Isquemia distal"
            ],
            "Evento Tromboembólico": [
                "Trombosis de stent",
                "Embolismo coronario",
                "Accidente cerebrovascular",
                "Tromboembolismo pulmonar"
            ],
            "Reacción a Medios de Contraste": [
                "Nefropatía por contraste",
                "Reacción alérgica leve",
                "Reacción anafiláctica",
                "Extravasación de contraste"
            ],
            "Infección Asociada": [
                "Infección sitio acceso vascular",
                "Endocarditis post-procedimiento",
                "Sepsis relacionada a catéter",
                "Infección de herida quirúrgica"
            ],
            "Falla de Equipo Crítico": [
                "Falla de balón intra-aórtico",
                "Malfunción de marcapasos",
                "Problemas con ECMO",
                "Falla en equipo de hemodinamia"
            ],
            "Error en Medicación Cardiovascular": [
                "Sobredosis de anticoagulante",
                "Error en trombolíticos",
                "Administración incorrecta de antiarrítmicos",
                "Omisión de medicación crítica"
            ]
        }

        subcategoria = ""
        if categoria_principal in subcategorias_cardio:
            subcategoria = st.selectbox("📌 Subcategoría específica", [""] + subcategorias_cardio[categoria_principal])

        col1, col2 = st.columns(2)
        with col1:
            escala_grace = st.radio("📊 Gravedad (Adaptado a ESC Guidelines)", [
                "Bajo riesgo (sin repercusión hemodinámica)",
                "Intermedio (requirió intervención no planificada)",
                "Alto riesgo (daño orgánico permanente)",
                "Crítico (muerte o ECMO requerido)"
            ])
        with col2:
            detectado_en = st.radio("🔎 ¿Cuándo se detectó?", [
                "Antes del procedimiento",
                "Durante el procedimiento",
                "Inmediatamente después",
                "Tardíamente (fuera de área crítica)"
            ])
    
    return {
        "categoria_principal": categoria_principal,
        "subcategoria": subcategoria,
        "escala_grace": escala_grace,
        "detectado_en": detectado_en
    }

def show_contributing_factors():
    """Muestra los factores contribuyentes"""
    with st.expander("🔎 Factores Contribuyentes", expanded=False):
        cols = st.columns(3)
        factores = {}
        with cols[0]:
            st.markdown("**Factores del Paciente**")
            factores["comorbilidad"] = st.checkbox("Comorbilidades complejas")
            factores["anatomia"] = st.checkbox("Anatomía desfavorable")
            factores["urgencia"] = st.checkbox("Procedimiento urgente")
        
        with cols[1]:
            st.markdown("**Factores Técnicos**")
            factores["equipo"] = st.checkbox("Falla de equipo")
            factores["imagen"] = st.checkbox("Imagen intraprocedimiento no óptima")
            factores["acceso"] = st.checkbox("Dificultad en acceso vascular")
        
        with cols[2]:
            st.markdown("**Factores Humanos**")
            factores["experiencia"] = st.checkbox("Experiencia insuficiente del operador")
            factores["comunicacion"] = st.checkbox("Comunicación equipo-paciente")
            factores["fatiga"] = st.checkbox("Fatiga del personal")
    
    return factores

def show_patient_data():
    """Muestra los datos del paciente"""
    with st.expander("👨‍⚕️ Datos del Paciente", expanded=False):
        cols = st.columns(2)
        paciente_data = {}
        with cols[0]:
            paciente_data["nombre_completo"] = st.text_input("Nombre completo del paciente")
            paciente_data["edad"] = st.selectbox("Edad", ["", "<40", "40-65", ">65"])
            paciente_data["imc"] = st.selectbox("IMC", ["", "<25 (Normal)", "25-30 (Sobrepeso)", ">30 (Obeso)"])
        with cols[1]:
            paciente_data["numero_cama"] = st.text_input("Número de cama")
            paciente_data["riesgo_previo"] = st.selectbox("Riesgo pre-procedimiento", [
                "",
                "Bajo (0-2%)",
                "Intermedio (3-5%)",
                "Alto (>5%)"
            ])
    return paciente_data

def show_lab_results():
    """Muestra los resultados de laboratorio"""
    with st.expander("🧪 Resultados de Laboratorio", expanded=False):
        lab_data = {}
        
        examenes_solicitados = st.multiselect("Seleccione los exámenes solicitados:", [
            "Glucosa",
            "Troponina",
            "Sodio",
            "Potasio",
            "Creatinina",
            "BNP",
            "pH arterial",
            "Lactato",
            "Gases arteriales",
            "Hemograma completo",
            "Pruebas de coagulación"
        ])
        
        lab_data["examenes_solicitados"] = examenes_solicitados
        
        if "Glucosa" in examenes_solicitados:
            lab_data["glucosa"] = st.number_input("Glucosa (mg/dL)", min_value=0, max_value=1000, value=90)
        
        if "Troponina" in examenes_solicitados:
            lab_data["troponina"] = st.number_input("Troponina (ng/mL)", min_value=0.0, max_value=100.0, value=0.01, step=0.01, format="%.2f")
        
        if "Sodio" in examenes_solicitados:
            lab_data["sodio"] = st.number_input("Sodio (mEq/L)", min_value=100, max_value=200, value=140)
        
        if "Potasio" in examenes_solicitados:
            lab_data["potasio"] = st.number_input("Potasio (mEq/L)", min_value=1.0, max_value=10.0, value=4.0, step=0.1, format="%.1f")
        
        if "Creatinina" in examenes_solicitados:
            lab_data["creatinina"] = st.number_input("Creatinina (mg/dL)", min_value=0.1, max_value=20.0, value=0.8, step=0.1, format="%.1f")
        
        if "BNP" in examenes_solicitados:
            lab_data["bnp"] = st.number_input("BNP (pg/mL)", min_value=0, max_value=5000, value=100)
        
        if "pH arterial" in examenes_solicitados:
            lab_data["ph"] = st.number_input("pH arterial", min_value=6.5, max_value=8.0, value=7.4, step=0.01, format="%.2f")
        
        if "Lactato" in examenes_solicitados:
            lab_data["lactato"] = st.number_input("Lactato (mmol/L)", min_value=0.0, max_value=20.0, value=1.0, step=0.1, format="%.1f")
        
        if "Gases arteriales" in examenes_solicitados:
            st.markdown("**Gases Arteriales**")
            gas_cols = st.columns(3)
            with gas_cols[0]:
                lab_data["pao2"] = st.number_input("PaO₂ (mmHg)", min_value=20, max_value=600, value=80)
            with gas_cols[1]:
                lab_data["paco2"] = st.number_input("PaCO₂ (mmHg)", min_value=10, max_value=150, value=40)
            with gas_cols[2]:
                lab_data["sao2"] = st.number_input("SaO₂ (%)", min_value=50, max_value=100, value=98)
        
        if "Hemograma completo" in examenes_solicitados:
            st.markdown("**Hemograma**")
            hemo_cols = st.columns(3)
            with hemo_cols[0]:
                lab_data["hb"] = st.number_input("Hemoglobina (g/dL)", min_value=3.0, max_value=25.0, value=12.0, step=0.1, format="%.1f")
            with hemo_cols[1]:
                lab_data["hto"] = st.number_input("Hematocrito (%)", min_value=10, max_value=80, value=36)
            with hemo_cols[2]:
                lab_data["plaquetas"] = st.number_input("Plaquetas (x10³/μL)", min_value=10, max_value=1000, value=200)
        
        if "Pruebas de coagulación" in examenes_solicitados:
            st.markdown("**Coagulación**")
            coag_cols = st.columns(3)
            with coag_cols[0]:
                lab_data["tp"] = st.number_input("TP (seg)", min_value=5, max_value=100, value=12)
            with coag_cols[1]:
                lab_data["inr"] = st.number_input("INR", min_value=0.5, max_value=10.0, value=1.0, step=0.1, format="%.1f")
            with coag_cols[2]:
                lab_data["ttpa"] = st.number_input("TTPa (seg)", min_value=20, max_value=200, value=30)
    
    return lab_data

def show_medication_section():
    """Muestra la sección de medicamentos y dosis"""
    with st.expander("💊 Medicamentos Involucrados", expanded=False):
        medicamentos = []
        
        st.markdown("**Añadir medicamentos relacionados con el evento grave o adverso**")
        
        num_medicamentos = st.number_input("Número de medicamentos a registrar", min_value=1, max_value=10, value=1)
        
        for i in range(num_medicamentos):
            with st.container():
                st.markdown(f"### Medicamento {i+1}")
                cols = st.columns([2, 1, 1, 1])
                
                with cols[0]:
                    nombre = st.selectbox(f"Nombre del medicamento {i+1}", [
                        "",
                        "Heparina",
                        "Aspirina",
                        "Clopidogrel",
                        "Ticagrelor",
                        "Enoxaparina",
                        "Furosemida",
                        "Amiodarona",
                        "Dobutamina",
                        "Noradrenalina",
                        "Midazolam",
                        "Otro"
                    ], key=f"med_{i}_nombre")
                    
                    if nombre == "Otro":
                        nombre = st.text_input(f"Especificar otro medicamento {i+1}", key=f"med_{i}_otro")
                
                with cols[1]:
                    if nombre == "Heparina":
                        dosis = st.selectbox(f"Dosis {i+1}", [
                            "",
                            "5000 UI",
                            "2500 UI",
                            "1000 UI",
                            "80 UI/kg",
                            "60 UI/kg",
                            "Otra dosis"
                        ], key=f"med_{i}_dosis")
                    elif nombre == "Enoxaparina":
                        dosis = st.selectbox(f"Dosis {i+1}", [
                            "",
                            "40 mg",
                            "60 mg",
                            "80 mg",
                            "1 mg/kg",
                            "1.5 mg/kg",
                            "Otra dosis"
                        ], key=f"med_{i}_dosis")
                    elif nombre == "Amiodarona":
                        dosis = st.selectbox(f"Dosis {i+1}", [
                            "",
                            "150 mg",
                            "300 mg",
                            "5 mg/kg",
                            "Otra dosis"
                        ], key=f"med_{i}_dosis")
                    elif nombre == "Noradrenalina":
                        dosis = st.selectbox(f"Dosis {i+1}", [
                            "",
                            "0.05 mcg/kg/min",
                            "0.1 mcg/kg/min",
                            "0.2 mcg/kg/min",
                            "0.5 mcg/kg/min",
                            "Otra dosis"
                        ], key=f"med_{i}_dosis")
                    else:
                        dosis = st.selectbox(f"Dosis {i+1}", [
                            "",
                            "5 mg",
                            "10 mg",
                            "25 mg",
                            "50 mg",
                            "75 mg",
                            "100 mg",
                            "Otra dosis"
                        ], key=f"med_{i}_dosis")
                    
                    if dosis == "Otra dosis":
                        dosis = st.text_input(f"Especificar otra dosis {i+1}", key=f"med_{i}_otra_dosis")
                
                with cols[2]:
                    unidad = st.selectbox(f"Unidad {i+1}", [
                        "mg",
                        "UI",
                        "mcg",
                        "ml",
                        "mg/kg",
                        "UI/kg",
                        "mcg/kg",
                        "mcg/kg/min"
                    ], key=f"med_{i}_unidad")
                
                with cols[3]:
                    via = st.selectbox(f"Vía {i+1}", [
                        "EV",
                        "Oral",
                        "SC",
                        "Intraarterial",
                        "Intracoronaria",
                        "Inhalatoria"
                    ], key=f"med_{i}_via")
                
                error_med = st.checkbox(f"¿Hubo error en la administración de este medicamento? {i+1}", key=f"med_{i}_error")
                
                if error_med:
                    tipo_error = st.selectbox(f"Tipo de error {i+1}", [
                        "",
                        "Dosis incorrecta",
                        "Medicamento equivocado",
                        "Vía incorrecta",
                        "Paciente equivocado",
                        "Omisión de dosis",
                        "Velocidad de infusión incorrecta"
                    ], key=f"med_{i}_tipo_error")
                    
                    medicamentos.append({
                        "nombre": nombre,
                        "dosis": dosis,
                        "unidad": unidad,
                        "via": via,
                        "error": True,
                        "tipo_error": tipo_error
                    })
                else:
                    medicamentos.append({
                        "nombre": nombre,
                        "dosis": dosis,
                        "unidad": unidad,
                        "via": via,
                        "error": False
                    })
                
                st.markdown("---")
    
    return medicamentos

def show_management_section():
    """Muestra la sección de manejo del evento"""
    with st.expander("🚑 Manejo del Evento", expanded=False):
        cols = st.columns(2)
        manejo = {}
        with cols[0]:
            manejo["accion_inmediata"] = st.selectbox("✅ Acción inmediata tomada", [
                "",
                "Reintervención urgente",
                "Manejo médico intensivo",
                "Soporte circulatorio mecánico",
                "Reversión farmacológica",
                "Traslado a UCIC/Quirófano"
            ])
        with cols[1]:
            manejo["seguimiento"] = st.multiselect("📋 Seguimiento requerido", [
                "Monitorización extendida en UCIC",
                "Estudios de imagen adicionales",
                "Consulta a especialidad relacionada",
                "Revisión por comité"
            ])
    return manejo

def capture_image():
    """Captura una imagen usando la cámara de la tablet"""
    img_file = st.camera_input("📸 Tomar foto del evento grave o adverso")
    
    if img_file is not None:
        img = Image.open(img_file)
        st.image(img, caption="Foto capturada", use_column_width=True)
        return img
    return None


def record_video():
    """Graba video usando la cámara de la tablet"""
    video_bytes = st.camera_input("🎥 Grabar video del evento", key="video_recorder")
    
    if video_bytes is not None:
        st.video(video_bytes)
        return video_bytes
    return None

def show_evidence_section():
    """Muestra la sección para capturar evidencia multimedia usando la cámara y micrófono"""
    with st.expander("📸 Evidencia Multimedia del Evento", expanded=False):
        st.info("""
        Capture evidencia relevante del evento grave o adverso usando los dispositivos de la tablet:
        - Fotografías (ECG, heridas, equipos)
        - Videos cortos (monitorización, procedimientos)
        """)
        
        evidence_data = {}
        
        opcion_evidencia = st.radio("Seleccione el tipo de evidencia a capturar:", [
            "Ninguno",
            "Tomar fotografía",
            "Grabar video"
        ], horizontal=True)
        
        if opcion_evidencia == "Tomar fotografía":
            img = capture_image()
            if img is not None:
                evidence_data["imagen"] = {
                    "tipo": "foto",
                    "descripcion": st.text_input("Descripción de la foto")
                }
        elif opcion_evidencia == "Grabar video":
            video = record_video()
            if video is not None:
                evidence_data["video"] = {
                    "tipo": "video",
                    "descripcion": st.text_input("Descripción del video")
                }
    
    return evidence_data

def show_death_certificate():
    """Muestra la sección de certificado de defunción"""
    with st.expander("⚰️ Datos de Defunción (si aplica)", expanded=False):
        death_data = {}
        cols = st.columns(3)
        
        with cols[0]:
            muerte = st.radio("¿Falleció el paciente?", ["No", "Sí"], horizontal=True)
            death_data["fallecio"] = muerte == "Sí"
            
            if muerte == "Sí":
                death_data["hora_defuncion"] = st.time_input("Hora de defunción", time(0, 0))
        
        with cols[1]:
            if muerte == "Sí":
                death_data["folio_certificado"] = st.text_input("Número de folio del certificado médico")
                death_data["causa_muerte"] = st.selectbox("Causa principal de muerte", [
                    "",
                    "Infarto agudo de miocardio",
                    "Choque cardiogénico",
                    "Arritmia fatal",
                    "Taponamiento cardíaco",
                    "Embolia pulmonar masiva",
                    "Accidente cerebrovascular",
                    "Sepsis",
                    "Otra causa cardiovascular",
                    "Causa no cardiovascular"
                ])
        
        with cols[2]:
            if muerte == "Sí":
                death_data["autopsia"] = st.radio("¿Se realizó autopsia?", ["No", "Sí"], horizontal=True)
                death_data["obituario_patologia"] = st.text_input("Folio obituario (Patología)")
    
    return death_data

def show_validation_section():
    """Muestra la sección de validación"""
    with st.expander("✍️ Validación del Reporte", expanded=False):
        cols = st.columns(2)
        validacion = {}
        with cols[0]:
            validacion["reporter_name"] = st.text_input("Nombre del profesional que reporta")
            validacion["reporter_role"] = st.selectbox("Rol", ["", "Médico", "Enfermería", "Técnico"])
        with cols[1]:
            validacion["supervisor_review"] = st.checkbox("Confirmo revisión con supervisor")
            validacion["fecha_reporte"] = datetime.now().strftime("%d/%m/%Y %H:%M")
    return validacion

def submit_report(context, classification, factors, patient, lab_results, medications, management, death_data, validation, evidence):
    """Procesa el envío del reporte"""
    if not classification["categoria_principal"]:
        st.error("❌ Debe seleccionar al menos la categoría principal del evento")
        return False
    
    if not validation["supervisor_review"]:
        st.error("❌ Requiere validación con supervisor de turno")
        return False
    
    codigo_reporte = f"CARD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    report_data = {
        **context,
        **classification,
        "factores_contribuyentes": factors,
        "datos_paciente": patient,
        "laboratorio": lab_results,
        "medicamentos": medications,
        "manejo": management,
        "evidencia_multimedia": evidence,
        "datos_defuncion": death_data if death_data["fallecio"] else None,
        "validacion": validation
    }
    
    st.success(f"✅ Reporte enviado correctamente! Código: {codigo_reporte}")
    
    with st.expander("📄 Resumen del Reporte", expanded=True):
        st.json(report_data)
    
    return True

def show_supervisor_panel():
    """Muestra el panel de supervisores"""
    if st.secrets.get("SUPERVISOR_MODE", False):
        st.markdown("---")
        st.subheader("📊 Panel de Análisis Cardiológico (Solo Supervisores)")
        
        kpi_data = pd.DataFrame({
            "Tipo de Evento": ["Isquémico", "Arritmia", "Vascular", "Tromboembólico"],
            "Casos (30d)": [12, 8, 5, 3],
            "Gravedad Promedio": [2.7, 3.1, 2.4, 3.8]
        })
        
        st.bar_chart(kpi_data, x="Tipo de Evento", y="Casos (30d)")

def main():
    """Función principal de la aplicación"""
    setup_page()
    
    context = show_event_context()
    classification = show_event_classification()
    factors = show_contributing_factors()
    patient_data = show_patient_data()
    lab_results = show_lab_results()
    medications = show_medication_section()
    management = show_management_section()
    evidence = show_evidence_section()
    death_data = show_death_certificate()
    validation = show_validation_section()
    
    if st.button("📤 Enviar Reporte Cardiológico", type="primary", use_container_width=True):
        submit_report(context, classification, factors, patient_data, lab_results, medications, management, death_data, validation, evidence)
    
    show_supervisor_panel()

if __name__ == "__main__":
    main()
