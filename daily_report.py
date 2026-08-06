import os
import re
import sys
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import pandas as pd
import pytz

# =========================
# Configuración de correo
# =========================
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]

# Permite separar destinatarios por coma, punto y coma o salto de línea
DESTINATARIOS = [
    correo.strip()
    for correo in re.split(r'[\n,;]+', os.environ["DESTINATARIOS"])
    if correo.strip()
]

# Zona horaria Chile
TZ_SANTIAGO = pytz.timezone("America/Santiago")

# =========================
# Funciones auxiliares
# =========================

def read_station_csv(file_path):
    df = pd.read_csv(file_path)

    # Normalizar nombres de columnas
    df.columns = [c.strip().lower() for c in df.columns]

    if "timestamp" not in df.columns:
        raise ValueError(f"El archivo {file_path} no tiene columna 'timestamp'.")

    # Buscar columna de velocidad de viento
    wind_col = None
    for candidate in ["wind_speed", "velocidad", "valor", "wind", "wind_kt"]:
        if candidate in df.columns:
            wind_col = candidate
            break

    if wind_col is None:
        raise ValueError(
            f"No se encontró columna de viento en {file_path}. "
            f"Columnas detectadas: {df.columns.tolist()}"
        )

    df.rename(columns={wind_col: "wind_speed"}, inplace=True)

    # Convertir timestamp a datetime con UTC
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

    # Filtrar filas válidas
    df = df.dropna(subset=["timestamp", "wind_speed"])

    return df


def build_report_for_date(date):
    files = ["data/330021.csv", "data/330114.csv"]
    report_lines = []

    date_str = date.strftime("%Y-%m-%d")
    date_display = date.strftime("%d/%m/%Y")

    report_lines.append(f"📌 Reporte Velocidad de Viento - {date_display}\n")

    for file in files:

        if not os.path.exists(file):
            report_lines.append(f"⚠️ No se encontró el archivo {file}")
            continue

        df = read_station_csv(file)

        df_day = df[df["timestamp"].dt.date == date.date()]

        if df_day.empty:
            report_lines.append(f"📭 {file}: No hay datos para {date_str}")
            continue

        max_wind = df_day["wind_speed"].max()
        mean_wind = df_day["wind_speed"].mean()

        report_lines.append(
            f"📊 {file} - {date_str}\n"
            f"• Velocidad máxima: {max_wind:.1f} kt\n"
            f"• Velocidad promedio: {mean_wind:.1f} kt\n"
        )

        df_last = df.tail(24).copy()

        df_last["timestamp"] = (
            df_last["timestamp"]
            .dt.tz_convert(TZ_SANTIAGO)
            .dt.strftime("%Y-%m-%d %H:%M")
        )

        report_lines.append(
            f"📄 Últimos 24 registros {os.path.basename(file).replace('.csv','')}:"
        )

        for _, row in df_last.iterrows():
            report_lines.append(
                f"{row['timestamp']} - {row['wind_speed']} kt"
            )

        report_lines.append("")

    return "\n".join(report_lines)


def send_email(subject, body):

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = CORREO_ORIGEN
    msg["To"] = ", ".join(DESTINATARIOS)
    msg["Subject"] = subject

    print("===================================")
    print("Destinatarios:")
    for correo in DESTINATARIOS:
        print(f" - {correo}")
    print("===================================")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(CORREO_ORIGEN, CONTRASENA)
        print("✅ Login SMTP correcto.")
        server.sendmail(
            CORREO_ORIGEN,
            DESTINATARIOS,
            msg.as_string()
        )


# =========================
# Script principal
# =========================

if __name__ == "__main__":

    report_date = datetime.now(TZ_SANTIAGO) - timedelta(days=1)

    try:

        body = build_report_for_date(report_date)

        subject = (
            f"Informe diario de viento - "
            f"{report_date.strftime('%Y-%m-%d')}"
        )

        send_email(subject, body)

        print("✅ Informe enviado con éxito.")

    except Exception as e:
        print(f"❌ Error al generar o enviar el informe: {e}")
        sys.exit(1)
