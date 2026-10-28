# development usa Node.js y live-server para servir la web y detectar cambios
# production usa Nginx y copia solo el HTML, CSS y el logo -> Nginx escucha en el puerto 80 dentro del contenedor

# Stage 1: Development
FROM node:22-alpine AS development

WORKDIR /app

# Servidor estático de desarrollo con recarga automática
RUN npm install --global live-server

COPY . .

EXPOSE 8080

CMD ["live-server", "--host=0.0.0.0", "--port=8080", "--no-browser", "--watch=."]
 
# Stage 2: Production
FROM nginx:alpine AS production

# Eliminar la página por defecto de Nginx
RUN rm -rf /usr/share/nginx/html/*

# Copiar únicamente los archivos estáticos necesarios
COPY index.html /usr/share/nginx/html/index.html
COPY css/ /usr/share/nginx/html/css/
COPY MiGaraje.png /usr/share/nginx/html/MiGaraje.png

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]