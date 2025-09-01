# daily_report.py
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config
CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]

def obtener_destinatarios():
    raw = os.environ.get("DESTINATARIOS") or os.environ.get("DESTINATARIO")
    if not raw:
        raise RuntimeError("No se encontró DESTINATARIOS ni DESTINATARIO")
    return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]

DESTINATARIOS = obtener_destinatarios()
TZ = ZoneInfo("America/Santiago")

def read_station_csv(station_id):
    path = f"data/{station_id}.csv"
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["timestamp"])
    # Asegurar tz-aware: si no tiene tz, consideramos que está en UTC y lo convertimos a TZ local
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC").dt.tz_convert(TZ)
    else:
        df["timestamp"] = df["timestamp"].dt.tz_convert(TZ)
    df = df.set_index("timestamp").sort_index()
    return df

def hourly_stats_for_date(df, date_local):
    start = datetime(date_local.year, date_local.month, date_local.day, tzinfo=TZ)
    end = start + timedelta(days=1)
    df_day = df.loc[(df.index >= start) & (df.index < end)]
    if df_day.empty:
        return None
    hourly = df_day["wind_kt"].resample("H").agg(["min", "max", "mean"])
    hourly["mean_ma3"] = hourly["mean"].rolling(window=3, min_periods=1).mean()
    return hourly

def build_report_for_date(date_local):
    stations = ["330021", "330114"]
    parts = []
    for s in stations:
        df = read_station_csv(s)
        parts.append(f"--- Estación {s} ---")
        if df is None:
            parts.append("No hay datos (archivo faltante).")
            continue
        stats = hourly_stats_for_date(df, date_local)
        if stats is None:
            parts.append("No se encontraron registros para la fecha.")
            continue
        parts.append("Hora (local) | min(kt) | max(kt) | mean(kt) | mean_MA3(kt)")
        for idx, row in stats.iterrows():
            hour_label = idx.strftime("%Y-%m-%d %H:%M")
            parts.append(f"{hour_label} | {row['min']:.1f} | {row['max']:.1f} | {row['mean']:.2f} | {row['mean_ma3']:.2f}")
    return "\n".join(parts)

def enviar_correo(subject, body):
    msg = MIMEMultipart()
    msg["From"] = CORREO_ORIGEN
    msg["To"] = ", ".join(DESTINATARIOS)
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login(CORREO_ORIGEN, CONTRASENA)
    s.sendmail(CORREO_ORIGEN, DESTINATARIOS, msg.as_string())
    s.quit()

if __name__ == "__main__":
    now = datetime.now(TZ)

    # Generar informe del día anterior (fecha local)
    report_date = (now - timedelta(days=1)).date()
    body = f"Informe diario para la fecha {report_date.isoformat()} (horas locales, America/Santiago)\n\n"
    body += build_report_for_date(report_date)
    subject = f"Informe diario de viento - {report_date.isoformat()}"
    enviar_correo(subject, body)
    print("✅ Informe diario enviado.")
