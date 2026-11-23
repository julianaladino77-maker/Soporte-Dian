import re
import unicodedata

import streamlit as st

st.set_page_config(
    page_title="Soporte Facturación DIAN", page_icon="🧾", layout="centered"
)

st.title("🧾 Asistente de Errores - Facturación Electrónica DIAN")
st.write(
    "Pega la traza del error o el texto del log para identificar la causa,"
    " solución y área a notificar."
)

# =====================================================================
# BASE DE DATOS DE ERRORES
# Para agregar uno nuevo: copia un bloque { ... }, y cambia sus campos.
# Las palabras clave no distinguen mayúsculas, tildes ni guiones.
# =====================================================================
BASE_DE_ERRORES = [
    {  # 1. Código postal
        "palabras_clave": ["codigo postal", "adq-14", "dfa-3", "postalzone"],
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
    {  # 2. NIT incorrecto
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
    {  # 3. Nota crédito sin referencia
        "palabras_clave": [
            "cude de nc referenciada no existe",
            "se requiere obligatoriamente referencia a documento",
            "cbgc02",
            "cbgc04",
            "cbgc05",
        ],
        "titulo": "Nota Crédito no referenciada",
        "causa": (
            "La nota crédito tiene una factura asociada sin el código CUFE"
            " de la factura electrónica."
        ),
        "solucion": (
            "1. Notificar en la mesa de servicio de Carvajal.\n"
            "2. Notificar al proceso de TI."
        ),
        "area": "Proceso de TI",
    },
    {  # 4. Resolución / rango
        "palabras_clave": [
            "fab11b",
            "fab12b",
            "fad05c",
            "valor inicial del rango de numeracion",
            "valor final del rango",
            "superior al final del rango",
        ],
        "titulo": "Error en el rango o resolución de numeración",
        "causa": (
            "El valor inicial o final del rango de numeración informado no"
            " corresponde a los rangos vigentes otorgados por la DIAN para el"
            " emisor (o superó el final del rango)."
        ),
        "solucion": (
            "1. Notificar al proceso contable para la actualización de resolución.\n"
            "2. Generar el archivo plano nuevamente y retransmitir."
        ),
        "area": "Proceso Contable",
    },
    {  # 5. Valor de tributo
        "palabras_clave": ["fat02", "valor total de un tributo no corresponde"],
        "titulo": "Rechazo FAT02: Error en el valor total de tributos y retenciones",
        "causa": (
            "La factura cuenta con tres tipos de retenciones, y por ahora el"
            " sistema está parametrizado con dos tipos de retenciones no más."
        ),
        "solucion": (
            "1. Notificar al proceso de T.I.\n"
            "2. Adicionar el otro tipo de retención en el sistema.\n"
            "3. Volver a generar el archivo plano y retransmitir."
        ),
        "area": "Proceso de T.I.",
    },
    {  # 6. Partida arancelaria IAE
        "palabras_clave": [
            "iae",
            "iae 1",
            "iae 2",
            "codigo del producto de acuerdo con el estandar descrito en el campo iae 2",
            "partida arancelaria",
            "documento del exterior",
        ],
        "titulo": "Falta de partida arancelaria (Campo IAE) en documento del exterior",
        "causa": (
            "El documento es del exterior y el sistema exige en el campo IAE"
            " la partida arancelaria, por lo que el código del producto se"
            " vuelve obligatorio."
        ),
        "solucion": (
            "1. Hablar con el asesor de zona exterior para que actualice el"
            " maestro con las partidas arancelarias correspondientes.\n"
            "2. Volver a generar el archivo plano.\n"
            "3. Retransmitir la factura."
        ),
        "area": "Asesor de Zona Exterior",
    },
]


def normalizar(texto):
    """Minúsculas, sin tildes y sin signos: 'ADQ - 14' -> 'adq 14'."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


def buscar(log):
    """Devuelve los errores que coinciden, el más específico primero.

    Compara palabras completas (así 'nit' no se activa con 'unitario'
    ni 'dv' con 'advertencia') y le da más peso a las claves largas.
    """
    texto = f" {normalizar(log)} "
    resultados = []
    for item in BASE_DE_ERRORES:
        puntaje = sum(
            len(normalizar(k))
            for k in item["palabras_clave"]
            if f" {normalizar(k)} " in texto
        )
        if puntaje:
            resultados.append((puntaje, item))
    resultados.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in resultados]


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
        st.subheader("🔍 Diagnóstico del Sistema")
        coincidencias = buscar(log_input)

        if coincidencias:
            if len(coincidencias) > 1:
                st.info(f"Se encontraron {len(coincidencias)} posibles errores en el log.")
            for item in coincidencias:
                with st.container(border=True):
                    st.markdown(f"#### ❌ {item['titulo']}")
                    st.markdown(f"**📋 Detalle / Causa:** {item['causa']}")
                    # Línea en blanco antes de la lista para que Markdown
                    # pinte cada paso en su propia línea.
                    st.markdown("**💡 Solución técnica:**\n\n" + item["solucion"])
                    st.markdown(f"**👥 A quién notificar:** {item['area']}")
        else:
            st.warning(
                "⚠️ No se reconoció una regla exacta para este error en la base de"
                " datos. Aquí tienes los pasos generales:"
            )
            st.markdown(
                "1. Verifique el número de la línea y la sección indicadas en la traza.\n"
                "2. Revise el documento en el visor de CT&S.\n"
                "3. Si persiste, escalar al equipo de desarrollo de TI o soporte técnico."
            )
