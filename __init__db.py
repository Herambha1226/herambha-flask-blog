from app.main import app, db

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Tables created successfully!")
