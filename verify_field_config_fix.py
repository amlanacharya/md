"""
Comprehensive verification script for field configuration fixes.
"""
from app import app, db
from models.config import FieldConfig
from services.field_service import FieldService

def verify_field_config_updates():
    """Verify that field configuration updates work correctly."""
    with app.app_context():
        print("=== Testing Field Configuration Updates ===")
        
        # Get all field configurations
        field_configs = FieldService.get_all_field_configs()
        if not field_configs:
            print("No field configurations found.")
            return False
        
        # Select a test field
        test_field = field_configs[0]
        print(f"Testing with field: {test_field.field_name} (ID: {test_field.id})")
        print(f"Current values: required={test_field.is_required}, visible={test_field.is_visible}")
        
        # Toggle the is_required value
        original_required = test_field.is_required
        new_required = not original_required
        print(f"Setting is_required to {new_required}")
        
        # Update the field configuration
        result = FieldService.update_field_config(
            test_field.id,
            new_required,
            test_field.is_visible,
            test_field.maker_can_edit,
            test_field.checker_can_edit,
            test_field.author_can_edit
        )
        
        if not result:
            print("❌ Failed to update field configuration.")
            return False
        
        # Verify the change by querying the database directly
        db.session.expire_all()  # Clear the session cache
        updated_field = FieldConfig.query.get(test_field.id)
        
        if not updated_field:
            print("❌ Failed to find the updated field.")
            return False
        
        print(f"Updated values: required={updated_field.is_required}, visible={updated_field.is_visible}")
        
        # Check if the update was successful
        if updated_field.is_required == new_required:
            print("✅ Test passed: Field configuration updated successfully!")
        else:
            print("❌ Test failed: Field configuration not updated correctly.")
            return False
        
        # Reset to original value
        print("Resetting to original value...")
        result = FieldService.update_field_config(
            test_field.id,
            original_required,
            test_field.is_visible,
            test_field.maker_can_edit,
            test_field.checker_can_edit,
            test_field.author_can_edit
        )
        
        if not result:
            print("❌ Failed to reset field configuration.")
            return False
        
        # Verify the reset
        db.session.expire_all()  # Clear the session cache
        reset_field = FieldConfig.query.get(test_field.id)
        
        if not reset_field:
            print("❌ Failed to find the reset field.")
            return False
        
        print(f"Reset values: required={reset_field.is_required}, visible={reset_field.is_visible}")
        
        # Check if the reset was successful
        if reset_field.is_required == original_required:
            print("✅ Test passed: Field configuration reset successfully!")
            return True
        else:
            print("❌ Test failed: Field configuration not reset correctly.")
            return False

def verify_field_config_persistence():
    """Verify that field configuration changes persist across sessions."""
    with app.app_context():
        print("\n=== Testing Field Configuration Persistence ===")
        
        # Get all field configurations
        field_configs = FieldService.get_all_field_configs()
        if not field_configs:
            print("No field configurations found.")
            return False
        
        # Select a test field
        test_field = field_configs[1]  # Use a different field than the first test
        print(f"Testing with field: {test_field.field_name} (ID: {test_field.id})")
        print(f"Current values: required={test_field.is_required}, visible={test_field.is_visible}")
        
        # Toggle the is_required value
        original_required = test_field.is_required
        new_required = not original_required
        print(f"Setting is_required to {new_required}")
        
        # Update the field configuration
        result = FieldService.update_field_config(
            test_field.id,
            new_required,
            test_field.is_visible,
            test_field.maker_can_edit,
            test_field.checker_can_edit,
            test_field.author_can_edit
        )
        
        if not result:
            print("❌ Failed to update field configuration.")
            return False
        
        # Close and reopen the session to simulate a new request
        db.session.close()
        
        # Verify the change persists after reopening the session
        with app.app_context():
            # Get the field configuration again
            persisted_field = FieldConfig.query.get(test_field.id)
            
            if not persisted_field:
                print("❌ Failed to find the field after reopening session.")
                return False
            
            print(f"Persisted values: required={persisted_field.is_required}, visible={persisted_field.is_visible}")
            
            # Check if the update persisted
            if persisted_field.is_required == new_required:
                print("✅ Test passed: Field configuration persisted across sessions!")
            else:
                print("❌ Test failed: Field configuration did not persist across sessions.")
                return False
            
            # Reset to original value
            print("Resetting to original value...")
            result = FieldService.update_field_config(
                test_field.id,
                original_required,
                test_field.is_visible,
                test_field.maker_can_edit,
                test_field.checker_can_edit,
                test_field.author_can_edit
            )
            
            if not result:
                print("❌ Failed to reset field configuration.")
                return False
            
            # Verify the reset
            db.session.expire_all()  # Clear the session cache
            reset_field = FieldConfig.query.get(test_field.id)
            
            if not reset_field:
                print("❌ Failed to find the reset field.")
                return False
            
            print(f"Reset values: required={reset_field.is_required}, visible={reset_field.is_visible}")
            
            # Check if the reset was successful
            if reset_field.is_required == original_required:
                print("✅ Test passed: Field configuration reset successfully!")
                return True
            else:
                print("❌ Test failed: Field configuration not reset correctly.")
                return False

if __name__ == "__main__":
    print("Field Configuration Fix Verification")
    print("===================================")
    
    update_success = verify_field_config_updates()
    persistence_success = verify_field_config_persistence()
    
    if update_success and persistence_success:
        print("\n✅ All tests passed! The field configuration fix is working correctly.")
    else:
        print("\n❌ Some tests failed. The field configuration fix may not be working correctly.")
