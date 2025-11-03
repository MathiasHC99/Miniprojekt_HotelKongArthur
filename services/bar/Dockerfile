FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask pandas
EXPOSE 5002
CMD ["python", "app.py"]
