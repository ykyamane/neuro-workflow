FROM node:24-slim AS build

WORKDIR /frontend

COPY package*.json /frontend/

RUN npm ci

COPY . /frontend

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
