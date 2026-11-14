# Circuit Coach prototype, built and served as static files.
#   docker build -t circuit-coach-app --build-arg VITE_API_URL=http://localhost:8000 frontend
#   docker run -p 8080:80 circuit-coach-app             # http://localhost:8080
# Without VITE_API_URL the prototype uses its in-browser engine, like the deployed demo.

FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=""
ARG VITE_ENGINE_MODEL=""
ENV VITE_API_URL=$VITE_API_URL \
    VITE_ENGINE_MODEL=$VITE_ENGINE_MODEL
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
