import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------
# Leer CSV (corrige ï»¿Nombre)
# -----------------------------
personal = pd.read_csv(
    "personal.csv",
    encoding="utf-8-sig",   # <-- CLAVE
    header=None,
    names=["Nombre"]
).dropna()

# -----------------------------
# Configuración página
# -----------------------------
st.set_page_config(page_title="Registro de Asistencia", layout="wide")

st.title("Registro de Asistencia")

fecha = st.date_input("Fecha")

supervisor = st.selectbox(
    "Supervisor",
    [
        "Marco Sanz", "Daniel Herreros", "Daniel Aedo", "Freddy Marquez",
        "Joey Abarca", "Wilmer Mixcan", "Lizeth Gonzales", "Victor Velasquez",
        "Jaime Vizcarra", "Juan Cojoma", "Diego Carpio", "Raul Cardenas"
    ]
)

st.markdown("### Lista de asistencia")

# -----------------------------
# Encabezados
# -----------------------------
h1, h2, h3, h4 = st.columns([0.7, 4, 2, 3])

with h1:
    st.markdown("**✔**")
with h2:
    st.markdown("**Nombre**")
with h3:
    st.markdown("**Estado**")
with h4:
    st.markdown("**Observación**")

st.divider()

# -----------------------------
# Tabla asistencia
# -----------------------------
asistencia = []

for i, row in personal.iterrows():
    col1, col2, col3, col4 = st.columns([0.7, 4, 2, 3])

    with col1:
        asistio = st.checkbox("", key=f"chk_{i}")

    with col2:
        st.write(row["Nombre"])

    with col3:
        estado = st.selectbox(
            "",
            ["Sin observación", "Observado"],
            key=f"estado_{i}"
        )

    with col4:
        comentario = st.text_input("", key=f"obs_{i}")

    asistencia.append({
        "Nombre": row["Nombre"],
        "Asistió": asistio,
        "Estado": estado,
        "Comentario": comentario
    })

# -----------------------------
# Enviar correo
# -----------------------------
if st.button("Enviar asistencia"):

    texto = f"Asistencia\nFecha: {fecha}\nSupervisor: {supervisor}\n\n"

    texto += "ASISTIERON:\n"
    for item in asistencia:
        if item["Asistió"]:
            texto += f"- {item['Nombre']} | {item['Estado']} | {item['Comentario']}\n"

    texto += "\nNO ASISTIERON:\n"
    for item in asistencia:
        if not item["Asistió"]:
            texto += f"- {item['Nombre']}\n"

    remitente = st.secrets["gmail_user"]
    contraseña = st.secrets["gmail_password"]
    destinatario = st.secrets["destino"]

    msg = MIMEMultipart()
    msg["From"] = remitente
    msg["To"] = destinatario
    msg["Subject"] = f"Asistencia {fecha} - {supervisor}"
    msg.attach(MIMEText(texto, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(remitente, contraseña)
        server.send_message(msg)
        server.quit()
        st.success("✅ Correo enviado correctamente")
    except Exception as e:
        st.error(f"❌ Error al enviar correo: {e}")
