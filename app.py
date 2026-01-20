import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Leer CSV ---
# Para tu CSV con encabezado “Nombre” o solo una columna
personal = pd.read_csv("personal.csv", encoding="latin1", header=None, names=["Nombre"]).dropna()

# --- App UI ---
st.title("Registro de Asistencia")

# Fecha y supervisor
fecha = st.date_input("Fecha")
supervisor = st.text_input("Supervisor")

st.write("Marca la asistencia y completa observaciones:")

# Diccionario para guardar asistencia
asistencia = {}

# Para cada persona
for i, row in personal.iterrows():
    nombre = row["Nombre"]
    col1, col2, col3 = st.columns([2,1,3])
    with col1:
        checked = st.checkbox(nombre, key=i)
    with col2:
        estado = st.selectbox("Estado", ["Sin observación","Observado"], key=f"estado{i}")
    with col3:
        comentario = st.text_input("Observación", key=f"obs{i}")
    asistencia[nombre] = {"Asistió": checked, "Estado": estado, "Comentario": comentario}

# Botón enviar
if st.button("Enviar asistencia"):

    # Crear texto del correo
    texto = f"Asistencia - Fecha: {fecha}, Supervisor: {supervisor}\n\n"
    texto += "ASISTIERON:\n"
    for nombre, info in asistencia.items():
        if info["Asistió"]:
            texto += f"- {nombre} | {info['Estado']} | {info['Comentario']}\n"
    texto += "\nNO ASISTIERON:\n"
    for nombre, info in asistencia.items():
        if not info["Asistió"]:
            texto += f"- {nombre}\n"

    # --- Enviar correo ---
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
        st.success("Correo enviado correctamente!")
    except Exception as e:
        st.error(f"Error al enviar correo: {e}")
