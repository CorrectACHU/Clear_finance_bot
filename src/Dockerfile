FROM python:3
WORKDIR /app/src
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY .. .
EXPOSE 80
CMD [ "python", "./main.py" ]