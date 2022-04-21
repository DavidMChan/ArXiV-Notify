# Copyright (c) 2022 David Chan
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

FROM --platform=linux/amd64 python:3.8-alpine

RUN pip install python-dateutil requests

COPY ./arxivnotify.py /app/arxivnotify.py
COPY ./configparse.py /app/configparse.py
COPY ./arxivnotify.cfg /app/arxivnotify.cfg

WORKDIR /app

CMD ["python", "arxivnotify.py"]
