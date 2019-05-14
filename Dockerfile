FROM frolvlad/alpine-python3
LABEL Caching - ON
MAINTAINER Karel Rudisar - krudisar@gmxxx.com

# --- CACHE SETTINGS ---
ENV CACHE_API_REQUESTS=1
ENV CACHE_IMAGES_IN_DB=1
# ----------------------

RUN apk add --no-cache --update python3-dev gcc build-base

RUN pip install --upgrade pip

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# set a correct timezone
ENV TZ=Europe/Prague
RUN apk add tzdata

ENTRYPOINT ["python"]
CMD ["app.py"]

