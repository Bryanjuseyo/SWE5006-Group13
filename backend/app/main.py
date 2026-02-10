from app.models import db
from app import create_app
from dotenv import load_dotenv
load_dotenv()


app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print('Tables created successfully')
