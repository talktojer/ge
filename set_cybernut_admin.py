#!/usr/bin/env python3
"""
Script to create CyberNut user and set admin privileges
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.app.core.database import get_db, engine
from backend.app.models.user import User, UserAccount
from backend.app.models.role import Role
from backend.app.core.rbac_service import RBACService
from backend.app.core.auth import AuthService

def create_cybernut_admin():
    """Create CyberNut user and set admin privileges"""
    
    # Create database session
    db = next(get_db())
    
    try:
        # Initialize services
        rbac_service = RBACService()
        auth_service = AuthService()
        
        # Check if CyberNut user already exists
        existing_user = db.query(User).filter(User.userid == "CyberNut").first()
        
        if existing_user:
            print(f"User CyberNut already exists (ID: {existing_user.id})")
            user = existing_user
        else:
            print("Creating CyberNut user...")
            
            # Create the user
            user = auth_service.create_user(
                db=db,
                userid="CyberNut",
                email="cybernut@galacticempire.local",
                password="admin123",  # You should change this password
                is_verified=True
            )
            print(f"Created user CyberNut (ID: {user.id})")
        
        # Initialize default roles and permissions if not already done
        print("Initializing default roles and permissions...")
        rbac_service.initialize_default_roles_and_permissions(db)
        
        # Get the admin role
        admin_role = rbac_service.get_role_by_name(db, "admin")
        if not admin_role:
            print("ERROR: Admin role not found!")
            return False
        
        # Assign admin role to CyberNut
        print("Assigning admin role to CyberNut...")
        success = rbac_service.assign_role_to_user(db, user.id, admin_role.id)
        if success:
            print("✓ Admin role assigned successfully")
        else:
            print("✗ Failed to assign admin role")
        
        # Also set UserAccount admin flags for compatibility
        user_account = db.query(UserAccount).filter(UserAccount.user_id == user.id).first()
        if not user_account:
            print("Creating UserAccount record...")
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
        print(f"User permissions: {sorted(list(permissions))}")
        
        print(f"\n✓ CyberNut is now set up as an admin!")
        print(f"Login credentials:")
        print(f"  Username: CyberNut")
        print(f"  Email: cybernut@galacticempire.local")
        print(f"  Password: admin123")
        print(f"\n⚠️  IMPORTANT: Change the default password after first login!")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Setting up CyberNut as admin user...")
    success = create_cybernut_admin()
    sys.exit(0 if success else 1)



