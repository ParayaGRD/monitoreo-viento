# Monitoreo de Viento - Estaciones 330021 y 330114

Este repositorio contiene un sistema de **monitoreo de velocidad del viento** para las estaciones meteorológicas **330021** y **330114**, que:  

- Envía **alertas por correo** si se supera un límite definido.  
- Genera un **informe diario consolidado** con valores mínimos, máximos y promedios horarios del día anterior.  
- Todo se ejecuta automáticamente en la nube mediante **GitHub Actions**, sin necesidad de tener un PC encendido.  

---

## 📂 Contenido del repositorio

- `330021.py` → Script que monitorea la estación 330021.  
- `330114.py` → Script que monitorea la estación 330114.  
- `daily_report.py` → Script que genera y envía el informe diario consolidado.  
- `.github/workflows/monitoreo.yml` → Workflow que ejecuta ambos scripts cada 10 minutos (monitoreo en tiempo real).  
- `.github/workflows/daily_report.yml` → Workflow que ejecuta el informe diario automáticamente una vez al día (08:00–09:00 hora de Santiago, UTC−4/UTC−3 según horario).  

---

## ⚙️ Configuración de GitHub Secrets

Para proteger las credenciales de correo, se usan **GitHub Secrets**.  

En tu repositorio:

1. Ve a: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`.  
2. Crea los siguientes secrets:  

| Nombre            | Valor                                                      |
|------------------|------------------------------------------------------------|
| `CORREO_ORIGEN`  | tu correo de Gmail (ej. `monitoreo.grdpudahuel@gmail.com`) |
| `CONTRASENA`     | contraseña o App Password de Gmail                         |
| `DESTINATARIOS`  | uno o más correos separados por coma (ej. `correo1@dom.cl,correo2@dom.cl`) |

> **Nota:** Ahora puedes configurar múltiples destinatarios en `DESTINATARIOS`.  

---

## 📝 Flujo de ejecución

### 1. Monitoreo en tiempo real
Cada 5 minutos se consulta la velocidad del viento en las estaciones:  
- Si la velocidad **supera el umbral definido** (`LIMITE_VELOCIDAD`, por defecto 25 kt), se envía un **correo de alerta inmediata**.  
- Si la velocidad está bajo el umbral, no se envía nada (para evitar saturación de correos).  

### 2. Informe diario consolidado
Una vez al día (entre 08:00 y 09:00, hora local de Santiago) se genera un informe que incluye:  
- Velocidad mínima registrada.  
- Velocidad máxima registrada.  
- Promedio de velocidad por hora del día anterior.  
- El informe se envía automáticamente a todos los destinatarios configurados.  

> También puedes ejecutar el workflow `daily_report.yml` manualmente desde la pestaña **Actions** si quieres generar el informe en cualquier momento.  

---

## 📧 Ejemplo de informe diario

```text
Informe diario 2025-08-31:

📍 Estación 330021
- Mínimo: 5.2 km/h
- Máximo: 48.7 km/h
- Promedio por hora:
hora
0    12.3
1    11.8
...

📍 Estación 330114
- Mínimo: 7.1 km/h
- Máximo: 52.4 km/h
- Promedio por hora:
hora
0    14.1
1    13.5
...
