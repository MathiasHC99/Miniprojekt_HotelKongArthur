FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask pandas requests
EXPOSE 5005
CMD ["python", "app.py"]
