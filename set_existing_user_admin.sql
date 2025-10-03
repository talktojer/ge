-- SQL script to set admin privileges for existing CyberNut user
-- Run this against your PostgreSQL database

DO $$
DECLARE
    cybernut_user_id INTEGER;
    admin_role_id INTEGER;
    user_account_id INTEGER;
BEGIN
    -- Find the existing CyberNut user
    SELECT id INTO cybernut_user_id FROM users WHERE userid = 'CyberNut';
    
    IF cybernut_user_id IS NULL THEN
        RAISE EXCEPTION 'CyberNut user not found! Please create the user first.';
    END IF;
    
    RAISE NOTICE 'Found CyberNut user with ID: %', cybernut_user_id;
    
    -- Create or update UserAccount record with admin privileges
    SELECT id INTO user_account_id FROM user_accounts WHERE user_id = cybernut_user_id;
    
    IF user_account_id IS NULL THEN
        -- Create UserAccount with admin privileges
        INSERT INTO user_accounts (
            user_id,
            is_admin,
            is_sysop,
            preferred_ship_class,
            auto_repair,
            auto_shield,
            created_at,
            updated_at
        ) VALUES (
            cybernut_user_id,
            true,
            true,
            1,
            false,
            false,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );
        RAISE NOTICE 'Created UserAccount for CyberNut with admin privileges';
    ELSE
        -- Update existing UserAccount to have admin privileges
        UPDATE user_accounts 
        SET is_admin = true, is_sysop = true, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = cybernut_user_id;
        RAISE NOTICE 'Updated UserAccount for CyberNut with admin privileges';
    END IF;
    
    -- Ensure admin role exists
    SELECT id INTO admin_role_id FROM roles WHERE name = 'admin' AND is_active = true;
    
    IF admin_role_id IS NULL THEN
        -- Create admin role
        INSERT INTO roles (name, description, is_active, created_at)
        VALUES ('admin', 'System administrator', true, CURRENT_TIMESTAMP)
        RETURNING id INTO admin_role_id;
        RAISE NOTICE 'Created admin role with ID: %', admin_role_id;
    END IF;
    
    -- Assign admin role to CyberNut (if not already assigned)
    IF NOT EXISTS (
        SELECT 1 FROM user_roles 
        WHERE user_id = cybernut_user_id AND role_id = admin_role_id
    ) THEN
        INSERT INTO user_roles (user_id, role_id)
        VALUES (cybernut_user_id, admin_role_id);
        RAISE NOTICE 'Assigned admin role to CyberNut';
    ELSE
        RAISE NOTICE 'CyberNut already has admin role';
    END IF;
    
    -- Show final status
    RAISE NOTICE '=== ADMIN SETUP COMPLETE ===';
    RAISE NOTICE 'CyberNut User ID: %', cybernut_user_id;
    RAISE NOTICE 'Admin privileges have been set successfully!';
    
END $$;

-- Verify the admin setup
SELECT 
    u.id,
    u.userid,
    u.email,
    u.is_active,
    u.is_verified,
    ua.is_admin,
    ua.is_sysop,
    array_agg(r.name) as roles
FROM users u
LEFT JOIN user_accounts ua ON u.id = ua.user_id
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
WHERE u.userid = 'CyberNut'
GROUP BY u.id, u.userid, u.email, u.is_active, u.is_verified, ua.is_admin, ua.is_sysop;
