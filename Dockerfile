FROM python:3.9

RUN apt-get update -y && apt-get upgrade -y

RUN curl -sL https://deb.nodesource.com/setup_17.x | bash -

RUN apt-get install -y nodejs

ENV PATH $PATH:/node_modules/.bin

COPY package.json /

RUN npm install && npm cache clean --force

WORKDIR /app

RUN useradd -m user

USER user

ENV PATH="/home/user/.local/bin:${PATH}"

COPY requirements.txt /app

RUN python -m pip install --upgrade pip

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["/bin/bash"]
