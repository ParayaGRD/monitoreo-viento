import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import os

# URL de la estación meteorológica
URL = "https://climatologia.meteochile.gob.cl/application/diariob/visorDeDatosEma/330021"

# Límite de velocidad del viento (en kt) para generar la alarma
LIMITE_VELOCIDAD = 25

# Variables de entorno (cargadas desde GitHub Secrets)
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]
DESTINATARIO = os.environ["DESTINATARIO"]

# Función para extraer la velocidad del viento
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
        return None

# Función para enviar un correo de alarma
def enviar_alarma_por_correo(velocidad):
    try:
        asunto = "Alerta: Velocidad de viento superada Pudahuel AMB"
        cuerpo = (f"La velocidad del viento ha alcanzado {velocidad} kt, "
                  f"lo cual supera el límite de {LIMITE_VELOCIDAD} kt. en Pudahuel AMB")
        mensaje = MIMEMultipart()
        mensaje["From"] = CORREO_ORIGEN
        mensaje["To"] = DESTINATARIO
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(CORREO_ORIGEN, CONTRASENA)
        servidor.sendmail(CORREO_ORIGEN, DESTINATARIO, mensaje.as_string())
        servidor.quit()

        print(f"✅ Correo enviado a {DESTINATARIO}")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

# Ejecución única (GitHub Actions lo correrá cada 5 min)
if __name__ == "__main__":
    print("🔍 Revisando la velocidad del viento...")
    velocidad = obtener_velocidad_viento()

    if velocidad is not None:
        print(f"Velocidad actual del viento: {velocidad} kt")
        if velocidad > LIMITE_VELOCIDAD:
            enviar_alarma_por_correo(velocidad)
        else:
            print("Todo en orden ✅ (no supera el límite)")
    else:
        print("No se pudo obtener la velocidad del viento ❌")
