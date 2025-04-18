"""
Fix script for field configuration issues.
This script ensures that field configurations are properly saved to the database.
"""
from app import app, db
from models.config import FieldConfig
from services.field_service import FieldService

def fix_field_configs():
    """
    Fix field configuration issues by ensuring database session is properly managed.
    """
    with app.app_context():
        # Get all field configurations
        field_configs = FieldService.get_all_field_configs()
        
        if not field_configs:
            print("No field configurations found.")
            return
        
        print(f"Found {len(field_configs)} field configurations.")
        
        # Check each field configuration
        for field_config in field_configs:
            print(f"Checking field: {field_config.field_name} (ID: {field_config.id})")
            print(f"Current values: required={field_config.is_required}, visible={field_config.is_visible}, "
                  f"maker_edit={field_config.maker_can_edit}, checker_edit={field_config.checker_can_edit}, "
                  f"author_edit={field_config.author_can_edit}")
            
            # Re-save the field configuration to ensure it's properly stored
            result = FieldService.update_field_config(
                field_config.id,
                field_config.is_required,
                field_config.is_visible,
                field_config.maker_can_edit,
                field_config.checker_can_edit,
                field_config.author_can_edit
            )
            
            if result:
                print(f"✅ Field {field_config.field_name} verified and saved.")
            else:
                print(f"❌ Failed to verify field {field_config.field_name}.")
        
        print("\nField configuration verification complete.")

def reset_field_configs():
    """
    Reset all field configurations to default values.
    """
    with app.app_context():
        result = FieldService.reset_field_configs()
        if result:
            print("✅ Field configurations reset to default values.")
        else:
            print("❌ Failed to reset field configurations.")

if __name__ == "__main__":
    print("Field Configuration Fix Utility")
    print("==============================")
    print("1. Verify and fix existing field configurations")
    print("2. Reset all field configurations to default values")
    print("3. Exit")
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        fix_field_configs()
    elif choice == "2":
        confirm = input("Are you sure you want to reset all field configurations? (y/n): ")
        if confirm.lower() == "y":
            reset_field_configs()
        else:
            print("Reset cancelled.")
    else:
        print("Exiting.")
