from app import app, db
from models.config import SystemConfig, init_default_configs

# Initialize the database
with app.app_context():
    # Create all tables
    db.create_all()
    
    # Initialize default configurations
    init_default_configs()
    
    # Check if the workflow mode is set
    config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
    if config:
        print(f"Current workflow mode: {config.value}")
    else:
        print("WORKFLOW_MODE not found in database")
        
    # Set workflow mode to manual
    if config:
        config.value = 'manual'
        db.session.commit()
        print(f"Workflow mode updated to: {config.value}")
    
    # Verify the change
    config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
    if config:
        print(f"Verified workflow mode: {config.value}")
    else:
        print("WORKFLOW_MODE still not found in database")
