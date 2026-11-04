import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Soporte Facturación DIAN", page_icon="🧾", layout="centered"
)

st.title("🧾 Asistente de Errores - Facturación Electrónica DIAN")
st.write(
    "Pega la traza del error o el texto del rechazo para identificar la causa,"
    " solución y proceso a notificar."
)

# =====================================================================
# BASE DE DATOS DE ERRORES
# =====================================================================
BASE_DE_ERRORES = [
    {
        #1. Código Postal
        "palabras_clave": ["codigo postal", "código postal", "adq-14",
            "dfa-3", "postalzone"],
        "titulo": "Error de longitud en el Código Postal",
        "causa": (
            "El campo enviado supera el límite permitido por el estándar de la"
            " DIAN (máximo 10 caracteres)."
        ),
        "solucion": (
            "1. Notificar al proceso de Cartera.\n"
            "2. Corregir el código postal en el maestro de clientes en el ERP.\n"
            "3. Generar el archivo plano nuevamente y retransmitir."
        ),
        "area": "Proceso de Cartera",
    },
    {
        #2. Dígito de Verificación
        "palabras_clave": ["nit", "digito de verificacion", "dv"],
        "titulo": "Error en el NIT o Dígito de Verificación",
        "causa": (
            "El NIT o el DV reportado no coincide con los registros del"
            " prevalidador de la DIAN."
        ),
        "solucion": (
            "1. Notificar al proceso de Cartera.\n"
            "2. Corregir el NIT en el maestro de clientes en el sistema ERP.\n"
            "3. Corregir el documento electrónico con el NIT corregido.\n"
            "4. Generar el archivo plano nuevamente y retransmitir."
        ),
        "area": "Proceso de Cartera",
    },

    {
            #3. Referenciar Factura en Nota Crédito
            "palabras_clave": ["Cude de NC referenciada no existe", 
                               "Se requiere obligatoriamente referencia a documento",
                                 "CBGC02", "CBGC04", "CBGC05"],
            "titulo": "Nota Crédito no referenciada",
            "causa": (
                "la nota crédito tiene una factura asociada sin el código cufe  "
                " de la factura electrónica."
            ),
            "solucion": (
                "1. Notificar en la mesa de servicio de Carvajal.\n"
                "2. Notificar al proceso de TI."
            ),
            "area": "Proceso de TI",
        },
]

# Campo de texto para que el equipo de TI pegue el log
log_input = st.text_area(
    "Pega aquí el detalle del error o la traza:",
    placeholder=(
        "Ej: [ERROR-VA0] ... Campo ADQ - 14 Codigo Postal ... No cumple la"
        " longitud"
    ),
)

if st.button("Diagnosticar Error", type="primary"):
  if not log_input.strip():
    st.warning("Por favor, pega una línea de error para analizar.")
  else:
    log_lower = log_input.lower()
    error_encontrado = False

    st.subheader("🔍 Diagnóstico del Sistema")

    # Buscamos en nuestra base de errores cuál coincide con el error pegado
    for item in BASE_DE_ERRORES:
      if any(keyword in log_lower for keyword in item["palabras_clave"]):
        error_encontrado = True
        st.error(f"❌ **Causa del Rechazo:** {item['titulo']}")

        # Usamos doble espacio o saltos limpios para que Markdown pinte cada línea aparte
        st.markdown(f"* **📋 Detalle / Causa:** {item['causa']}")
        st.markdown(f"* **💡 Solución Técnica:**")
        # Imprimimos la solución respetando los saltos de línea de cada número
        for linea in item["solucion"].split("\n"):
          st.markdown(f"  {linea}")

        st.markdown(f"* **👥 A quién notificar:** {item['area']}")
        break

    # Si ningún error de la lista coincide
    if not error_encontrado:
      st.warning(
          "⚠️ No se reconoció una regla exacta para este error en la base de"
          " datos. Aquí tienes los pasos generales:"
      )
      st.markdown("""
            1. Verifique el número de la línea y la sección indicadas en la traza.
            2. Revise el documento en el visor de CT&S.
            3. Si persiste, escalar al equipo de desarrollo de TI o soporte técnico.
            """)
