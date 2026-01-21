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

personal_norm = {normalizar(p): p for p in personal}

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
# BUSCADOR REAL (SIN TEXTO, CON TILDES)
# -----------------------------
st.subheader("🔍 Buscar trabajador")

busqueda = st.text_input(
    "",
    placeholder="Buscar por nombre o apellido"
)

if busqueda:
    buscado = normalizar(busqueda)

    opciones = [
        p for p in personal
        if buscado in normalizar(p)
        and p not in [x["Nombre"] for x in st.session_state.seleccionados]
    ]
else:
    opciones = []

if opciones:
    seleccionado = st.selectbox(
        "Resultados",
        options=opciones,
        label_visibility="collapsed"
    )

    if st.button("➕ Agregar"):
        st.session_state.seleccionados.append({
            "id": str(uuid.uuid4()),
            "Nombre": seleccionado,
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

# -----------------------------
# ENVIAR REGISTRO
# -----------------------------
if st.button("📨 ENVIAR REGISTRO", use_container_width=True):

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

        if y < 120:
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
            c.drawImage(img, 50, y - 80, width=100, height=80, preserveAspectRatio=True)
            y -= 90

        y -= 10

    c.save()

    # -------- DESCARGA --------
    with open(pdf_temp.name, "rb") as pdf_file:
        st.download_button(
            "⬇️ Descargar PDF",
            data=pdf_file,
            file_name=f"Lista_Alcohotest_{fecha}_{supervisor}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    # -------- MAIL --------
    remitente = st.secrets["gmail_user"]
    contraseña = st.secrets["gmail_password"]
    destinatarios = [d.strip() for d in st.secrets["destino"].split(",")]

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = f"Lista Alcohotest - {fecha} - {supervisor}"

    cuerpo = f"""REGISTRO DE ALCOHOTEST

Fecha: {fecha}
Supervisor: {supervisor}

Se adjunta el archivo PDF con el registro.
"""
    msg.attach(MIMEText(cuerpo, "plain"))

    with open(pdf_temp.name, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f'attachment; filename="Lista_Alcohotest_{fecha}.pdf"'
    )

    msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(remitente, contraseña)
    server.sendmail(remitente, destinatarios, msg.as_string())
    server.quit()

    st.success("✅ Registro enviado correctamente")

    if st.button("➕ Registrar otro control"):
        st.session_state.seleccionados = []
        st.rerun()

