"""
Verification script to ensure essential fields (date and application_id) are always required.
"""
from app import app, db
from models.config import FieldConfig
from services.field_service import FieldService

def verify_essential_fields():
    """Verify that essential fields are always required."""
    with app.app_context():
        print("=== Verifying Essential Fields ===")
        
        # Get the date and application_id field configurations
        date_config = FieldService.get_field_config('date')
        app_id_config = FieldService.get_field_config('application_id')
        
        if not date_config or not app_id_config:
            print("❌ Essential field configurations not found.")
            return False
        
        print(f"Date field: required={date_config.is_required}, visible={date_config.is_visible}")
        print(f"Application ID field: required={app_id_config.is_required}, visible={app_id_config.is_visible}")
        
        # Try to set them as not required
        print("\nAttempting to set essential fields as not required...")
        
        # Update date field
        result1 = FieldService.update_field_config(
            date_config.id,
            False,  # Try to set as not required
            True,
            date_config.maker_can_edit,
            date_config.checker_can_edit,
            date_config.author_can_edit
        )
        
        # Update application_id field
        result2 = FieldService.update_field_config(
            app_id_config.id,
            False,  # Try to set as not required
            True,
            app_id_config.maker_can_edit,
            app_id_config.checker_can_edit,
            app_id_config.author_can_edit
        )
        
        # Verify the changes
        db.session.expire_all()  # Clear session cache
        
        date_config = FieldService.get_field_config('date')
        app_id_config = FieldService.get_field_config('application_id')
        
        print("\nAfter attempted update:")
        print(f"Date field: required={date_config.is_required}, visible={date_config.is_visible}")
        print(f"Application ID field: required={app_id_config.is_required}, visible={app_id_config.is_visible}")
        
        # Check if the fields are still required
        if date_config.is_required and app_id_config.is_required:
            print("\n✅ Test passed: Essential fields remain required even after attempting to set them as not required!")
            return True
        else:
            print("\n❌ Test failed: Essential fields were set as not required.")
            
            # Fix the fields
            print("\nFixing essential fields...")
            FieldService.update_field_config(
                date_config.id,
                True,
                True,
                date_config.maker_can_edit,
                date_config.checker_can_edit,
                date_config.author_can_edit
            )
            
            FieldService.update_field_config(
                app_id_config.id,
                True,
                True,
                app_id_config.maker_can_edit,
                app_id_config.checker_can_edit,
                app_id_config.author_can_edit
            )
            
            return False

if __name__ == "__main__":
    print("Essential Fields Verification")
    print("============================")
    
    success = verify_essential_fields()
    
    if success:
        print("\nAll tests passed! The essential fields fix is working correctly.")
    else:
        print("\nSome tests failed. The essential fields fix may not be working correctly.")
