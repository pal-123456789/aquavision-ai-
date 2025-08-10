#!/bin/bash

# Build and start containers
docker-compose up -d --build

# Run database migrations
docker-compose exec backend flask db init
docker-compose exec backend flask db migrate
docker-compose exec backend flask db upgrade

echo "Deployment completed successfully!"