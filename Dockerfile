FROM python:3.12.2 AS PackageBuilder
COPY ./requirements.txt ./requirements.txt
RUN pip3 wheel -r requirements.txt


FROM python:3.12.2-slim
EXPOSE 80

# Setup user
ENV UID=2000
ENV GID=2000

RUN groupadd -g "${GID}" python \
  && useradd --create-home --no-log-init --shell /bin/bash -u "${UID}" -g "${GID}" python

USER python
WORKDIR /home/python

RUN mkdir ./wheels
COPY --from=PackageBuilder ./*.whl ./wheels/
RUN pip3 install ./wheels/*.whl --no-warn-script-location

COPY setup.py ./
COPY ./app ./app
RUN pip3 install .


CMD PATH=$PATH:/home/python/.local/bin && \
    cd app/db && \
    alembic -c ./alembic.prod.ini upgrade head && \
    cd /home/python && \
    gunicorn app.main:fastapi_app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:80
