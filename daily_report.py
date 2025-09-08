import pandas as pd
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# Variables de entorno (GitHub Secrets)
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]
DESTINATARIOS = os.environ["DESTINATARIOS"].split(",")

# Directorio donde se guardan los CSV
DATA_DIR = "data"

# Función para leer y preparar CSV
def read_station_csv(path):
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        # Convertir a datetime
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        # Localizar timezone si no lo tiene
        if df["timestamp"].dt.tz is None:
            df["timestamp"] = df["timestamp"].dt.tz_localize("America/Santiago")
    return df

# Función para generar el informe diario
def build_report_for_date(report_date):
    report_lines = []
    estaciones = {
        "330021": "Pudahuel AMB",
        "330114": "San Pablo DASA"
    }

    for code, name in estaciones.items():
        file_path = os.path.join(DATA_DIR, f"{code}.csv")
        if not os.path.exists(file_path):
            report_lines.append(f"⚠️ No hay datos para la estación {name} ({code})\n")
            continue

        df = read_station_csv(file_path)

        # Filtrar datos del día solicitado
        df_day = df[df["timestamp"].dt.date == report_date.date()]

        if df_day.empty:
            report_lines.append(f"⚠️ Sin registros para {name} ({code}) en {report_date.date()}\n")
            continue

        # Agrupar por hora y calcular estadísticas
        df_day["hour"] = df_day["timestamp"].dt.hour
        stats = df_day.groupby("hour")["velocidad"].agg(["min", "max", "mean"])

        report_lines.append(f"📊 Informe {name} ({code}) - {report_date.date()}")
        report_lines.append(stats.to_string())
        report_lines.append("")

    return "\n".join(report_lines)

# Función para enviar correo
def enviar_informe_por_correo(asunto, cuerpo):
    try:
        mensaje = MIMEMultipart()
        mensaje["From"] = CORREO_ORIGEN
        mensaje["To"] = ", ".join(DESTINATARIOS)
        mensaje["Subject"] = asunto
        mensaje.attach(MIMEText(cuerpo, "plain"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(CORREO_ORIGEN, CONTRASENA)
        servidor.sendmail(CORREO_ORIGEN, DESTINATARIOS, mensaje.as_string())
        servidor.quit()

        print(f"✅ Informe enviado a {', '.join(DESTINATARIOS)}")
    except Exception as e:
        print(f"❌ Error al enviar informe: {e}")

# Ejecución principal
if __name__ == "__main__":
    report_date = datetime.now() - timedelta(days=1)  # Informe del día anterior
    body = build_report_for_date(report_date)

    if body.strip():
        enviar_informe_por_correo(
            f"📌 Informe diario de viento - {report_date.date()}",
            body
        )
    else:
        print("⚠️ No se generó contenido para el informe.")
