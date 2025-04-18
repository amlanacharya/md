"""
Test script to verify field configuration updates.
"""
from app import app, db
from models.config import FieldConfig
from services.field_service import FieldService

def test_field_config_update():
    """Test updating field configurations."""
    with app.app_context():
        # Get all field configurations
        field_configs = FieldService.get_all_field_configs()
        
        if not field_configs:
            print("No field configurations found.")
            return
        
        # Select a field to test with
        test_field = field_configs[0]
        print(f"Testing with field: {test_field.field_name} (ID: {test_field.id})")
        print(f"Current values: required={test_field.is_required}, visible={test_field.is_visible}")
        
        # Toggle the is_required value
        new_is_required = not test_field.is_required
        print(f"Setting is_required to {new_is_required}")
        
        # Update the field configuration
        result = FieldService.update_field_config(
            test_field.id,
            new_is_required,
            test_field.is_visible,
            test_field.maker_can_edit,
            test_field.checker_can_edit,
            test_field.author_can_edit
        )
        
        print(f"Update result: {result}")
        
        # Verify the change by re-fetching from the database
        updated_field = FieldConfig.query.get(test_field.id)
        print(f"Updated values: required={updated_field.is_required}, visible={updated_field.is_visible}")
        
        # Check if the update was successful
        if updated_field.is_required == new_is_required:
            print("✅ Test passed: Field configuration updated successfully!")
        else:
            print("❌ Test failed: Field configuration not updated.")
            
        # Reset to original value
        print("Resetting to original value...")
        FieldService.update_field_config(
            test_field.id,
            test_field.is_required,
            test_field.is_visible,
            test_field.maker_can_edit,
            test_field.checker_can_edit,
            test_field.author_can_edit
        )
        
        # Verify reset
        reset_field = FieldConfig.query.get(test_field.id)
        print(f"Reset values: required={reset_field.is_required}, visible={reset_field.is_visible}")

if __name__ == "__main__":
    test_field_config_update()
