from datetime import datetime
import os
import time
import requests
import urllib3
from bs4 import BeautifulSoup

# Desactivar advertencias de certificados SSL autofirmados
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN POR VARIABLES DE ENTORNO ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Validación para asegurar que las variables están configuradas en el entorno
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError(
        "❌ Error: Faltan las variables de entorno TELEGRAM_BOT_TOKEN o"
        " TELEGRAM_CHAT_ID."
    )

URL_PRINCIPAL = (
    "https://ieshotelescuela.myqnapcloud.com:8081/Reservas/ReservasMenu.php"
)
URL_AJAX = (
    "https://ieshotelescuela.myqnapcloud.com:8081/Reservas/calendarioReservasAjax.php"
)

# Intervalo de comprobación en segundos (ej. cada 5 minutos = 300 segundos)
INTERVALO_SEGUNDOS = 300

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": URL_PRINCIPAL,
}

# --- SISTEMA DE LOGS POR SEMANAS ---
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

def escribir_log(mensaje):
  ahora = datetime.now()
  # Obtenemos año y número de semana (ej: 2026 y semana 46 -> log_2026_W46.txt)
  año, semana, _ = ahora.isocalendar()
  nombre_archivo = f"log_{año}_W{semana:02d}.txt"
  ruta_archivo = os.path.join(LOG_DIR, nombre_archivo)

  linea = f"[{ahora}] {mensaje}"
  print(linea, flush=True)  # Muestra en consola de Docker de forma inmediata

  try:
    with open(ruta_archivo, "a", encoding="utf-8") as f:
      f.write(linea + "\n")
  except Exception as e:
    print(f"[{ahora}] ❌ Error al escribir en el archivo de log: {e}", flush=True)


def enviar_alerta_telegram(mensaje):
  url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": TELEGRAM_CHAT_ID,
      "text": mensaje,
      "parse_mode": "Markdown",
  }
  try:
    response = requests.post(url_api, data=payload, timeout=10)
    if response.status_code == 200:
      escribir_log("Alerta enviada con éxito por Telegram.")
      return True
    else:
      escribir_log(
          f"❌ Error al enviar Telegram (Código {response.status_code}):"
          f" {response.text}"
      )
      return False
  except Exception as e:
    escribir_log(f"❌ Excepción al conectar con Telegram: {e}")
    return False


def obtener_siguiente_mes(año, mes):
  if mes == 12:
    return año + 1, 1
  else:
    return año, mes + 1


def obtener_dias_mes(año, mes):
  payload = {"mes": mes, "ano": año}
  dias_set = set()
  try:
    response = requests.post(
        URL_AJAX, headers=HEADERS, data=payload, timeout=15, verify=False
    )
    if response.status_code != 200 or not response.text.strip():
      response = requests.get(
          URL_AJAX, headers=HEADERS, params=payload, timeout=15, verify=False
      )

    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      dias_disponibles = soup.find_all("td", class_="diavalidor")
      for d in dias_disponibles:
        texto_dia = d.get_text(strip=True)
        dias_set.add(f"{año}-{mes:02d}-{texto_dia}")
      return dias_set
    else:
      escribir_log(f"Error HTTP al consultar mes {mes}/{año}: Código {response.status_code}")
      return None

  except Exception as e:
    escribir_log(f"Error de conexión al consultar mes {mes}/{año}: {e}")

    return None


def monitorizar():
  estado_anterior = set()
  escribir_log("--- Bot Monitor de Reservas (Logs Semanales) Iniciado ---")

  while True:
    ahora = datetime.now()
    año_actual, mes_actual = ahora.year, ahora.month
    año_siguiente, mes_siguiente = obtener_siguiente_mes(
        año_actual, mes_actual
    )

    escribir_log(
        f"Comprobando meses: {mes_actual}/{año_actual} y"
        f" {mes_siguiente}/{año_siguiente}..."
    )

    dias_actual_set = obtener_dias_mes(año_actual, mes_actual)
    dias_siguiente_set = obtener_dias_mes(año_siguiente, mes_siguiente)

    if dias_actual_set is None or dias_siguiente_set is None:
      escribir_log("⚠️ La web no responde correctamente. Omitiendo ciclo.")
      time.sleep(INTERVALO_SEGUNDOS)
      continue

    estado_actual = dias_actual_set.union(dias_siguiente_set)

    if estado_actual != estado_anterior:
      if estado_actual:
        mensaje = (
            "🚨 *¡Cambio en la disponibilidad de reservas!*\n\nSe han"
            f" detectado {len(estado_actual)} días libres."
            f" \nFechas/Días detectados:"
            f" `{sorted(list(estado_actual))}`\n\n🔗 [Acceder a la"
            f" web]({URL_PRINCIPAL})"
        )
        enviar_alerta_telegram(mensaje)
        escribir_log(f"¡Novedad detallada notificada con éxito por Telegram! {sorted(list(estado_actual))}")

      else:
        escribir_log("Las plazas disponibles se han agotado. Actualizando estado.")

      estado_anterior = estado_actual
    else:
      escribir_log("Sin cambios en la disponibilidad respecto a la última comprobación.")

    time.sleep(INTERVALO_SEGUNDOS)

if __name__ == "__main__":
  monitorizar()
