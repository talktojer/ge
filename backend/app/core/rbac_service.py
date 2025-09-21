"""
Role-Based Access Control (RBAC) Service

This service provides role and permission management functionality
for the Galactic Empire game security system.
"""

import json
from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.user import User
from ..models.role import Role, Permission, UserPermission, APIKey


class RBACService:
    """Service for role-based access control operations"""
    
    def __init__(self):
        self.permission_cache = {}
    
    # Role Management
    def create_role(self, db: Session, name: str, description: str = None, parent_role_id: int = None) -> Role:
        """Create a new role"""
        role = Role(
            name=name,
            description=description,
            parent_role_id=parent_role_id
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    
    def get_role(self, db: Session, role_id: int) -> Optional[Role]:
        """Get role by ID"""
        return db.query(Role).filter(Role.id == role_id, Role.is_active == True).first()
    
    def get_role_by_name(self, db: Session, name: str) -> Optional[Role]:
        """Get role by name"""
        return db.query(Role).filter(Role.name == name, Role.is_active == True).first()
    
    def list_roles(self, db: Session) -> List[Role]:
        """List all active roles"""
        return db.query(Role).filter(Role.is_active == True).all()
    
    def update_role(self, db: Session, role_id: int, **updates) -> Optional[Role]:
        """Update role properties"""
        role = self.get_role(db, role_id)
        if not role:
            return None
        
        for key, value in updates.items():
            if hasattr(role, key):
                setattr(role, key, value)
        
        db.commit()
        db.refresh(role)
        return role
    
    def delete_role(self, db: Session, role_id: int) -> bool:
        """Soft delete a role"""
        role = self.get_role(db, role_id)
        if not role:
            return False
        
        role.is_active = False
        db.commit()
        return True
    
    # Permission Management
    def create_permission(self, db: Session, name: str, resource: str, action: str, description: str = None) -> Permission:
        """Create a new permission"""
        permission = Permission(
            name=name,
            resource=resource,
            action=action,
            description=description
        )
        db.add(permission)
        db.commit()
        db.refresh(permission)
        return permission
    
    def get_permission(self, db: Session, permission_id: int) -> Optional[Permission]:
        """Get permission by ID"""
        return db.query(Permission).filter(Permission.id == permission_id, Permission.is_active == True).first()
    
    def get_permission_by_name(self, db: Session, name: str) -> Optional[Permission]:
        """Get permission by name"""
        return db.query(Permission).filter(Permission.name == name, Permission.is_active == True).first()
    
    def list_permissions(self, db: Session) -> List[Permission]:
        """List all active permissions"""
        return db.query(Permission).filter(Permission.is_active == True).all()
    
    def list_permissions_by_resource(self, db: Session, resource: str) -> List[Permission]:
        """List permissions for a specific resource"""
        return db.query(Permission).filter(
            Permission.resource == resource,
            Permission.is_active == True
        ).all()
    
    # Role-Permission Assignment
    def assign_permission_to_role(self, db: Session, role_id: int, permission_id: int) -> bool:
        """Assign a permission to a role"""
        role = self.get_role(db, role_id)
        permission = self.get_permission(db, permission_id)
        
        if not role or not permission:
            return False
        
        if permission not in role.permissions:
            role.permissions.append(permission)
            db.commit()
        
        return True
    
    def remove_permission_from_role(self, db: Session, role_id: int, permission_id: int) -> bool:
        """Remove a permission from a role"""
        role = self.get_role(db, role_id)
        permission = self.get_permission(db, permission_id)
        
        if not role or not permission:
            return False
        
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.commit()
        
        return True
    
    def get_role_permissions(self, db: Session, role_id: int) -> List[Permission]:
        """Get all permissions for a role (including inherited)"""
        role = self.get_role(db, role_id)
        if not role:
            return []
        
        permissions = set(role.permissions)
        
        # Add permissions from parent roles
        current_role = role
        while current_role.parent_role:
            current_role = current_role.parent_role
            permissions.update(current_role.permissions)
        
        return list(permissions)
    
    # User-Role Assignment
    def assign_role_to_user(self, db: Session, user_id: int, role_id: int) -> bool:
        """Assign a role to a user"""
        user = db.query(User).filter(User.id == user_id).first()
        role = self.get_role(db, role_id)
        
        if not user or not role:
            return False
        
        if role not in user.roles:
            user.roles.append(role)
            db.commit()
        
        return True
    
    def remove_role_from_user(self, db: Session, user_id: int, role_id: int) -> bool:
        """Remove a role from a user"""
        user = db.query(User).filter(User.id == user_id).first()
        role = self.get_role(db, role_id)
        
        if not user or not role:
            return False
        
        if role in user.roles:
            user.roles.remove(role)
            db.commit()
        
        return True
    
    def get_user_roles(self, db: Session, user_id: int) -> List[Role]:
        """Get all roles assigned to a user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        return user.roles
    
    # User Permission Overrides
    def grant_user_permission(self, db: Session, user_id: int, permission_id: int, expires_at: datetime = None) -> bool:
        """Grant a direct permission to a user"""
        # Check if override already exists
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id
        ).first()
        
        if existing:
            existing.granted = True
            existing.expires_at = expires_at
        else:
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
                granted=True,
                expires_at=expires_at
            )
            db.add(user_permission)
        
        db.commit()
        return True
    
    def deny_user_permission(self, db: Session, user_id: int, permission_id: int, expires_at: datetime = None) -> bool:
        """Deny a direct permission to a user (overrides role permissions)"""
        # Check if override already exists
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id
        ).first()
        
        if existing:
            existing.granted = False
            existing.expires_at = expires_at
        else:
            user_permission = UserPermission(
                user_id=user_id,
                permission_id=permission_id,
                granted=False,
                expires_at=expires_at
            )
            db.add(user_permission)
        
        db.commit()
        return True
    
    def remove_user_permission_override(self, db: Session, user_id: int, permission_id: int) -> bool:
        """Remove a direct permission override for a user"""
        user_permission = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission_id
        ).first()
        
        if user_permission:
            db.delete(user_permission)
            db.commit()
            return True
        
        return False
    
    # Permission Checking
    def user_has_permission(self, db: Session, user_id: int, resource: str, action: str) -> bool:
        """Check if user has permission for a resource/action"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        permission = db.query(Permission).filter(
            Permission.resource == resource,
            Permission.action == action,
            Permission.is_active == True
        ).first()
        
        if not permission:
            return False
        
        # Check direct user permission overrides first
        user_permission = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_id == permission.id,
            or_(UserPermission.expires_at == None, UserPermission.expires_at > datetime.utcnow())
        ).first()
        
        if user_permission:
            return user_permission.granted
        
        # Check role permissions
        for role in user.roles:
            if permission in self.get_role_permissions(db, role.id):
                return True
        
        return False
    
    def get_user_permissions(self, db: Session, user_id: int) -> Set[str]:
        """Get all permission names that a user has"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return set()
        
        permissions = set()
        
        # Get permissions from roles
        for role in user.roles:
            role_permissions = self.get_role_permissions(db, role.id)
            for perm in role_permissions:
                permissions.add(f"{perm.resource}:{perm.action}")
        
        # Apply user permission overrides
        user_overrides = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            or_(UserPermission.expires_at == None, UserPermission.expires_at > datetime.utcnow())
        ).all()
        
        for override in user_overrides:
            perm_name = f"{override.permission.resource}:{override.permission.action}"
            if override.granted:
                permissions.add(perm_name)
            else:
                permissions.discard(perm_name)
        
        return permissions
    
    # Default Roles and Permissions Setup
    def initialize_default_roles_and_permissions(self, db: Session):
        """Initialize default roles and permissions for the game"""
        
        # Create default permissions
        default_permissions = [
            # User permissions
            ("user:read", "user", "read", "View user information"),
            ("user:write", "user", "write", "Modify user information"),
            ("user:delete", "user", "delete", "Delete user accounts"),
            ("user:admin", "user", "admin", "Administer user accounts"),
            
            # Ship permissions
            ("ship:read", "ship", "read", "View ship information"),
            ("ship:write", "ship", "write", "Modify ships"),
            ("ship:delete", "ship", "delete", "Delete ships"),
            ("ship:admin", "ship", "admin", "Administer ship system"),
            
            # Planet permissions
            ("planet:read", "planet", "read", "View planet information"),
            ("planet:write", "planet", "write", "Modify planets"),
            ("planet:delete", "planet", "delete", "Delete planets"),
            ("planet:admin", "planet", "admin", "Administer planet system"),
            
            # Team permissions
            ("team:read", "team", "read", "View team information"),
            ("team:write", "team", "write", "Modify teams"),
            ("team:delete", "team", "delete", "Delete teams"),
            ("team:admin", "team", "admin", "Administer team system"),
            
            # Communication permissions
            ("communication:read", "communication", "read", "Read messages"),
            ("communication:write", "communication", "write", "Send messages"),
            ("communication:admin", "communication", "admin", "Administer communication system"),
            
            # Game permissions
            ("game:read", "game", "read", "View game state"),
            ("game:write", "game", "write", "Modify game state"),
            ("game:admin", "game", "admin", "Administer game system"),
            
            # System permissions
            ("system:read", "system", "read", "View system information"),
            ("system:write", "system", "write", "Modify system settings"),
            ("system:admin", "system", "admin", "Full system administration"),
        ]
        
        permissions_map = {}
        for name, resource, action, description in default_permissions:
            existing = self.get_permission_by_name(db, name)
            if not existing:
                perm = self.create_permission(db, name, resource, action, description)
                permissions_map[name] = perm
            else:
                permissions_map[name] = existing
        
        # Create default roles
        default_roles = [
            ("player", "Basic player role", None, ["user:read", "ship:read", "ship:write", "planet:read", "planet:write", "team:read", "communication:read", "communication:write", "game:read"]),
            ("team_leader", "Team leader role", None, ["team:write"]),
            ("moderator", "Game moderator", None, ["user:admin", "communication:admin", "team:admin"]),
            ("admin", "System administrator", None, ["system:admin", "game:admin", "user:admin", "ship:admin", "planet:admin", "team:admin", "communication:admin"]),
            ("sysop", "System operator", None, ["system:admin"]),
        ]
        
        for role_name, description, parent_name, permission_names in default_roles:
            existing = self.get_role_by_name(db, role_name)
            if not existing:
                parent_id = None
                if parent_name:
                    parent_role = self.get_role_by_name(db, parent_name)
                    if parent_role:
                        parent_id = parent_role.id
                
                role = self.create_role(db, role_name, description, parent_id)
                
                # Assign permissions to role
                for perm_name in permission_names:
                    if perm_name in permissions_map:
                        self.assign_permission_to_role(db, role.id, permissions_map[perm_name].id)


# Global RBAC service instance
rbac_service = RBACService()
