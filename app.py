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
# Opcional: "detalles": {1: "texto"} agrega un "Más detalle" desplegable
# debajo del paso 1 de la solución (usa el número del paso que quieras).
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
    {  # 7. Nota crédito sobre factura ya aceptada
        "palabras_clave": [
            "lgc15",
            "cbf03a",
            "no es posible la transmision de una nota credito",
            "notas credito no puede anular facturas",
        ],
        "titulo": "Rechazo LGC15: Nota crédito sobre una factura ya aceptada",
        "causa": (
            "La nota crédito referencia una factura que ya está aceptada por"
            " la DIAN y fue creada con causal de anulación, lo cual no es"
            " permitido."
        ),
        "solucion": (
            "1. Verificar que la factura referenciada en la nota crédito no esté"
            " aceptada por la DIAN.\n"
            "2. Si ya está aceptada, la nota no puede ir con causal de anulación:"
            " debe ir como descuento y sin referenciar la factura.\n"
            "3. Notificar al proceso de Contabilidad para que modifique la nota"
            " y cambie el causal de anulación.\n"
            "4. Facturación debe quitar la referencia de la factura, volver a"
            " generar el archivo plano y retransmitir."
        ),
        "detalles": {
            1: (
                "Para saber si la factura está aceptada:\n\n"
                "1. Copia el **CUFE de la factura** referenciada en la nota"
                " crédito (aparece en la representación gráfica o PDF de la"
                " factura).\n"
                "2. Entra a [Buscar documento de la DIAN]"
                "(https://catalogo-vpfe.dian.gov.co/User/SearchDocument).\n"
                "3. Pega el CUFE y consulta. Desde julio de 2026 la DIAN puede"
                " pedir también el NIT del emisor o del receptor.\n"
                "4. Si la factura aparece validada/aceptada, la nota crédito no"
                " puede ir con causal de anulación."
            ),
        },
        "area": "Proceso de Contabilidad y Facturación",
    },
    {  # 8. Valor del tributo en nota crédito (CAS07)
        "palabras_clave": ["cas07"],
        "titulo": "Rechazo CAS07: El valor del tributo no corresponde (nota crédito)",
        "causa": (
            "El valor del tributo informado no corresponde al porcentaje"
            " aplicado sobre la base imponible; puede ser un problema de"
            " decimales o de parametrización del impuesto."
        ),
        "solucion": (
            "1. Notificar al proceso de T.I.\n"
            "2. T.I. valida el decimal o el impuesto del documento."
        ),
        "area": "Proceso de T.I.",
    },
    {  # 9. Comprobante duplicado (DI2)
        "palabras_clave": [
            "error di2",
            "di2",
            "ya existe un comprobante con ese mismo tipo y numero",
        ],
        "titulo": "Error DI2: Comprobante ya existe (duplicado)",
        "causa": (
            "Ya existe un comprobante con el mismo tipo y número enviado a la"
            " entidad reguladora."
        ),
        "solucion": (
            "1. Validar en comprobantes emitidos si la factura ya fue"
            " transmitida.\n"
            "2. Si ya fue emitida, no es necesario retransmitirla.\n"
            "3. Si no ha sido emitida, volver a generar el insumo y"
            " retransmitir."
        ),
        "area": "Proceso de Facturación",
    },
    {  # 10. Fecha de generación distinta a fecha de firma (FAD09e)
        "palabras_clave": [
            "fad09e",
            "fecha de generacion de la factura sea igual a la fecha de firma",
        ],
        "titulo": "Rechazo FAD09e: Fecha de generación diferente a la fecha de firma",
        "causa": (
            "La factura fue emitida con una fecha posterior a hoy y firmada"
            " electrónicamente, pero no llegó a la DIAN porque fue rechazada y"
            " no se corrigió el mismo día."
        ),
        "solucion": (
            "1. Comunicarse con el proceso de T.I.\n"
            "2. T.I. soluciona el tema de la fecha de la factura."
        ),
        "area": "Proceso de T.I.",
    },
    {  # 11. Valor del tributo en factura (FAS07)
        "palabras_clave": ["fas07"],
        "titulo": "Rechazo FAS07: El valor del tributo no corresponde (factura)",
        "causa": (
            "El valor del tributo informado no corresponde al porcentaje"
            " aplicado sobre la base imponible; puede ser un problema de"
            " decimales o de parametrización del impuesto."
        ),
        "solucion": (
            "1. Notificar al proceso de T.I.\n"
            "2. T.I. valida el decimal o el impuesto del documento."
        ),
        "area": "Proceso de T.I.",
    },
    {  # 12. Error de estructura por salto de línea (VA0)
        "palabras_clave": [
            "va0",
            "no se pudo cargar por error en su estructura",
        ],
        "titulo": "Error VA0: Error de estructura por salto de línea en la dirección",
        "causa": (
            "La dirección de entrega tiene un salto de línea. Caracteres como"
            " la coma o el tabulador se toman como salto de línea y rompen la"
            " estructura del archivo."
        ),
        "solucion": (
            "1. Notificar al proceso de Cartera.\n"
            "2. Quitar el salto de línea y los caracteres especiales (coma,"
            " tabulador) de la dirección.\n"
            "3. Volver a generar el insumo y retransmitir."
        ),
        "area": "Proceso de Cartera",
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
                    st.markdown("**💡 Solución técnica:**")
                    detalles = item.get("detalles", {})
                    # Cada paso va en su propia línea; si tiene "detalle",
                    # se muestra un desplegable justo debajo de ese paso.
                    for num, paso in enumerate(item["solucion"].split("\n"), start=1):
                        st.markdown(paso)
                        if num in detalles:
                            with st.expander("🔎 Más detalle"):
                                st.markdown(detalles[num])
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
