"""
Test script to verify the field configuration fix.
"""
from app import app
from services.field_service import FieldService

def test_field_config_persistence():
    """Test that field configuration changes persist."""
    with app.app_context():
        # Get all field configurations
        field_configs = FieldService.get_all_field_configs()
        
        if not field_configs:
            print("No field configurations found.")
            return
        
        print(f"Found {len(field_configs)} field configurations.")
        
        # Find a field that is currently required
        required_field = None
        for field in field_configs:
            if field.is_required:
                required_field = field
                break
        
        if not required_field:
            print("No required field found to test with.")
            return
        
        print(f"Testing with field: {required_field.field_name} (ID: {required_field.id})")
        print(f"Current values: required={required_field.is_required}, visible={required_field.is_visible}")
        
        # Toggle the is_required value
        new_is_required = not required_field.is_required
        print(f"Setting is_required to {new_is_required}")
        
        # Update the field configuration
        result = FieldService.update_field_config(
            required_field.id,
            new_is_required,
            required_field.is_visible,
            required_field.maker_can_edit,
            required_field.checker_can_edit,
            required_field.author_can_edit
        )
        
        if not result:
            print("❌ Failed to update field configuration.")
            return
        
        # Get the field configurations again to verify the change persisted
        field_configs = FieldService.get_all_field_configs()
        updated_field = None
        for field in field_configs:
            if field.id == required_field.id:
                updated_field = field
                break
        
        if not updated_field:
            print("❌ Failed to find the updated field.")
            return
        
        print(f"Updated values: required={updated_field.is_required}, visible={updated_field.is_visible}")
        
        # Check if the update was successful
        if updated_field.is_required == new_is_required:
            print("✅ Test passed: Field configuration updated successfully and persisted!")
        else:
            print("❌ Test failed: Field configuration not updated or not persisted.")
        
        # Reset to original value
        print("Resetting to original value...")
        FieldService.update_field_config(
            required_field.id,
            required_field.is_required,
            required_field.is_visible,
            required_field.maker_can_edit,
            required_field.checker_can_edit,
            required_field.author_can_edit
        )

if __name__ == "__main__":
    test_field_config_persistence()
