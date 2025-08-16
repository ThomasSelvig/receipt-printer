# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
# USER appuser

# Install udev and create dialout group with same GID as host
RUN apt-get update && apt-get install -y udev && rm -rf /var/lib/apt/lists/*

# Create dialout group with GID 20 (standard on most systems)
RUN groupadd -g 20 dialout || true

# Create user with UID 1000 and add to dialout group
RUN useradd -u 1000 -g 1000 -G dialout appuser || usermod -a -G dialout appuser

RUN chown -R 1000:1000 /app
USER 1000:1000

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "bot.py"]
