from app import app, db
from models.config import SystemConfig
from services.workflow_service import WorkflowService

# Add debug logging to WorkflowService.set_workflow_mode
original_set_workflow_mode = WorkflowService.set_workflow_mode

def debug_set_workflow_mode(mode):
    print(f"Debug: WorkflowService.set_workflow_mode called with mode={mode}")
    
    # Get current mode before update
    with app.app_context():
        config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
        current_mode = config.value if config else "Not set"
        print(f"Debug: Current mode before update: {current_mode}")
    
    # Call original method
    result = original_set_workflow_mode(mode)
    
    # Get mode after update
    with app.app_context():
        config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
        new_mode = config.value if config else "Not set"
        print(f"Debug: Mode after update: {new_mode}")
        print(f"Debug: Update result: {result}")
    
    return result

# Replace the original method with our debug version
WorkflowService.set_workflow_mode = debug_set_workflow_mode

print("Debug hooks installed for WorkflowService.set_workflow_mode")
print("Now run the application and try to change the workflow mode from the UI")
print("Check the console for debug output")
