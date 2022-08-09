FROM python:3
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
#ENV PYTHONPATH ./
CMD [ "python", "./server.py"]