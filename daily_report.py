import os
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------
# Configuración de correo
# -----------------------------
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]
DESTINATARIO = os.environ["DESTINATARIO"]

# Carpeta donde se guardan los datos
DATA_FOLDER = "data"

# -----------------------------
# Función: Leer CSV y normalizar
# -----------------------------
def read_station_csv(file_path):
    df = pd.read_csv(file_path)

    # Normalizar nombres de columnas
    df.columns = [c.strip().lower() for c in df.columns]

    # Verificar columna timestamp
    if "timestamp" not in df.columns:
        raise ValueError(f"El archivo {file_path} no tiene columna 'timestamp'.")

    # Buscar columna de velocidad de viento
    wind_col = None
    for candidate in ["wind_speed", "velocidad", "valor", "wind", "wind_kt"]:
        if candidate in df.columns:
            wind_col = candidate
            break

    if wind_col is None:
        raise ValueError(f"No se encontró columna de viento en {file_path}. Columnas detectadas: {df.columns.tolist()}")

    # Renombrar a wind_speed para trabajar uniforme
    df.rename(columns={wind_col: "wind_speed"}, inplace=True)

    # Convertir timestamp a datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # Filtrar filas válidas
    df = df.dropna(subset=["timestamp", "wind_speed"])

    return df

# -----------------------------
# Función: Generar reporte diario
# -----------------------------
def build_report_for_date(date):
    report_lines = [f"📊 Informe diario de viento ({date.date()})\n"]

    for station_file in os.listdir(DATA_FOLDER):
        if not station_file.endswith(".csv"):
            continue

        station_id = station_file.replace(".csv", "")
        file_path = os.path.join(DATA_FOLDER, station_file)

        df = read_station_csv(file_path)

        # Filtrar por la fecha indicada
        df_day = df[df["timestamp"].dt.date == date.date()]
        if df_day.empty:
            report_lines.append(f"\n🌐 Estación {station_id}: Sin datos para este día.")
            continue

        # Cálculos básicos
        max_wind = df_day["wind_speed"].max()
        min_wind = df_day["wind_speed"].min()
        avg_wind = df_day["wind_speed"].mean()

        # Promedios horarios
        hourly_avg = df_day.groupby(df_day["timestamp"].dt.hour)["wind_speed"].mean()

        report_lines.append(f"\n🌐 Estación {station_id}:")
        report_lines.append(f"   ➡️ Velocidad máxima: {max_wind:.2f} kt")
        report_lines.append(f"   ➡️ Velocidad mínima: {min_wind:.2f} kt")
        report_lines.append(f"   ➡️ Velocidad promedio: {avg_wind:.2f} kt")
        report_lines.append("   ⏰ Promedios por hora:")
        for hour, value in hourly_avg.items():
            report_lines.append(f"      - {hour:02d}:00 → {value:.2f} kt")

    return "\n".join(report_lines)

# -----------------------------
# Función: Enviar correo
# -----------------------------
def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = CORREO_ORIGEN
    msg["To"] = DESTINATARIO
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(CORREO_ORIGEN, CONTRASENA)
        server.send_message(msg)

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    report_date = datetime.now() - timedelta(days=1)  # Informe del día anterior
    body = build_report_for_date(report_date)
    subject = f"📩 Informe diario de viento - {report_date.date()}"

    print(body)  # Para debug en logs
    send_email(subject, body)
