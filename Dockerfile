FROM python:3.8.5-slim-buster

ENV PIP_NO_CACHE_DIR=1

# Repoint apt sources to the Debian archive since Buster is EOL and removed
# from the standard mirrors
RUN sed -i 's|deb.debian.org|archive.debian.org|g; s|security.debian.org|archive.debian.org/debian-security|g' /etc/apt/sources.list

# Install git and other needed tools
RUN apt-get update && apt-get install -y git gcc && apt-get clean

# Upgrade pip and setuptools
RUN pip3 install --upgrade pip setuptools

# Copy application code
COPY . /app/

# Set working directory
WORKDIR /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir -U -r requirements.txt

# Run the bot
CMD ["python3", "-m", "TEAMZYRO"]
