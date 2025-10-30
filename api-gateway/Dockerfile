FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# VIGTIGT: Kopiér hele mappen
COPY . .

ENV PYTHONUNBUFFERED=1
CMD ["python", "-u", "app.py"]
EXPOSE 5000
