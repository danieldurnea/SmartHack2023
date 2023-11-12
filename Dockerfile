FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN mkdir /code
WORKDIR /code
COPY ./django/smarthack /code
RUN pip install -r requirements.txt
RUN pip install mysqlclient django-redis redis django-debug-toolbar djangorestframework django-cors-headers openai
RUN pip install requests
RUN pip install insta-scrape
RUN pip install google-cloud-language
ENV GOOGLE_APPLICATION_CREDENTIALS="/code/service-key.json"
RUN pip install selenium==4.15.2
RUN apt-get install -y wget
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list
RUN apt-get update && apt-get -y install google-chrome-stable
RUN pip install webdriver-manager