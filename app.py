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
personal = personal[personal.str.lower() != "nombre"].tolist()

# -----------------------------
# SESSION STATE
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
# BUSCADOR REAL (AUTOFILTRO)
# -----------------------------
st.subheader("🔍 Buscar y agregar trabajador")

seleccion = st.multiselect(
    "Buscar trabajador",
    options=personal,
    placeholder="Escribe apellido o nombre",
    label_visibility="collapsed"
)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🧹 Limpiar todo"):
        st.session_state.seleccionados = []
        st.rerun()

# Agregar seleccionados (sin duplicar)
for nombre in seleccion:
    if nombre not in [x["Nombre"] for x in st.session_state.seleccionados]:
        st.session_state.seleccionados.append({
            "Nombre": nombre,
            "Estado": "Sin observación",
            "Comentario": "",
            "Foto": None
        })

st.divider()

# -----------------------------
# LISTA SELECCIONADA
# -----------------------------
st.subheader("👥 Personal evaluado")

for i, item in enumerate(st.session_state.seleccionados):
    with st.container(border=True):

        col1, col2, col3 = st.columns([6, 2, 1])

        with col1:
            st.markdown(f"**{item['Nombre']}**")

        with col2:
            item["Estado"] = st.radio(
                "Estado",
                ["Sin observación", "Observado"],
                horizontal=True,
                key=f"estado_{i}"
            )

        with col3:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.seleccionados.pop(i)
                st.rerun()

        # Observación SOLO si es observado
        if item["Estado"] == "Observado":
            item["Comentario"] = st.text_input(
                "Observación",
                placeholder="Ej: Aliento etílico / 0.15",
                key=f"obs_{i}"
            )
        else:
            item["Comentario"] = ""

        # FOTO OPCIONAL PARA TODOS
        item["Foto"] = st.file_uploader(
            "📷 Fotografía (opcional)",
            type=["jpg", "png", "jpeg"],
            key=f"foto_{i}"
        )

# -----------------------------
# BOTÓN ENVIAR
# -----------------------------
if st.button("📨 ENVIAR REGISTRO", use_container_width=True):

    # -------- PDF --------
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

    for item in st.session_state.seleccionados:
        if item["Estado"] == "Observado":
            c.setFillColor(colors.red)
        else:
            c.setFillColor(colors.green)

        tiene_foto = "Sí" if item["Foto"] else "No"
        texto = f"- {item['Nombre']} | {item['Estado']} | {item['Comentario']} | Foto: {tiene_foto}"
        c.drawString(40, y, texto)
        y -= 14

        if y < 60:
            c.showPage()
            y = height - 40

    c.save()

    # -------- DESCARGA PDF --------
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



