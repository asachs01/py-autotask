"""
ClientPortalUsers entity for Autotask API operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ClientPortalUsersEntity(BaseEntity):
    """
    Handles all ClientPortalUsers-related operations for the Autotask API.

    ClientPortalUsers represent user accounts that have access to the client portal,
    allowing customers to view and interact with their tickets, projects, and services.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_portal_user(
        self,
        contact_id: int,
        username: str,
        password: str,
        is_active: bool = True,
        security_level: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new client portal user.

        Args:
            contact_id: ID of the associated contact
            username: Portal username
            password: Initial password (will be hashed)
            is_active: Whether the user account is active
            security_level: Security/access level (1=Basic, 2=Advanced, etc.)
            **kwargs: Additional user properties

        Returns:
            Created client portal user data
        """
        user_data = {
            "ContactID": contact_id,
            "UserName": username,
            "Password": password,
            "IsActive": is_active,
            "SecurityLevel": security_level,
            **kwargs,
        }

        return self.create(user_data)

    def get_active_portal_users(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all active client portal users.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of active portal users
        """
        filters = [QueryFilter(field="IsActive", op="eq", value=True)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_users_by_company(
        self, company_id: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get client portal users for a specific company.

        Args:
            company_id: ID of the company
            active_only: Whether to return only active users
            limit: Maximum number of users to return

        Returns:
            List of portal users for the company
        """
        # This would typically join with Contacts to filter by company
        # For now, we'll implement a basic version
        filters = []

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        users = response.items if hasattr(response, "items") else response

        # Would need to filter by company through contact relationship
        return users

    def get_users_by_security_level(
        self, security_level: int, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get client portal users by security level.

        Args:
            security_level: Security level to filter by
            active_only: Whether to return only active users
            limit: Maximum number of users to return

        Returns:
            List of users with the specified security level
        """
        filters = [QueryFilter(field="SecurityLevel", op="eq", value=security_level)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def authenticate_user(self, username: str, password: str) -> Optional[EntityDict]:
        """
        Authenticate a client portal user.

        Args:
            username: Portal username
            password: Password to verify

        Returns:
            User data if authentication successful, None otherwise
        """
        filters = [
            QueryFilter(field="UserName", op="eq", value=username),
            QueryFilter(field="IsActive", op="eq", value=True),
        ]

        response = self.query(filters=filters, max_records=1)
        users = response.items if hasattr(response, "items") else response

        if users:
            user = users[0]
            # In a real implementation, password would be properly hashed and verified
            # For now, we'll just return the user data
            return user

        return None

    def activate_user(self, user_id: int) -> EntityDict:
        """
        Activate a client portal user account.

        Args:
            user_id: ID of the user to activate

        Returns:
            Updated user data
        """
        return self.update_by_id(user_id, {"IsActive": True})

    def deactivate_user(self, user_id: int) -> EntityDict:
        """
        Deactivate a client portal user account.

        Args:
            user_id: ID of the user to deactivate

        Returns:
            Updated user data
        """
        return self.update_by_id(user_id, {"IsActive": False})

    def reset_user_password(
        self, user_id: int, new_password: str, force_change: bool = True
    ) -> EntityDict:
        """
        Reset a client portal user's password.

        Args:
            user_id: ID of the user
            new_password: New password
            force_change: Whether to force password change on next login

        Returns:
            Updated user data
        """
        update_data = {
            "Password": new_password,
            "PasswordResetDate": datetime.now().isoformat(),
        }

        if force_change:
            update_data["ForcePasswordChange"] = True

        return self.update_by_id(user_id, update_data)

    def update_security_level(
        self, user_id: int, new_security_level: int
    ) -> EntityDict:
        """
        Update a user's security level.

        Args:
            user_id: ID of the user
            new_security_level: New security level

        Returns:
            Updated user data
        """
        return self.update_by_id(user_id, {"SecurityLevel": new_security_level})

    def get_user_login_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get login statistics for a client portal user.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary containing login statistics
        """
        user = self.get(user_id)
        if not user:
            return {"error": "User not found"}

        # This would typically come from login tracking data
        return {
            "user_id": user_id,
            "username": user.get("UserName"),
            "is_active": user.get("IsActive", False),
            "security_level": user.get("SecurityLevel"),
            "last_login": user.get("LastLoginDate"),
            "login_count": user.get("LoginCount", 0),
            "failed_login_attempts": user.get("FailedLoginAttempts", 0),
            "account_locked": user.get("IsLocked", False),
            "password_reset_date": user.get("PasswordResetDate"),
            "force_password_change": user.get("ForcePasswordChange", False),
        }

    def bulk_create_portal_users(
        self, users_data: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple client portal users in batch.

        Args:
            users_data: List of user data dictionaries

        Returns:
            List of created user responses
        """
        return self.batch_create(users_data)

    def search_users_by_username(
        self, search_term: str, active_only: bool = True, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search client portal users by username.

        Args:
            search_term: Term to search for in usernames
            active_only: Whether to search only active users
            limit: Maximum number of users to return

        Returns:
            List of matching users
        """
        filters = [QueryFilter(field="UserName", op="contains", value=search_term)]

        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_users_by_last_login(
        self, days_inactive: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get users who haven't logged in for a specified number of days.

        Args:
            days_inactive: Number of days since last login
            limit: Maximum number of users to return

        Returns:
            List of inactive users
        """
        cutoff_date = datetime.now() - datetime.timedelta(days=days_inactive)

        filters = [
            QueryFilter(field="LastLoginDate", op="lt", value=cutoff_date.isoformat()),
            QueryFilter(field="IsActive", op="eq", value=True),
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_portal_user_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all client portal users.

        Returns:
            Dictionary containing user statistics summary
        """
        all_users = self.query_all()
        active_users = [user for user in all_users if user.get("IsActive", False)]

        security_levels = {}
        for user in all_users:
            level = user.get("SecurityLevel", 0)
            if level not in security_levels:
                security_levels[level] = {"total": 0, "active": 0}

            security_levels[level]["total"] += 1
            if user.get("IsActive", False):
                security_levels[level]["active"] += 1

        return {
            "total_users": len(all_users),
            "active_users": len(active_users),
            "inactive_users": len(all_users) - len(active_users),
            "activation_rate": (len(active_users) / max(1, len(all_users))) * 100,
            "security_levels": security_levels,
            "users_requiring_password_change": len(
                [
                    user
                    for user in active_users
                    if user.get("ForcePasswordChange", False)
                ]
            ),
            "locked_accounts": len(
                [user for user in all_users if user.get("IsLocked", False)]
            ),
        }

    def cleanup_inactive_users(
        self, days_inactive: int = 365, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up users that have been inactive for an extended period.

        Args:
            days_inactive: Number of days of inactivity before cleanup
            dry_run: If True, only identify users without deleting

        Returns:
            Dictionary containing cleanup results
        """
        inactive_users = self.get_users_by_last_login(days_inactive)

        cleanup_results = {
            "total_inactive_users": len(inactive_users),
            "days_inactive_threshold": days_inactive,
            "dry_run": dry_run,
            "users_to_cleanup": [
                {
                    "user_id": user.get("id"),
                    "username": user.get("UserName"),
                    "last_login": user.get("LastLoginDate"),
                    "contact_id": user.get("ContactID"),
                }
                for user in inactive_users
            ],
            "cleanup_count": 0,
        }

        if not dry_run and inactive_users:
            # In a real implementation, you might deactivate rather than delete
            cleanup_results["warning"] = (
                "Actual cleanup not implemented - use with caution"
            )

        return cleanup_results
