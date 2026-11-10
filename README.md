# 🍽️ Monitor de Reservas - IES Hotel Escuela

Script en Python diseñado para monitorizar de forma automática y recurrente la disponibilidad de reservas en la web del **IES Hotel Escuela**, enviando alertas instantáneas a través de un bot de Telegram únicamente cuando se detectan cambios reales en las fechas libres.

## 🚀 Características

* **Consulta Multimes**: Comprueba automáticamente tanto el mes en curso como el mes siguiente mediante peticiones AJAX simuladas.
* **Control de Cambios Inteligente**: Evita el spam de notificaciones. Solo envía un mensaje a Telegram cuando hay una novedad (nuevas fechas disponibles o plazas agotadas).
* **Protección Anti-caídas**: Si el servidor del QNAP no responde o da timeout, el script omite el ciclo de forma segura sin vaciar su memoria de estado, evitando falsos positivos al recuperarse.
* **Preparado para Contenedores**: Diseñado para ejecutarse de manera ligera y permanente 24/7 en servidores Docker / Portainer.

## ChangeLogs
V1.1 - Start
V1.2 - Added smart notification
V1.3 - Added weekly log

---

## 🛠️ Estructura del Repositorio

Tu repositorio debe contener los siguientes archivos:
```text
├── monitor_reservas.py    # Script principal de Python
├── requirements.txt       # Dependencias necesarias
├── Dockerfile             # Configuración para empaquetar la imagen Docker
└── docker-compose.yml     # Definición del stack para Portainer



