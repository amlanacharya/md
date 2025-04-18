from app import app, db
from models.config import SystemConfig

# Set workflow mode to auto
with app.app_context():
    config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
    if config:
        config.value = 'auto'
        db.session.commit()
        print(f'Workflow mode updated to: {config.value}')
    else:
        print('WORKFLOW_MODE configuration not found')
