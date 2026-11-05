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
      print(f"[{datetime.now()}] Alerta enviada con éxito por Telegram.")
    else:
      print(
          f"[{datetime.now()}] Error al enviar Telegram:"
          f" {response.status_code} - {response.text}"
      )
  except Exception as e:
    print(f"[{datetime.now()}] Excepción al conectar con Telegram: {e}")


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
      print(
          f"[{datetime.now()}] Error HTTP al consultar mes {mes}/{año}:"
          f" {response.status_code}"
      )
      return None

  except Exception as e:
    print(
        f"[{datetime.now()}] Error de conexión al consultar mes {mes}/{año}:"
        f" {e}"
    )
    return None


def monitorizar():
  estado_anterior = set()

  print(
      "--- Bot Monitor de Reservas (Entorno Docker) Iniciado ---"
  )

  while True:
    ahora = datetime.now()
    año_actual, mes_actual = ahora.year, ahora.month
    año_siguiente, mes_siguiente = obtener_siguiente_mes(
        año_actual, mes_actual
    )

    print(
        f"[{datetime.now()}] Comprobando meses: {mes_actual}/{año_actual} y"
        f" {mes_siguiente}/{año_siguiente}..."
    )

    dias_actual_set = obtener_dias_mes(año_actual, mes_actual)
    dias_siguiente_set = obtener_dias_mes(año_siguiente, mes_siguiente)

    if dias_actual_set is None or dias_siguiente_set is None:
      print(
          f"[{datetime.now()}] ⚠️ La web no responde correctamente. Omitiendo"
          " ciclo y manteniendo estado anterior intacto."
      )
      time.sleep(INTERVALO_SEGUNDOS)
      continue

    estado_actual = dias_actual_set.union(dias_siguiente_set)

    if estado_actual != estado_anterior:
      if estado_actual:
        mensaje = (
            "🚨 *¡Cambio en la disponibilidad de reservas!*\n\nSe han"
            f" detectado {len(estado_actual)} días libres"
            f" (`diavalidor`).\nFechas/Días detectados:"
            f" `{sorted(list(estado_actual))}`\n\n🔗 [Acceder a la"
            f" web]({URL_PRINCIPAL})"
        )
        enviar_alerta_telegram(mensaje)
        print(
            f"[{datetime.now()}] ¡Novedad! Disponibilidad modificada."
            f" Notificación enviada."
        )
      else:
        print(
            f"[{datetime.now()}] Las plazas disponibles se han agotado."
            " Actualizando estado."
        )

      estado_anterior = estado_actual
    else:
      print(
          f"[{datetime.now()}] Sin cambios en la disponibilidad respecto a la"
          " última comprobación."
      )

    time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
  monitorizar()
