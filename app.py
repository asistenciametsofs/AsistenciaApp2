import streamlit as st
import pandas as pd
import smtplib
import tempfile
import uuid
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
st.set_page_config(page_title="REGISTRO DE ALCOHOTEST", layout="wide")
st.title("🧪 REGISTRO DE ALCOHOTEST")

# -----------------------------
# LEER PERSONAL
# -----------------------------
personal = pd.read_csv("personal.csv", encoding="utf-8-sig", header=None)
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
# BUSCADOR
# -----------------------------
st.subheader("🔍 Buscar y agregar trabajador")

seleccion = st.multiselect(
    "Buscar trabajador",
    options=personal,
    placeholder="Escribe apellido o nombre",
    label_visibility="collapsed"
)

if st.button("🧹 Limpiar todo"):
    st.session_state.seleccionados = []
    st.rerun()

# Agregar sin duplicar
nombres_existentes = [x["Nombre"] for x in st.session_state.seleccionados]

for nombre in seleccion:
    if nombre not in nombres_existentes:
        st.session_state.seleccionados.append({
            "id": str(uuid.uuid4()),
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

id_a_borrar = None

for item in st.session_state.seleccionados:
    with st.container(border=True):

        col1, col2, col3 = st.columns([6, 2, 1])

        with col1:
            st.markdown(f"**{item['Nombre']}**")

        with col2:
            item["Estado"] = st.radio(
                "Estado",
                ["Sin observación", "Observado"],
                horizontal=True,
                key=f"estado_{item['id']}"
            )

        with col3:
            if st.button("🗑️", key=f"del_{item['id']}"):
                id_a_borrar = item["id"]

        if item["Estado"] == "Observado":
            item["Comentario"] = st.text_input(
                "Observación",
                placeholder="Ej: Aliento etílico / 0.15",
                key=f"obs_{item['id']}"
            )
        else:
            item["Comentario"] = ""

        item["Foto"] = st.file_uploader(
            "📷 Fotografía (opcional)",
            type=["jpg", "png", "jpeg"],
            key=f"foto_{item['id']}"
        )

# 🔥 BORRADO REAL Y SEGURO
if id_a_borrar:
    st.session_state.seleccionados = [
        x for x in st.session_state.seleccionados if x["id"] != id_a_borrar
    ]
    st.rerun()

# -----------------------------
# ENVIAR
# -----------------------------
if st.button("📨 ENVIAR REGISTRO", use_container_width=True):

    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(pdf_temp.name, pagesize=A4)
    y = A4[1] - 40

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "REGISTRO DE ALCOHOTEST")
    y -= 30

    c.setFont("Helvetica", 11)
    c.drawString(40, y, f"Fecha: {fecha}")
    y -= 15
    c.drawString(40, y, f"Supervisor: {supervisor}")
    y -= 30

    for item in st.session_state.seleccionados:
        c.setFillColor(colors.red if item["Estado"] == "Observado" else colors.green)
        foto = "Sí" if item["Foto"] else "No"
        texto = f"- {item['Nombre']} | {item['Estado']} | {item['Comentario']} | Foto: {foto}"
        c.drawString(40, y, texto)
        y -= 14

        if y < 60:
            c.showPage()
            y = A4[1] - 40

    c.save()

    with open(pdf_temp.name, "rb") as pdf:
        st.download_button(
            "⬇️ Descargar PDF",
            data=pdf,
            file_name=f"Lista_Alcohotest_{fecha}_{supervisor}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.success("✅ Registro generado correctamente")


