"""
Field configuration service for OPTiMuS.
This module provides services for managing field configurations.
"""
from flask_login import current_user

# Import models dynamically to avoid circular imports
_FieldConfig = None

def _get_field_config():
    """Get the FieldConfig model, importing it if necessary."""
    global _FieldConfig
    if _FieldConfig is None:
        from models.config import FieldConfig
        _FieldConfig = FieldConfig
    return _FieldConfig

class FieldService:
    """
    Service for managing field configurations.
    """

    @staticmethod
    def get_field_config(field_name):
        """
        Get configuration for a specific field by name.

        Args:
            field_name (str): The name of the field

        Returns:
            FieldConfig: The field configuration
        """
        try:
            FieldConfig = _get_field_config()
            if FieldConfig is None:
                return None  # Return None if model not available

            return FieldConfig.query.filter_by(field_name=field_name).first()
        except Exception as e:
            print(f"Error getting field config for {field_name}: {str(e)}")
            return None

    @staticmethod
    def get_field_config_by_id(field_id):
        """
        Get configuration for a specific field by ID.

        Args:
            field_id (int): The ID of the field configuration

        Returns:
            FieldConfig: The field configuration
        """
        try:
            FieldConfig = _get_field_config()
            if FieldConfig is None:
                return None  # Return None if model not available

            return FieldConfig.query.get(field_id)
        except Exception as e:
            print(f"Error getting field config for ID {field_id}: {str(e)}")
            return None

    @staticmethod
    def get_all_field_configs():
        """
        Get all field configurations.

        Returns:
            list: List of FieldConfig objects
        """
        try:
            FieldConfig = _get_field_config()
            if FieldConfig is None:
                return []  # Return empty list if model not available

            return FieldConfig.query.order_by(FieldConfig.order).all()
        except Exception as e:
            print(f"Error getting all field configs: {str(e)}")
            return []

    @staticmethod
    def update_field_config(field_id, is_required, is_visible, maker_can_edit, checker_can_edit, author_can_edit):
        """
        Update a field configuration.

        Args:
            field_id (int): The ID of the field configuration
            is_required (bool): Whether the field is required
            is_visible (bool): Whether the field is visible
            maker_can_edit (bool): Whether makers can edit the field
            checker_can_edit (bool): Whether checkers can edit the field
            author_can_edit (bool): Whether authors can edit the field

        Returns:
            bool: True if successful, False otherwise
        """
        # Import db at the beginning to ensure we're using the same session
        from app import db

        try:
            FieldConfig = _get_field_config()
            if FieldConfig is None:
                print("Cannot update field config: FieldConfig model not available")
                return False

            field_config = FieldConfig.query.get(field_id)
            if not field_config:
                print(f"Field config with ID {field_id} not found")
                return False

            # Debug: Print current values before update
            print(f"Updating field config for {field_config.field_name} (ID: {field_id})")
            print(f"Current values: required={field_config.is_required}, visible={field_config.is_visible}, ")
            print(f"maker_edit={field_config.maker_can_edit}, checker_edit={field_config.checker_can_edit}, author_edit={field_config.author_can_edit}")
            print(f"New values: required={is_required}, visible={is_visible}, ")
            print(f"maker_edit={maker_can_edit}, checker_edit={checker_can_edit}, author_edit={author_can_edit}")

            # Validate configuration
            # A required field must be visible
            if is_required and not is_visible:
                is_visible = True
                print(f"Field {field_config.field_name} is required, forcing visibility to True")

            # Special handling for essential fields
            # Date and Application ID must always be required
            if field_config.field_name in ['date', 'application_id']:
                if not is_required or not is_visible:
                    is_required = True
                    is_visible = True
                    print(f"Field {field_config.field_name} is essential, forcing required and visible to True")

            # Special handling for workflow fields
            if field_config.field_name == 'maker':
                # Maker field must be visible and required
                if not is_visible or not is_required:
                    is_visible = True
                    is_required = True
                    print(f"Field {field_config.field_name} is essential for workflow, forcing required and visible to True")

            # Ensure at least one role can edit a visible field
            if is_visible and not (maker_can_edit or checker_can_edit or author_can_edit):
                # Default to maker can edit if no role is selected
                maker_can_edit = True
                print(f"Field {field_config.field_name} is visible but no role can edit, defaulting maker_can_edit to True")

            # Apply the validated configuration
            field_config.is_required = is_required
            field_config.is_visible = is_visible
            field_config.maker_can_edit = maker_can_edit
            field_config.checker_can_edit = checker_can_edit
            field_config.author_can_edit = author_can_edit

            # Commit the changes with explicit transaction management
            try:
                db.session.commit()
                print(f"Field config for {field_config.field_name} updated successfully")

                # Force a flush to ensure changes are written to the database
                db.session.flush()

                # Verify the update was successful by re-fetching from the database with a new query
                # This ensures we're not using cached data
                db.session.expire_all()  # Clear session cache
                verified_config = FieldConfig.query.filter_by(id=field_id).first()

                if verified_config:
                    print(f"Verified values after update: required={verified_config.is_required}, visible={verified_config.is_visible}, ")
                    print(f"maker_edit={verified_config.maker_can_edit}, checker_edit={verified_config.checker_can_edit}, author_edit={verified_config.author_can_edit}")

                    # Double-check that essential fields are always required
                    if verified_config.field_name in ['date', 'application_id'] and not verified_config.is_required:
                        print(f"Warning: Essential field {verified_config.field_name} is not required after update. Fixing...")
                        verified_config.is_required = True
                        verified_config.is_visible = True
                        db.session.commit()
                        print(f"Fixed essential field {verified_config.field_name} to be required")
                else:
                    print("Warning: Could not verify the update - field config not found after commit")
            except Exception as commit_error:
                print(f"Error during commit: {str(commit_error)}")
                db.session.rollback()
                return False

            return True

        except Exception as e:
            print(f"Error updating field config: {str(e)}")
            try:
                db.session.rollback()
            except Exception as rollback_error:
                print(f"Error during rollback: {str(rollback_error)}")
            return False

    @staticmethod
    def can_user_edit_field(field_name):
        """
        Check if the current user can edit a field.

        Args:
            field_name (str): The name of the field

        Returns:
            bool: True if the user can edit the field, False otherwise
        """
        if not current_user.is_authenticated:
            return False

        field_config = FieldService.get_field_config(field_name)
        if not field_config:
            return True  # Default to allowing edit if no config exists

        if current_user.is_maker():
            return field_config.maker_can_edit
        elif current_user.is_checker():
            return field_config.checker_can_edit
        elif current_user.is_author():
            return field_config.author_can_edit

        return False

    @staticmethod
    def is_field_required(field_name):
        """
        Check if a field is required.

        Args:
            field_name (str): The name of the field

        Returns:
            bool: True if the field is required, False otherwise
        """
        field_config = FieldService.get_field_config(field_name)
        if not field_config:
            return True  # Default to required if no config exists

        return field_config.is_required

    @staticmethod
    def is_field_visible(field_name):
        """
        Check if a field is visible.

        Args:
            field_name (str): The name of the field

        Returns:
            bool: True if the field is visible, False otherwise
        """
        field_config = FieldService.get_field_config(field_name)
        if not field_config:
            return True  # Default to visible if no config exists

        return field_config.is_visible

    @staticmethod
    def get_field_attributes(field_name):
        """
        Get attributes for a field based on configuration and current user role.

        Args:
            field_name (str): The name of the field

        Returns:
            dict: Dictionary of field attributes
        """
        field_config = FieldService.get_field_config(field_name)
        if not field_config:
            return {
                'is_required': True,
                'is_visible': True,
                'can_edit': True,
                'display_name': field_name.replace('_', ' ').title()
            }

        can_edit = False
        if current_user.is_authenticated:
            if current_user.is_maker():
                can_edit = field_config.maker_can_edit
            elif current_user.is_checker():
                can_edit = field_config.checker_can_edit
            elif current_user.is_author():
                can_edit = field_config.author_can_edit

        return {
            'is_required': field_config.is_required,
            'is_visible': field_config.is_visible,
            'can_edit': can_edit,
            'display_name': field_config.display_name
        }

    @staticmethod
    def reset_field_configs():
        """
        Reset all field configurations to default values.

        Returns:
            bool: True if successful, False otherwise
        """
        # Import db at the beginning to ensure we're using the same session
        from app import db
        from models.config import get_default_field_configs

        try:
            FieldConfig = _get_field_config()
            if FieldConfig is None:
                print("Cannot reset field configs: FieldConfig model not available")
                return False

            # Get current configurations for logging
            current_configs = FieldConfig.query.all()
            print(f"Current field configurations: {len(current_configs)} found")
            for config in current_configs:
                print(f"  - {config.field_name}: required={config.is_required}, visible={config.is_visible}")

            # Delete all existing field configurations
            print("Deleting existing field configurations...")
            db.session.query(FieldConfig).delete()
            db.session.commit()
            print("Existing configurations deleted successfully")

            # Initialize default field configurations
            print("Creating default field configurations...")
            default_configs = get_default_field_configs()
            for config in default_configs:
                print(f"  - Adding {config.field_name}: required={config.is_required}, visible={config.is_visible}")
                db.session.add(config)

            # Commit the changes
            db.session.commit()
            print("Default configurations added successfully")

            # Verify the reset was successful
            count = db.session.query(FieldConfig).count()
            print(f"Field configurations reset to default values. {count} configurations created.")

            # Verify each configuration was created correctly
            # Query again to avoid session issues
            try:
                new_configs = FieldConfig.query.all()
                for config in new_configs:
                    print(f"  - Verified {config.field_name}: required={config.is_required}, visible={config.is_visible}")
            except Exception as verify_error:
                print(f"Warning: Could not verify configurations after reset: {str(verify_error)}")

            return True
        except Exception as e:
            print(f"Error resetting field configs: {str(e)}")
            try:
                db.session.rollback()
                print("Database session rolled back successfully")
            except Exception as rollback_error:
                print(f"Error during rollback: {str(rollback_error)}")
            return False
