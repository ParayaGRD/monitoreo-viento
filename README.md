# Monitoreo de Viento - Estaciones 330021 y 330114

Este repositorio contiene un sistema de monitoreo de velocidad del viento para las estaciones meteorológicas **330021** y **330114**, que envía alertas por correo si se supera un límite definido. El sistema se ejecuta automáticamente cada 5 minutos usando **GitHub Actions**, sin necesidad de tener un PC encendido.

---

## 📂 Contenido del repositorio

- `330021.py` → Script que monitorea la estación 330021.
- `330114.py` → Script que monitorea la estación 330114.
- `.github/workflows/monitoreo.yml` → Workflow de GitHub Actions que ejecuta ambos scripts cada 5 minutos.

---

## ⚙️ Configuración de GitHub Secrets

Para proteger las credenciales de correo, se usan **GitHub Secrets**.  

En tu repositorio:

1. Ve a: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`.
2. Crea los siguientes secrets:

| Nombre           | Valor                               |
|-----------------|------------------------------------|
| `CORREO_ORIGEN` | tu correo de Gmail (ej. monitoreo.grdpudahuel@gmail.com) |
| `CONTRASENA`    | contraseña o App Password de Gmail |
| `DESTINATARIO`  | correo que recibirá las alertas (ej. correo@mpudahuel.cl) |

> **Nota:** Se recomienda usar **App Passwords de Gmail** en lugar de tu contraseña normal.

---

## 📝 Estructura del script Python

Cada script (`330021.py` y `330114.py`) realiza:

1. Obtener la velocidad del viento desde la página de MeteoChile.
2. Comparar con un límite definido (`LIMITE_VELOCIDAD = 25 kt` por defecto).
3. Si la velocidad supera el límite, enviar un correo de alerta al destinatario configurado.

Los scripts usan las variables de entorno de GitHub Secrets:

```python
import os

CORREO_ORIGEN = os.environ["CORREO_ORIGEN"]
CONTRASENA = os.environ["CONTRASENA"]
DESTINATARIO = os.environ["DESTINATARIO"]
