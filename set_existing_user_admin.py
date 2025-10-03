#!/usr/bin/env python3
"""
Script to set admin privileges for existing CyberNut user
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.app.core.database import get_db, engine
from backend.app.models.user import User, UserAccount
from backend.app.models.role import Role
from backend.app.core.rbac_service import RBACService

def set_cybernut_admin():
    """Set admin privileges for existing CyberNut user"""
    
    # Create database session
    db = next(get_db())
    
    try:
        # Initialize RBAC service
        rbac_service = RBACService()
        
        # Find the existing CyberNut user
        user = db.query(User).filter(User.userid == "CyberNut").first()
        
        if not user:
            print("ERROR: CyberNut user not found!")
            return False
        
        print(f"Found CyberNut user (ID: {user.id})")
        
        # Initialize default roles and permissions if not already done
        print("Ensuring default roles and permissions exist...")
        rbac_service.initialize_default_roles_and_permissions(db)
        
        # Get the admin role
        admin_role = rbac_service.get_role_by_name(db, "admin")
        if not admin_role:
            print("ERROR: Admin role not found!")
            return False
        
        # Check if user already has admin role
        current_roles = rbac_service.get_user_roles(db, user.id)
        role_names = [role.name for role in current_roles]
        
        if "admin" not in role_names:
            print("Assigning admin role to CyberNut...")
            success = rbac_service.assign_role_to_user(db, user.id, admin_role.id)
            if success:
                print("✓ Admin role assigned successfully")
            else:
                print("✗ Failed to assign admin role")
        else:
            print("✓ CyberNut already has admin role")
        
        # Set UserAccount admin flags for compatibility
        user_account = db.query(UserAccount).filter(UserAccount.user_id == user.id).first()
        if not user_account:
            print("Creating UserAccount record with admin privileges...")
            user_account = UserAccount(
                user_id=user.id,
                is_admin=True,
                is_sysop=True
            )
            db.add(user_account)
        else:
            print("Updating UserAccount admin flags...")
            user_account.is_admin = True
            user_account.is_sysop = True
        
        # Commit all changes
        db.commit()
        
        # Verify the setup
        print("\nVerifying admin privileges...")
        
        # Check RBAC roles
        user_roles = rbac_service.get_user_roles(db, user.id)
        role_names = [role.name for role in user_roles]
        print(f"User roles: {role_names}")
        
        # Check UserAccount flags
        db.refresh(user_account)
        print(f"UserAccount is_admin: {user_account.is_admin}")
        print(f"UserAccount is_sysop: {user_account.is_sysop}")
        
        # Check permissions
        permissions = rbac_service.get_user_permissions(db, user.id)
        print(f"User permissions count: {len(permissions)}")
        print(f"Key admin permissions: {[p for p in permissions if 'admin' in p]}")
        
        print(f"\n✓ CyberNut now has admin privileges!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Setting admin privileges for existing CyberNut user...")
    success = set_cybernut_admin()
    sys.exit(0 if success else 1)



