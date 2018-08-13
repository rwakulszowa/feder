FROM python:2

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
COPY requirements/ /usr/src/app/requirements/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app


COPY start.sh /start.sh

CMD ["/start.sh"]


