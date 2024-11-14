FROM swaggerapi/swagger-ui:latest

# Copia il file swagger.json nella cartella di Swagger UI
COPY static/swagger.json /usr/share/nginx/html/static/swagger.json

EXPOSE 8080

# Configura l'applicazione per usare swagger.json
ENV SWAGGER_JSON /usr/share/nginx/html/static/swagger.json