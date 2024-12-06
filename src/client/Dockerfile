# Dockerfile
FROM php:8.1-apache

# Install dependencies
RUN apt-get update && apt-get install -y libcurl4-openssl-dev

# Install PHP extensions
RUN docker-php-ext-install curl

# COPY . /var/www/html/
EXPOSE 80