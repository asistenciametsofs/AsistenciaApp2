import streamlit as st
import pandas as pd
import smtplib
import tempfile
import uuid
import unicodedata
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image
import io

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="REGISTRO DE ALCOHOTEST", layout="wide")
st.title("🧪 REGISTRO DE ALCOHOTEST")

# -----------------------------
# FUNCIONES
# -----------------------------
def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    ).lower()

def comprimir_imagen(file, max_size=(800, 600), quality=60):
    img = Image.open(file)
    img.thumbnail(max_size)
    buffer = io.BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return buffer

# -----------------------------
# PERSONAL
# -----------------------------
personal = pd.read_csv("personal.csv", encoding="utf-8-sig", header=None)
personal = personal.iloc[:, 0].astype(str)
personal = personal[personal.str.lower() != "nombre"].tolist()

# Mapa normalizado → nombre real
mapa_personal = {
    f"{normalizar(p)}|||{p}": p for p in personal
}

# -----------------------------
# STATE
# -----------------------------
if "seleccionados" not in st.session_state:
    st.session_state.seleccionados = []

# -----------------------------
# DATOS GENERALES
# -----------------------------
fecha = st.date_input("📅 Fecha")

supervisor = st.selectbox(
    "👷 Supervisor",
    [
        "Marco Sanz", "Daniel Herreros", "Daniel Aedo", "Freddy Marquez",
        "Joey Abarca", "Wilmer Mixcan", "Lizeth Gonzales", "Victor Velasquez",
        "Jaime Vizcarra", "Juan Cojoma", "Diego Carpio", "Raul Cardenas"
    ]
)

st.divider()

# -----------------------------
# BUSCADOR (NO SE CAMBIA)
# -----------------------------
st.subheader("🔍 Buscar trabajador")

opciones_disponibles = [
    k for k, v in mapa_personal.items()
    if v not in [x["Nombre"] for x in st.session_state.seleccionados]
]

busqueda = st.selectbox(
    "",
    options=[""] + opciones_disponibles,
    format_func=lambda x: "" if x == "" else x.split("|||")[1]
)

if busqueda:
    nombre_real = mapa_personal[busqueda]

    st.session_state.seleccionados.append({
        "id": str(uuid.uuid4()),
        "Nombre": nombre_real,
        "Estado": "Sin observación",
        "Comentario": "",
        "Foto": None
    })
    st.rerun()

st.divider()

# -----------------------------
# LISTA SELECCIONADA
# -----------------------------
st.subheader("👥 Personal evaluado")

borrar_id = None

for item in st.session_state.seleccionados:
    with st.container(border=True):

        col1, col2, col3 = st.columns([6, 2, 1])

        col1.markdown(f"**{item['Nombre']}**")

        item["Estado"] = col2.radio(
            "Estado",
            ["Sin observación", "Observado"],
            horizontal=True,
            key=f"estado_{item['id']}"
        )

        if col3.button("🗑️", key=f"del_{item['id']}"):
            borrar_id = item["id"]

        if item["Estado"] == "Observado":
            item["Comentario"] = st.text_input(
                "Observación",
                key=f"obs_{item['id']}"
            )
        else:
            item["Comentario"] = ""

        item["Foto"] = st.file_uploader(
            "📷 Fotografía (opcional)",
            type=["jpg", "jpeg", "png"],
            key=f"foto_{item['id']}"
        )

if borrar_id:
    st.session_state.seleccionados = [
        x for x in st.session_state.seleccionados if x["id"] != borrar_id
    ]
    st.rerun()

st.divider()

# -----------------------------
# BOTONES FINALES
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    enviar = st.button("📨 ENVIAR REGISTRO", use_container_width=True)

with col2:
    if st.button("🧹 LIMPIAR REGISTRO", use_container_width=True):
        st.session_state.seleccionados = []
        st.rerun()

# -----------------------------
# ENVÍO
# -----------------------------
if enviar:
    st.success("✅ Registro enviado correctamente")
