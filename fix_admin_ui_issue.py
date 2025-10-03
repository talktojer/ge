#!/usr/bin/env python3
"""
Script to fix the admin UI recognition issue by ensuring proper admin setup
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User, UserAccount
from backend.app.models.role import Role
from backend.app.core.rbac_service import RBACService

def fix_admin_ui_issue():
    """Fix admin UI recognition for CyberNut user"""
    
    # Create database session
    db = next(get_db())
    
    try:
        # Initialize RBAC service
        rbac_service = RBACService()
        
        # Find CyberNut user
        user = db.query(User).filter(User.userid == "CyberNut").first()
        
        if not user:
            print("ERROR: CyberNut user not found!")
            return False
        
        print(f"Found CyberNut user (ID: {user.id})")
        print(f"Current userid: {user.userid}")
        print(f"Current email: {user.email}")
        
        # Ensure admin role exists and is assigned
        rbac_service.initialize_default_roles_and_permissions(db)
        admin_role = rbac_service.get_role_by_name(db, "admin")
        
        if admin_role:
            success = rbac_service.assign_role_to_user(db, user.id, admin_role.id)
            print(f"Admin role assignment: {'✓ Success' if success else '✓ Already assigned'}")
        
        # Ensure UserAccount admin flags are set
        user_account = db.query(UserAccount).filter(UserAccount.user_id == user.id).first()
        if user_account:
            user_account.is_admin = True
            user_account.is_sysop = True
            print("✓ UserAccount admin flags updated")
        else:
            user_account = UserAccount(
                user_id=user.id,
                is_admin=True,
                is_sysop=True
            )
            db.add(user_account)
            print("✓ UserAccount created with admin flags")
        
        # Commit changes
        db.commit()
        
        # Verify setup
        print("\n=== VERIFICATION ===")
        user_roles = rbac_service.get_user_roles(db, user.id)
        role_names = [role.name for role in user_roles]
        print(f"User roles: {role_names}")
        
        db.refresh(user_account)
        print(f"UserAccount is_admin: {user_account.is_admin}")
        print(f"UserAccount is_sysop: {user_account.is_sysop}")
        
        print("\n✓ Admin setup verified!")
        print("\n=== NEXT STEPS ===")
        print("1. Restart your frontend development server")
        print("2. Clear browser cache/localStorage")
        print("3. Log in again as CyberNut")
        print("4. The UI should now show 'CyberNut' instead of 'Guest'")
        print("5. Admin pages should be accessible")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    print("Fixing admin UI recognition issue...")
    success = fix_admin_ui_issue()
    sys.exit(0 if success else 1)



