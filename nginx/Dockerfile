FROM nginx:1.25

WORKDIR /opt/app

COPY ./nginx.conf /etc/nginx/nginx.conf
COPY ./site.conf /etc/nginx/conf.d

EXPOSE 80

RUN rm -rf /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]