import streamlit as st
from datetime import datetime
import pandas as pd

def setup_page():
    """Configura la página de Streamlit"""
    st.set_page_config(
        page_title="🚨 Reporte Cardiológico de Eventos Adversos",
        layout="wide",
        page_icon="❤️"
    )
    st.title("❤️‍🩹 Reporte Estructurado de Eventos Adversos Cardiológicos")
    st.markdown("**Instituto de Cardiología - Sistema estandarizado para UCIC, Hemodinamia y Cirugía Cardiovascular**")

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
    """Muestra la clasificación del evento adverso"""
    with st.expander("⚠️ Clasificación del Evento Adverso", expanded=True):
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
            # ... (otras subcategorías como en el código anterior)
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
        cols = st.columns(3)
        paciente_data = {}
        with cols[0]:
            paciente_data["edad"] = st.selectbox("Edad", ["", "<40", "40-65", ">65"])
        with cols[1]:
            paciente_data["imc"] = st.selectbox("IMC", ["", "<25 (Normal)", "25-30 (Sobrepeso)", ">30 (Obeso)"])
        with cols[2]:
            paciente_data["riesgo_previo"] = st.selectbox("Riesgo pre-procedimiento", [
                "",
                "Bajo (0-2%)",
                "Intermedio (3-5%)",
                "Alto (>5%)"
            ])
    return paciente_data

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

def submit_report(context, classification, factors, patient, management, validation):
    """Procesa el envío del reporte"""
    if not classification["categoria_principal"]:
        st.error("❌ Debe seleccionar al menos la categoría principal del evento")
        return False
    
    if not validation["supervisor_review"]:
        st.error("❌ Requiere validación con supervisor de turno")
        return False
    
    codigo_reporte = f"CARD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Aquí iría la lógica para guardar en base de datos
    report_data = {
        **context,
        **classification,
        "factores_contribuyentes": factors,
        "datos_paciente": patient,
        "manejo": management,
        "validacion": validation
    }
    
    st.success(f"✅ Reporte enviado correctamente! Código: {codigo_reporte}")
    
    # Mostrar resumen
    with st.expander("📄 Resumen del Reporte", expanded=True):
        st.json(report_data)  # Alternativa: st.dataframe(pd.DataFrame.from_dict(report_data))
    
    return True

def show_supervisor_panel():
    """Muestra el panel de supervisores"""
    if st.secrets.get("SUPERVISOR_MODE", False):
        st.markdown("---")
        st.subheader("📊 Panel de Análisis Cardiológico (Solo Supervisores)")
        
        # Datos de ejemplo
        kpi_data = pd.DataFrame({
            "Tipo de Evento": ["Isquémico", "Arritmia", "Vascular", "Tromboembólico"],
            "Casos (30d)": [12, 8, 5, 3],
            "Gravedad Promedio": [2.7, 3.1, 2.4, 3.8]
        })
        
        st.bar_chart(kpi_data, x="Tipo de Evento", y="Casos (30d)")

def main():
    """Función principal de la aplicación"""
    # Configuración inicial
    setup_page()
    
    # Mostrar secciones del formulario
    context = show_event_context()
    classification = show_event_classification()
    factors = show_contributing_factors()
    patient_data = show_patient_data()
    management = show_management_section()
    validation = show_validation_section()
    
    # Botón de envío
    if st.button("📤 Enviar Reporte Cardiológico", type="primary", use_container_width=True):
        submit_report(context, classification, factors, patient_data, management, validation)
    
    # Panel de supervisores
    show_supervisor_panel()

if __name__ == "__main__":
    main()
