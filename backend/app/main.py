from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print(app.url_map)
    print('Tables created successfully')
