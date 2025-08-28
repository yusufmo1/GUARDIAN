# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:1.25-alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy favicon and static assets
COPY --from=build /app/static/favicon* /usr/share/nginx/html/
COPY --from=build /app/static/*.png /usr/share/nginx/html/
COPY --from=build /app/static/*.svg /usr/share/nginx/html/
COPY --from=build /app/static/*.ico /usr/share/nginx/html/

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]