"""
Workflow service for OPTiMuS.
This module provides services for managing workflow configurations and processes.
"""
from datetime import datetime

# Import SystemConfig dynamically to avoid circular imports
_SystemConfig = None

def _get_system_config():
    """Get the SystemConfig model, importing it if necessary."""
    global _SystemConfig
    if _SystemConfig is None:
        from models.config import SystemConfig
        _SystemConfig = SystemConfig
    return _SystemConfig

class WorkflowService:
    """
    Service for managing workflow configurations and processes.
    """

    @staticmethod
    def get_workflow_mode():
        """
        Get the current workflow mode.

        Returns:
            str: 'auto' or 'manual'
        """
        try:
            SystemConfig = _get_system_config()
            if SystemConfig is None:
                return 'manual'  # Default to manual mode if model not available

            config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
            if not config:
                return 'manual'  # Default to manual mode

            return config.value
        except Exception as e:
            print(f"Error getting workflow mode: {str(e)}")
            return 'manual'  # Default to manual mode on error

    @staticmethod
    def set_workflow_mode(mode):
        """
        Set the workflow mode.

        Args:
            mode (str): 'auto' or 'manual'

        Returns:
            bool: True if successful, False otherwise
        """
        if mode not in ['auto', 'manual']:
            return False

        try:
            SystemConfig = _get_system_config()
            if SystemConfig is None:
                print("Cannot set workflow mode: SystemConfig model not available")
                return False

            config = SystemConfig.query.filter_by(key='WORKFLOW_MODE').first()
            if not config:
                config = SystemConfig(key='WORKFLOW_MODE', value=mode)
                from app import db
                db.session.add(config)
            else:
                config.value = mode
        except Exception as e:
            print(f"Error setting workflow mode: {str(e)}")
            return False

        try:
            from app import db
            db.session.commit()
            return True
        except Exception:
            from app import db
            db.session.rollback()
            return False

    @staticmethod
    def is_auto_mode():
        """
        Check if the workflow is in auto mode.

        Returns:
            bool: True if in auto mode, False if in manual mode
        """
        return WorkflowService.get_workflow_mode() == 'auto'

    @staticmethod
    def get_next_status(current_status, user_role, is_approved=True, is_rejected=False):
        """
        Get the next status based on the current status, user role, and action.

        Args:
            current_status (str): The current status
            user_role (str): The user role ('maker', 'checker', 'author')
            is_approved (bool): Whether the application is being approved
            is_rejected (bool): Whether the application is being rejected

        Returns:
            str: The next status
        """
        from app import LoanApplication, ROLE_MAKER, ROLE_CHECKER, ROLE_AUTHOR

        # If rejected, return rejected status
        if is_rejected:
            return LoanApplication.STATUS_REJECTED

        # If not approved, keep the current status
        if not is_approved:
            return current_status

        # Handle status transitions based on role and current status
        if user_role == ROLE_MAKER:
            return LoanApplication.STATUS_PENDING_CHECKER

        elif user_role == ROLE_CHECKER:
            # In auto mode, checker approval goes straight to approved
            if WorkflowService.is_auto_mode():
                return LoanApplication.STATUS_APPROVED
            else:
                return LoanApplication.STATUS_PENDING_AUTHOR

        elif user_role == ROLE_AUTHOR:
            return LoanApplication.STATUS_APPROVED

        # Default: keep current status
        return current_status

    @staticmethod
    def update_application_status(application, new_status, rejected_by=None, rejection_reason=None):
        """
        Update an application's status.

        Args:
            application: The loan application object
            new_status (str): The new status
            rejected_by: The user who rejected the application (if applicable)
            rejection_reason (str): The reason for rejection (if applicable)

        Returns:
            bool: True if successful, False otherwise
        """
        from app import LoanApplication

        application.status = new_status
        application.status_changed_at = datetime.utcnow()

        # If rejected, update rejection information
        if new_status == LoanApplication.STATUS_REJECTED and rejected_by:
            application.rejected_by = rejected_by.username
            application.rejected_by_id = rejected_by.id
            application.rejection_reason = rejection_reason

        try:
            from app import db
            db.session.commit()
            return True
        except Exception:
            from app import db
            db.session.rollback()
            return False
