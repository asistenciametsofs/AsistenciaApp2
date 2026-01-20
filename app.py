import streamlit as st
import pandas as pd
import smtplib
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# -----------------------------
# CONFIGURACIÓN GENERAL
# -----------------------------
st.set_page_config(
    page_title="REGISTRO DE ALCOHOTEST",
    layout="wide"
)

st.title("🧪 REGISTRO DE ALCOHOTEST")

# -----------------------------
# LEER PERSONAL
# -----------------------------
personal = pd.read_csv(
    "personal.csv",
    encoding="utf-8-sig",
    header=None
)

personal = personal.iloc[:, 0].astype(str)
personal = personal[personal.str.lower() != "nombre"]

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

st.markdown("### 👥 Lista de personal")

# -----------------------------
# LISTA DE ASISTENCIA (MOBILE)
# -----------------------------
asistencia = []

for i, nombre in enumerate(personal):
    with st.container(border=True):
        col1, col2 = st.columns([1, 6])

        with col1:
            asistio = st.checkbox("✔️", key=f"chk_{i}")

        with col2:
            st.markdown(f"**{nombre}**")

        estado = st.radio(
            "Estado",
            ["Sin observación", "Observado"],
            horizontal=True,
            key=f"estado_{i}"
        )

        comentario = ""
        if estado == "Observado":
            comentario = st.text_input(
                "Observación",
                placeholder="Ej: Aliento etílico / 0.15",
                key=f"obs_{i}"
            )

        asistencia.append({
            "Nombre": nombre,
            "Asistió": asistio,
            "Estado": estado,
            "Comentario": comentario
        })

# -----------------------------
# BOTÓN ENVIAR
# -----------------------------
if st.button("📨 ENVIAR REGISTRO", use_container_width=True):

    # -----------------------------
    # CREAR PDF
    # -----------------------------
    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    c = canvas.Canvas(pdf_temp.name, pagesize=A4)
    width, height = A4
    y = height - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "REGISTRO DE ALCOHOTEST")
    y -= 25

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Fecha: {fecha}")
    y -= 15
    c.drawString(40, y, f"Supervisor: {supervisor}")
    y -= 30

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "ASISTIERON")
    y -= 15

    for item in asistencia:
        if item["Asistió"]:
            # Color según estado
            if item["Estado"] == "Observado":
                c.setFillColor(colors.red)
            else:
                c.setFillColor(colors.green)

            texto = f"- {item['Nombre']} | {item['Estado']} | {item['Comentario']}"
            c.drawString(50, y, texto)
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 40

    y -= 20
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawString(40, y, "NO ASISTIERON")
    y -= 15

    c.setFont("Helvetica", 10)
    for item in asistencia:
        if not item["Asistió"]:
            c.setFillColor(colors.black)
            c.drawString(50, y, f"- {item['Nombre']}")
            y -= 14
            if y < 60:
                c.showPage()
                y = height - 40

    c.save()

    # -----------------------------
    # ENVÍO CORREO
    # -----------------------------
    remitente = st.secrets["gmail_user"]
    contraseña = st.secrets["gmail_password"]
    destinatarios = [d.strip() for d in st.secrets["destino"].split(",")]

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = f"Lista Alcohotest - {fecha} - {supervisor}"

    cuerpo = f"""
REGISTRO DE ALCOHOTEST

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

