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
st.title("🧪 REGISTRO DE ASISTENCIA PRE-EMBARQUE")
st.markdown(
    """
    <div style="margin-top:-10px; line-height:1.6;">
        <strong>Alcoholímetro Marca:</strong> Hanwei<br>
        <strong>Modelo:</strong> AT7000<br>
        <strong>Serie:</strong> 2C0702200018
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()

st.subheader("📝 Tipo de registro")

tipo_registro = st.multiselect(
    "",
    ["Prueba de Alcoholemia", "Embarque a SMCV"],
    default=[]
)

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

mapa_personal = {
    f"{normalizar(p)}|||{p}": p for p in personal
}

# -----------------------------
# STATE
# -----------------------------
if "seleccionados" not in st.session_state:
    st.session_state.seleccionados = []

if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

# -----------------------------
# DATOS GENERALES
# -----------------------------
fecha = st.date_input("📅 Fecha")

supervisor = st.selectbox(
    "👷 Supervisor",
    [
        "Marco Sanz", "Daniel Herreros", "Daniel Aedo", "Freddy Marquez",
        "Joey Abarca", "Wilmer Mixcan", "Gabriel Choque", "Lizeth Gonzales", "Victor Velasquez",
        "Jaime Vizcarra", "Juan Cojoma", "Diego Carpio", "Raul Cardenas"
    ]
)

st.divider()

# -----------------------------
# BUSCADOR (NO SE TOCA)
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
    st.session_state.seleccionados.insert(0, {
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
# BOTONES
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    enviar = st.button("📨 ENVIAR REGISTRO", use_container_width=True)

with col2:
    if st.button("🧹 LIMPIAR REGISTRO", use_container_width=True):
        st.session_state.seleccionados = []
        st.session_state.pdf_path = None
        st.rerun()

# -----------------------------
# ENVÍO + PDF + MAIL
# -----------------------------
if enviar:

    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    st.session_state.pdf_path = pdf_temp.name

    c = canvas.Canvas(pdf_temp.name, pagesize=A4)
    width, height = A4
    y = height - 40

    titulo = " / ".join(tipo_registro) if tipo_registro else "REGISTRO"
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"REGISTRO DE {titulo.upper()}")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(40, y, "Alcoholímetro Marca: Hanwei")
    y -= 14
    c.drawString(40, y, "Modelo: AT7000")
    y -= 14
    c.drawString(40, y, "Serie: 2C0702200018")
    y -= 20

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
            c.drawImage(img, 50, y - 80, width=100, height=80)
            y -= 90

        y -= 10

    c.save()

    # -------- MAIL --------
    remitente = st.secrets["gmail_user"]
    contraseña = st.secrets["gmail_password"]
    destinatarios = [d.strip() for d in st.secrets["destino"].split(",")]

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = f"Lista Alcohotest - {fecha} - {supervisor}"

    msg.attach(MIMEText("Se adjunta el registro en PDF.", "plain"))

    with open(st.session_state.pdf_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", 'attachment; filename="Alcohotest.pdf"')
    msg.attach(part)

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(remitente, contraseña)
    server.sendmail(remitente, destinatarios, msg.as_string())
    server.quit()

    st.success("✅ Registro enviado correctamente")

# -----------------------------
# DESCARGA (SIEMPRE VISIBLE)
# -----------------------------
if st.session_state.pdf_path:
    with open(st.session_state.pdf_path, "rb") as f:
        st.download_button(
            "⬇️ Descargar PDF",
            data=f,
            file_name=f"Lista_Alcohotest_{fecha}.pdf",
            mime="application/pdf",
            use_container_width=True
        )






