FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        libusb-1.0-0 \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api.py utils.py OpenSans-VariableFont_wdth,wght.ttf ./

EXPOSE 8000

CMD ["python", "api.py"]