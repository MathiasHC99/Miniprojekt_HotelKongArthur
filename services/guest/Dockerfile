FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5003
CMD ["python", "app.py"]
