FROM node:24-alpine
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
COPY docs/contracts /docs/contracts
ENV VITE_API_PROXY_TARGET=http://api:8000
CMD ["npm","run","dev:container"]
