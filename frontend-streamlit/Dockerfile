FROM python:3.11-slim
WORKDIR /app
COPY . .
ENV API_URL=http://gateway:8000/api
RUN pip install streamlit requests pandas altair
EXPOSE 8501
CMD ["streamlit", "run", "home2.py", "--server.port=8501", "--server.address=0.0.0.0"]
