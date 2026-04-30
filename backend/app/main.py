from app.models import db
from app import create_app
from dotenv import load_dotenv
load_dotenv()


app = create_app()

with app.app_context():
    # Create all tables (for new databases)
    db.create_all()

    # Apply ALTER TABLE for existing databases that are missing new columns/enums
    from app.services.db_migrate import apply_migrations
    apply_migrations(db)

    print(app.url_map)
    print('Tables created successfully')
