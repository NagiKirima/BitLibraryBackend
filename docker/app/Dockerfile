FROM python:3.10-slim

COPY app/requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir
RUN chmod 755 .
COPY app/ .
ENV PYTHONPATH "${PYTHONPATH}:."

CMD ["python", "app.py"]