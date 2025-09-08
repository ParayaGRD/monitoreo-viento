import os
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pytz

# ========================
# 📂 Lectura de datos CSV
# ========================
def read_station_csv(path):
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        # Forzar conversión de timestamp a datetime con UTC
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

        # Eliminar filas inválidas
        df = df.dropna(subset=["timestamp"])

        # Convertir de UTC a horario de Chile
        df["timestamp"] = df["timestamp"].dt.tz_convert("America/Santiago")

    return df

# ========================
# 📊 Generación del reporte
# ========================
def build_report_for_date(report_date):
    report_lines = []
    station_files = {
        "330021": "data/330021.csv",
        "330114": "data/330114.csv"
    }

    for station, file_path in station_files.items():
        if not os.path.exists(file_path):
            report_lines.append(f"⚠️ No hay datos para la estación {station}.\n")
            continue

        df = read_station_csv(file_path)

        if df.empty:
            report_lines.append(f"⚠️ Archivo vacío para estación {station}.\n")
            continue

        # Filtrar solo las filas del día solicitado
        df_day = df[df["timestamp"].dt.date == report_date.date()]

        if df_day.empty:
            report_lines.append(f"⚠️ Sin datos para la estación {station} el {report_date.date()}.\n")
            continue

        # Calcular métricas básicas
        max_wind = df_day["wind_speed"].max()
        avg_wind = df_day["wind_speed"].mean()
        last_record = df_day.iloc[-1]

        report_lines.append(
            f"📍 Estación {station} ({report_date.date()}):\n"
            f"- Velocidad máxima: {max_wind:.1f} km/h\n"
            f"- Velocidad promedio: {avg_wind:.1f} km/h\n"
            f"- Último registro: {last_record['wind_speed']:.1f} km/h "
            f"a las {last_record['timestamp'].strftime('%H:%M')}\n"
        )

    return "\n".join(report_lines)

# ========================
# 📧 Envío de correo
# ========================
def send_email(subject, body):
    correo_origen = os.environ["CORREO_ORIGEN"]
    contrasena = os.environ["CONTRASENA"]
    destinatario = os.environ["DESTINATARIO"]

    msg = MIMEMultipart()
    msg["From"] = correo_origen
    msg["To"] = destinatario
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(correo_origen, contrasena)
        server.send_message(msg)

# ========================
# 🚀 Main
# ========================
if __name__ == "__main__":
    chile_tz = pytz.timezone("America/Santiago")
    report_date = datetime.now(chile_tz) - timedelta(days=1)

    body = build_report_for_date(report_date)
    subject = f"Informe diario de viento - {report_date.strftime('%Y-%m-%d')}"

    send_email(subject, body)
    print("✅ Informe enviado correctamente.")
