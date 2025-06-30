FROM node:lts AS node

RUN cd / && git clone https://github.com/NENightElves/tokenfileserver.git && cd /tokenfileserver && make && \
    mkdir server && cp main.py server && cp -r static server

FROM python:3.12
RUN pip install flask==3.1.0 flasgger==0.9.7.1
COPY --from=node /tokenfileserver/server /app
WORKDIR /app
ENTRYPOINT [ "python", "main.py" ]
