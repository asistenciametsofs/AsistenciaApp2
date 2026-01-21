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

def comprimir_imagen(file, max_size=(800, 800), quality=60):
    img = Image.open(file)
    img.thumbnail(max_size)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return buffer

# -----------------------------
# PERSONAL
# -----------------------------
personal = pd.read_csv("personal.csv", encoding="utf-8-sig", header=None)
personal = personal.iloc[:, 0].astype(str).tolist()

# -----------------------------
# STATE
# -----------------------------
if "seleccionados" not in st.session_state:
    st.session_state.seleccionados = []

if "buscador_id" not in st.session_state:
    st.session_state.buscador_id = 0

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
# BUSCADOR (SIEMPRE ACTIVO)
# -----------------------------
st.subheader("🔍 Buscar y agregar trabajador")

opciones = [
    p for p in personal
    if p not in [x["Nombre"] for x in st.session_state.seleccionados]
]

seleccion = st.multiselect(
    "Buscar trabajador",
    options=opciones,
    placeholder="Escribe nombre o apellido",
    key=f"buscador_{st.session_state.buscador_id}",
    label_visibility="collapsed"
)

if seleccion:
    for nombre in seleccion:
        st.session_state.seleccionados.append({
            "id": str(uuid.uuid4()),
            "Nombre": nombre,
            "Estado": "Sin observación",
            "Comentario": "",
            "Foto": None
        })

    st.session_state.buscador_id += 1
    st.rerun()

st.divider()

# -----------------------------
# LISTA SELECCIONADA
# -----------------------------
st.subheader("👥 Personal evaluado")

id_borrar = None

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
            id_borrar = item["id"]

        if item["Estado"] == "Observado":
            item["Comentario"] = st.text_input(
                "Observación",
                placeholder="Ej: 0.15 / Aliento etílico",
                key=f"obs_{item['id']}"
            )
        else:
            item["Comentario"] = ""

        item["Foto"] = st.file_uploader(
            "📷 Fotografía (opcional)",
            type=["jpg", "jpeg", "png"],
            key=f"foto_{item['id']}"
        )

if id_borrar:
    st.session_state.seleccionados = [
        x for x in st.session_state.seleccionados if x["id"] != id_borrar
    ]
    st.rerun()

# -----------------------------
# BOTONES FINALES
# -----------------------------
colA, colB = st.columns(2)

with colA:
    enviar = st.button("📨 ENVIAR REGISTRO", use_container_width=True)

with colB:
    if st.button("🧹 NUEVO REGISTRO", use_container_width=True):
        st.session_state.seleccionados = []
        st.session_state.buscador_id += 1
        st.rerun()

# -----------------------------
# ENVIAR / PDF
# -----------------------------
if enviar and st.session_state.seleccionados:

    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(pdf_temp.name, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "REGISTRO DE ALCOHOTEST")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Fecha: {fecha}")
    y -= 15
    c.drawString(40, y, f"Supervisor: {supervisor}")
    y -= 30

    for item in st.session_state.seleccionados:
        if y < 150:
            c.showPage()
            y = height - 40

        c.setFillColor(colors.red if item["Estado"] == "Observado" else colors.green)
        c.drawString(40, y, f"{item['Nombre']} | {item['Estado']}")
        y -= 15

        c.setFillColor(colors.black)
        if item["Comentario"]:
            c.drawString(50, y, f"Obs: {item['Comentario']}")
            y -= 15

        if item["Foto"]:
            img_buffer = comprimir_imagen(item["Foto"])
            img = ImageReader(img_buffer)
            c.drawImage(img, 50, y - 80, width=100, height=80)
            y -= 90

        y -= 10

    c.save()

    with open(pdf_temp.name, "rb") as pdf_file:
        st.download_button(
            "⬇️ Descargar PDF",
            data=pdf_file,
            file_name=f"Lista_Alcohotest_{fecha}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.success("✅ Registro generado correctamente")

