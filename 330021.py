# 330021.py
import os, re, traceback
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URL = "https://climatologia.meteochile.gob.cl/application/diariob/visorDeDatosEma/330021"
LIMITE_VELOCIDAD = 25

CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]

def obtener_destinatarios():
    raw = os.environ.get("DESTINATARIOS") or os.environ.get("DESTINATARIO")
    if not raw:
        raise RuntimeError("No se encontró DESTINATARIOS ni DESTINATARIO")
    parts = [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]
    return parts

DESTINATARIOS = obtener_destinatarios()

def obtener_velocidad_viento():
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
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
        print("Error al obtener datos:", e)
        print(traceback.format_exc())
        return None

def append_csv(station_id: str, timestamp_iso: str, velocidad: int):
    os.makedirs("data", exist_ok=True)
    path = f"data/{station_id}.csv"
    header = "timestamp,wind_kt\n"
    write_header = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if write_header:
            f.write(header)
        f.write(f"{timestamp_iso},{velocidad}\n")

def enviar_alerta(velocidad):
    try:
        subject = f"ALERTA: Velocidad de viento SUPERADA - Pudahuel AMB (330021) {velocidad} kt"
        body = (f"ALERTA:\n\nLa velocidad del viento alcanzó {velocidad} kt, "
                f"superando el límite de {LIMITE_VELOCIDAD} kt en estación 330021 (Pudahuel AMB).")
        msg = MIMEMultipart()
        msg["From"] = CORREO_ORIGEN
        msg["To"] = ", ".join(DESTINATARIOS)
        msg["Subject"] = subject
        msg["Importance"] = "High"
        msg["X-Priority"] = "1 (Highest)"
        msg.attach(MIMEText(body, "plain"))

        s = smtplib.SMTP("smtp.gmail.com", 587)
        s.starttls()
        s.login(CORREO_ORIGEN, CONTRASENA)
        s.sendmail(CORREO_ORIGEN, DESTINATARIOS, msg.as_string())
        s.quit()
        print("✅ Alerta enviada.")
    except Exception as e:
        print("Error al enviar alerta:", e)
        print(traceback.format_exc())

if __name__ == "__main__":
    print("Revisando 330021...")
    velocidad = obtener_velocidad_viento()
    tz = ZoneInfo("America/Santiago")
    now = datetime.now(tz)
    ts = now.isoformat()
    if velocidad is not None:
        print(f"{ts} - Velocidad: {velocidad} kt")
        append_csv("330021", ts, velocidad)
        if velocidad > LIMITE_VELOCIDAD:
            enviar_alerta(velocidad)
        else:
            print("No supera el límite.")
    else:
        print("No se pudo obtener velocidad.")
