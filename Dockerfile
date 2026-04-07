FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirement.txt

EXPOSE 8501

CMD ["streamlit", "run", "frontend.py", "--server.address=0.0.0.0", "--server.port=8501"]