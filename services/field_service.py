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
        Get configuration for a specific field.

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
        try:
            FieldConfig = _get_field_config()
            if FieldConfig is None:
                print("Cannot update field config: FieldConfig model not available")
                return False

            field_config = FieldConfig.query.get(field_id)
            if not field_config:
                return False
        except Exception as e:
            print(f"Error getting field config for update: {str(e)}")
            return False

        field_config.is_required = is_required
        field_config.is_visible = is_visible
        field_config.maker_can_edit = maker_can_edit
        field_config.checker_can_edit = checker_can_edit
        field_config.author_can_edit = author_can_edit

        try:
            from app import db
            db.session.commit()
            return True
        except Exception:
            from app import db
            db.session.rollback()
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
