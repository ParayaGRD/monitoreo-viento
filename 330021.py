import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import os
import traceback

# URL de la estación meteorológica
URL = "https://climatologia.meteochile.gob.cl/application/diariob/visorDeDatosEma/330021"

# Límite de velocidad del viento (en kt) para generar la alarma
LIMITE_VELOCIDAD = 25

# Variables de entorno (cargadas desde GitHub Secrets)
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]
DESTINATARIO = os.environ["DESTINATARIO"]

def obtener_velocidad_viento():
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        celdas = soup.find_all("td", class_="text-center")

        for celda in celdas:
            texto = celda.text.strip()
            if "/" in texto:  # Formato dirección/velocidad
                _, velocidad = texto.split("/")
                velocidad = int(velocidad)
                return velocidad

        return None
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        print(traceback.format_exc())
        return None

def enviar_correo(subject: str, body: str, important: bool = False):
    """
    Envía un correo. Si important=True agrega cabeceras que indican alta prioridad.
    Nota: SMTP no puede forzar etiquetas internas de Gmail; esto solo añade cabeceras de prioridad.
    """
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = CORREO_ORIGEN
        mensaje["To"] = DESTINATARIO
        mensaje["Subject"] = subject

        # Cabeceras que suelen usarse para indicar prioridad
        if important:
            mensaje["Importance"] = "High"
            mensaje["X-Priority"] = "1 (Highest)"
            mensaje["X-MSMail-Priority"] = "High"
            mensaje["Priority"] = "urgent"

        mensaje.attach(MIMEText(body, "plain"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(CORREO_ORIGEN, CONTRASENA)
        servidor.sendmail(CORREO_ORIGEN, DESTINATARIO, mensaje.as_string())
        servidor.quit()

        print(f"✅ Correo enviado a {DESTINATARIO} — Asunto: {subject}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    print("🔍 Revisando la velocidad del viento...")
    velocidad = obtener_velocidad_viento()

    if velocidad is not None:
        print(f"Velocidad actual del viento: {velocidad} kt")

        # 1) Enviar siempre el informe de medición
        asunto_informe = f"Informe: Velocidad del viento Pudahuel AMB - {velocidad} kt"
        cuerpo_informe = (
            f"Informe automático de velocidad del viento (estación 330021):\n\n"
            f"Velocidad actual: {velocidad} kt\n"
            f"Límite configurado: {LIMITE_VELOCIDAD} kt\n\n"
            f"Si necesita más detalles revise el sistema de monitoreo."
        )
        enviar_correo(asunto_informe, cuerpo_informe, important=False)

        # 2) Si excede el límite, enviar además una alerta marcada como importante
        if velocidad > LIMITE_VELOCIDAD:
            asunto_alerta = "ALERTA IMPORTANTE: Velocidad de viento SUPERADA - Pudahuel AMB"
            cuerpo_alerta = (
                f"ALERTA:\n\nLa velocidad del viento ha alcanzado {velocidad} kt, "
                f"superando el límite de {LIMITE_VELOCIDAD} kt en la estación 330021 (Pudahuel AMB).\n\n"
                f"Acción recomendada: revisar operaciones y tomar medidas de mitigación."
            )
            enviar_correo(asunto_alerta, cuerpo_alerta, important=True)
        else:
            print("Todo en orden ✅ (no supera el límite)")
    else:
        print("No se pudo obtener la velocidad del viento ❌")
        # Opcional: enviar correo de error (descomentar si quieres)
        # enviar_correo("Error: No se pudieron obtener datos de viento", "Revisar proceso de scraping o la URL.", important=True)
