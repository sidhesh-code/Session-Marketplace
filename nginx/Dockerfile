FROM nginx:alpine

ENV BACKEND_HOST=backend \
    FRONTEND_HOST=frontend

COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
