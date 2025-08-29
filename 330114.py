import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import os
import traceback
import re

# URL de la estación meteorológica
URL = "https://climatologia.meteochile.gob.cl/application/diariob/visorDeDatosEma/330114"

# Límite de velocidad del viento (en kt) para generar la alarma
LIMITE_VELOCIDAD = 25

# Credenciales desde GitHub Secrets
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]

def obtener_destinatarios():
    raw = os.environ.get("DESTINATARIOS") or os.environ.get("DESTINATARIO")
    if not raw:
        raise RuntimeError("No se encontró la variable DESTINATARIOS ni DESTINATARIO en el entorno")
    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    if not parts:
        raise RuntimeError("No hay destinatarios válidos en DESTINATARIOS/DESTINATARIO")
    return parts

DESTINATARIOS = obtener_destinatarios()

def obtener_velocidad_viento():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        celdas = soup.find_all("td", class_="text-center")
        for celda in celdas:
            texto = celda.text.strip()
            if "/" in texto:
                partes = texto.split("/")
                velocidad_raw = partes[-1].strip()
                m = re.search(r"(\d+)", velocidad_raw)
                if m:
                    return int(m.group(1))
        return None
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        print(traceback.format_exc())
        return None

def enviar_correo(subject: str, body: str, important: bool = False):
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = CORREO_ORIGEN
        mensaje["To"] = ", ".join(DESTINATARIOS)
        mensaje["Subject"] = subject

        if important:
            mensaje["Importance"] = "High"
            mensaje["X-Priority"] = "1 (Highest)"
            mensaje["X-MSMail-Priority"] = "High"
            mensaje["Priority"] = "urgent"

        mensaje.attach(MIMEText(body, "plain"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(CORREO_ORIGEN, CONTRASENA)
        servidor.sendmail(CORREO_ORIGEN, DESTINATARIOS, mensaje.as_string())
        servidor.quit()

        print(f"✅ Correo enviado a: {', '.join(DESTINATARIOS)} — Asunto: {subject}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("🔍 Revisando la velocidad del viento (estación 330114)...")
    velocidad = obtener_velocidad_viento()

    if velocidad is not None:
        print(f"Velocidad actual del viento: {velocidad} kt")

        asunto_informe = f"Informe: Velocidad del viento San Pablo DASA (330114) - {velocidad} kt"
        cuerpo_informe = (
            f"Informe automático (estación 330114 - San Pablo DASA):\n\n"
            f"Velocidad actual: {velocidad} kt\n"
            f"Límite configurado: {LIMITE_VELOCIDAD} kt\n\n"
            f"Este correo es un registro periódico generado por el sistema de monitoreo."
        )
        enviar_correo(asunto_informe, cuerpo_informe, important=False)

        if velocidad > LIMITE_VELOCIDAD:
            asunto_alerta = "ALERTA IMPORTANTE: Velocidad de viento SUPERADA - San Pablo DASA (330114)"
            cuerpo_alerta = (
                f"ALERTA:\n\nLa velocidad del viento ha alcanzado {velocidad} kt, "
                f"superando el límite de {LIMITE_VELOCIDAD} kt en la estación 330114 (San Pablo DASA).\n\n"
                f"Acción recomendada: revisar operaciones y tomar medidas de mitigación."
            )
            enviar_correo(asunto_alerta, cuerpo_alerta, important=True)
        else:
            print("Todo en orden ✅ (no supera el límite)")
    else:
        print("No se pudo obtener la velocidad del viento ❌")
