from app import app, db
from models.config import SystemConfig

with app.app_context():
    config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
    print(f'Current workflow mode: {config.value if config else "Not set"}')
