FROM tiangolo/uwsgi-nginx-flask:python3.6

RUN apt-get update
RUN apt-get remove -y yarn cmdtest
RUN apt-get install -y curl
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb http://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update
RUN apt-get install -y yarn
RUN cd /app && yarn install

RUN pip3 install flask-sqlalchemy
RUN pip3 install git+https://github.com/RyanSquared/gigaspoon
RUN pip3 install boto3
RUN pip3 install psycopg2
RUN pip3 install pymysql
RUN pip3 install raven[flask]

ENV STATIC_PATH /app/noticast_web/static

COPY . /app
