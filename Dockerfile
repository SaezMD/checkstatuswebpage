FROM python:3.11-slim

WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el script de Python
COPY monitor_reservas.py .

# Ejecutar el script
CMD ["python", "monitor_reservas.py"]
