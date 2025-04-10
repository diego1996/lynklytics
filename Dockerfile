# Dockerfile
FROM python:3.10-slim

# Establece el directorio de trabajo en /app
WORKDIR /app

# Copia el archivo de requerimientos e instala las dependencias
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código de la aplicación al contenedor
COPY . /app/

# Cambia al directorio donde se encuentra la aplicación
WORKDIR /app/lynklytics

# Expone el puerto 8000 (ajusta según lo que necesites)
EXPOSE 8000

# Ejecuta las migraciones y levanta Gunicorn utilizando config.wsgi
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic && gunicorn config.wsgi --log-file -"]
