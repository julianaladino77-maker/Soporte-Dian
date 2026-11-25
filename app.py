import os
import re
import unicodedata
from datetime import datetime
from urllib.parse import quote

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Soporte de errores Juli", page_icon="🧾", layout="centered")

# Empresas que aparecen en el selector (editar aquí para agregar otra).
EMPRESAS = ["Rotoplast", "Leguz"]
ARCHIVO = "catalogo.xlsx"  # El administrador edita este Excel.
MAX_PASOS = 6


def secreto(clave, defecto=""):
    try:
        return st.secrets.get(clave, defecto)
    except Exception:
        return defecto


def normalizar(texto):
    """Minúsculas, sin tildes y sin signos: 'ADQ - 14' -> 'adq 14'."""
    t = unicodedata.normalize("NFKD", str(texto).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).strip()


@st.cache_data
def cargar(_version):
    df = pd.read_excel(ARCHIVO, sheet_name=0, dtype=str).fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    return df[df["activo"].str.strip().str.upper() != "NO"]


def aplica_a(valor_empresa, empresa):
    """True si la fila es 'Todas' o incluye la empresa elegida."""
    lista = [normalizar(x) for x in valor_empresa.split(";")]
    return "todas" in lista or normalizar(empresa) in lista


def buscar(log, filas):
    """Errores que coinciden con el log, el más específico primero.

    Compara palabras completas (así 'nit' no se activa con 'unitario')
    y pesa más las palabras clave largas.
    """
    texto = f" {normalizar(log)} "
    resultados = []
    for _, f in filas.iterrows():
        claves = [normalizar(k) for k in f["palabras_clave"].split(";") if k.strip()]
        puntaje = sum(len(k) for k in claves if k and f" {k} " in texto)
        if puntaje:
            resultados.append((puntaje, f))
    resultados.sort(key=lambda x: x[0], reverse=True)
    return [f for _, f in resultados]


def mostrar(f):
    with st.container(border=True):
        st.markdown(f"#### ❌ {f['titulo']}")
        if f["codigo"].strip():
            st.caption(f"Código: {f['codigo']}")
        st.markdown(f"**📋 Detalle / Causa:** {f['causa']}")
        st.markdown("**💡 Solución técnica:**")
        num = 0
        for i in range(1, MAX_PASOS + 1):
            paso = f.get(f"paso_{i}", "").strip()
            if not paso:
                continue
            num += 1
            st.markdown(f"{num}. {paso}")
            detalle = f.get(f"detalle_{i}", "").strip()
            if detalle:
                with st.expander("🔎 Más detalle"):
                    st.markdown(detalle)
        st.markdown(f"**👥 A quién notificar:** {f['area']}")


# ---------------------------------------------------------------- interfaz
try:
    df = cargar(os.path.getmtime(ARCHIVO))
except Exception as e:
    st.error(f"No se pudo leer {ARCHIVO}. Revisa que exista y tenga las columnas originales. ({e})")
    st.stop()

with st.sidebar:
    st.subheader("Estado del catálogo")
    st.caption(f"Archivo: {ARCHIVO}")
    st.caption(
        "Última modificación (hora del servidor): "
        + datetime.fromtimestamp(os.path.getmtime(ARCHIVO)).strftime("%d/%m/%Y %H:%M")
    )
    st.caption(f"Errores activos cargados: {len(df)}")
    st.dataframe(
        df.groupby("tema").size().rename("errores"),
        width="stretch",
    )
    if st.button("🔄 Recargar catálogo"):
        st.cache_data.clear()
        st.rerun()

col1, col2 = st.columns(2)
empresa = col1.selectbox("Empresa", EMPRESAS)
disponibles = df[df["empresa"].apply(lambda v: aplica_a(v, empresa))]
temas = sorted(disponibles["tema"].unique())
if not temas:
    st.warning("No hay errores activos para esta empresa.")
    st.stop()
tema = col2.selectbox("Tema", temas)
filas = disponibles[disponibles["tema"] == tema]

st.title(f"🧾 Asistente de errores: {tema}")
st.write(
    "Pega la traza del error o el texto del log para identificar la causa,"
    " solución y área a notificar."
)

log_input = st.text_area(
    "Pega aquí el detalle del error o la traza:",
    placeholder="Ej: [ERROR-VA0] ... Campo ADQ - 14 Codigo Postal ... No cumple la longitud",
)

if st.button("Diagnosticar Error", type="primary"):
    if not log_input.strip():
        st.warning("Por favor, pega un log de error para analizar.")
    else:
        st.subheader("🔍 Diagnóstico del Sistema")
        coincidencias = buscar(log_input, filas)

        if coincidencias:
            if len(coincidencias) > 1:
                st.info(f"Se encontraron {len(coincidencias)} posibles errores en el log.")
            for f in coincidencias:
                mostrar(f)
        else:
            st.warning(
                "⚠️ No se reconoció una regla exacta para este error en la base de"
                " datos. Aquí tienes los pasos generales:"
            )
            pasos = ["Verifique el número de la línea y la sección indicadas en la traza."]
            if "factur" in normalizar(tema):
                pasos.append("Revise el documento en el visor de CT&S.")
            pasos.append("Si persiste, escalar al equipo de desarrollo de TI o soporte técnico.")
            st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(pasos, start=1)))

            contacto = secreto("CONTACTO_TI")
            if contacto:
                asunto = quote(f"Error no reconocido ({empresa} - {tema})")
                cuerpo = quote(log_input[:1500])
                st.link_button("📧 Reportar este error a T.I.",
                               f"mailto:{contacto}?subject={asunto}&body={cuerpo}")
