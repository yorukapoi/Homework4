FROM node:18-alpine

WORKDIR /app

# API gateway URL is injected via build arg / env
ARG API_URL
ENV NEXT_PUBLIC_API_URL=$API_URL

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]


