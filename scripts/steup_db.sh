#!/bin/bash

echo "Initializing database..."

# Create the database
docker-compose exec db psql -U postgres -c "CREATE DATABASE aquavision;"

# Run migrations
docker-compose exec backend flask db init
docker-compose exec backend flask db migrate -m "Initial migration"
docker-compose exec backend flask db upgrade

# Create admin user
docker-compose exec backend python -c "
from app.models.user import User
from app.extensions import db
admin = User(name='Admin', email='admin@aquavision.ai')
admin.set_password('adminpassword')
db.session.add(admin)
db.session.commit()
print('Admin user created')"

echo "Database setup completed successfully."