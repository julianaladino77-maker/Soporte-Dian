import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Soporte Facturación DIAN", page_icon="🧾", layout="centered"
)

st.title("🧾 Asistente de Errores - Facturación Electrónica DIAN")
st.write(
    "Pega la traza del error o el texto del log para identificar la causa,"
    " solución y área a notificar."
)

# =====================================================================
# AQUÍ PUEDES AGREGAR TODOS LOS ERRORES QUE QUIERAS MÁS ADELANTE
# =====================================================================
# Cada error tiene:
# - 'palabras_clave': palabras que el sistema buscará en el log.
# - 'titulo': El título del error.
# - 'causa': Qué significa el error.
# - 'solucion': Los pasos para solucionarlo.
# - 'area': A quién se debe notificar.
# =====================================================================

BASE_DE_ERRORES = [
    {
        "palabras_clave": [
            "codigo postal",
            "adq-14",
            "dfa-3",
            "postalzone",
        ],
        "titulo": "Error de longitud en el Código Postal",
        "causa": (
            "El campo enviado supera el límite permitido por el estándar de la"
            " DIAN (máximo 10 caracteres)."
        ),
        "solucion": (
            "1. Notificar al proceso de Cartera/Datos Maestros.\n2. Corregir"
            " el código postal en la ficha del cliente en el ERP.\n3."
            " Regenerar el archivo plano y retransmitir."
        ),
        "area": "Área de Cartera",
    },
    {
        "palabras_clave": ["nit", "digito de verificacion", "dv"],
        "titulo": "Error en el NIT o Dígito de Verificación",
        "causa": (
            "El NIT o el DV reportado no coincide con los registros del"
            " prevalidador de la DIAN."
        ),
        "solucion": (
            "1. Validar el RUT actualizado del cliente o emisor.\n2. Actualizar"
            " el dato maestro en el sistema y reintentar el envío."
        ),
        "area": "Área Comercial / Cartera",
    },
    # -----------------------------------------------------------------
    # 👇 PARA AGREGAR UN NUEVO ERROR, SOLO COPIA Y PEGA UN BLOQUE COMO ESTE:
    # -----------------------------------------------------------------
    # {
    #     "palabras_clave": ["nombre_del_error", "otro_codigo"],
    #     "titulo": "Título de tu nuevo error",
    #     "causa": "Explicación de por qué ocurre.",
    #     "solucion": "Pasos para solucionarlo.",
    #     "area": "Área encargada"
    # },
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
    st.warning("Por favor, pega un log de error para analizar.")
  else:
    log_lower = log_input.lower()
    error_encontrado = False

    st.subheader("🔍 Diagnóstico del Sistema")

    # Buscamos en nuestra base de errores cuál coincide con el log pegado
    for item in BASE_DE_ERRORES:
      # Si alguna de las palabras clave está dentro del log del usuario
      if any(keyword in log_lower for keyword in item["palabras_clave"]):
        error_encontrado = True
        st.error(f"❌ **Causa del Rechazo:** {item['titulo']}")
        st.markdown(f"""
                * **Detalle / Causa:** {item['causa']}
                * **💡 Solución Técnica:** 
                  {item['solucion']}
                * **👥 A quién notificar:** {item['area']}
                """)
        break  # Detiene la búsqueda al encontrar el primer match

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