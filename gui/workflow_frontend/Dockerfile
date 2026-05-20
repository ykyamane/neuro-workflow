FROM node:24-slim

WORKDIR /frontend

COPY package*.json /frontend/

RUN npm install

COPY . /frontend

CMD ["npm", "run", "dev:docker"]
