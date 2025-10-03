-- SQL script to create CyberNut user and set admin privileges
-- Run this against your PostgreSQL database

-- First, let's check if the user already exists
DO $$
DECLARE
    user_id INTEGER;
    admin_role_id INTEGER;
    user_account_id INTEGER;
BEGIN
    -- Check if CyberNut user exists
    SELECT id INTO user_id FROM users WHERE userid = 'CyberNut';
    
    IF user_id IS NULL THEN
        -- Create CyberNut user
        INSERT INTO users (
            userid, 
            email, 
            password_hash, 
            is_active, 
            is_verified,
            score,
            noships,
            topshipno,
            kills,
            planets,
            cash,
            debt,
            plscore,
            klscore,
            population,
            teamcode,
            scan_names,
            scan_home,
            created_at,
            last_login
        ) VALUES (
            'CyberNut',
            'cybernut@galacticempire.local',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewHmGJB/K4A.Wy7O', -- hashed 'admin123'
            true,
            true,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            true,
            true,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        ) RETURNING id INTO user_id;
        
        RAISE NOTICE 'Created CyberNut user with ID: %', user_id;
    ELSE
        RAISE NOTICE 'CyberNut user already exists with ID: %', user_id;
    END IF;
    
    -- Create or update UserAccount record
    SELECT id INTO user_account_id FROM user_accounts WHERE user_id = user_id;
    
    IF user_account_id IS NULL THEN
        -- Create UserAccount
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
            user_id,
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
        -- Update existing UserAccount
        UPDATE user_accounts 
        SET is_admin = true, is_sysop = true, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = user_id;
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
        WHERE user_id = user_id AND role_id = admin_role_id
    ) THEN
        INSERT INTO user_roles (user_id, role_id)
        VALUES (user_id, admin_role_id);
        RAISE NOTICE 'Assigned admin role to CyberNut';
    ELSE
        RAISE NOTICE 'CyberNut already has admin role';
    END IF;
    
    -- Show final status
    RAISE NOTICE '=== SETUP COMPLETE ===';
    RAISE NOTICE 'CyberNut User ID: %', user_id;
    RAISE NOTICE 'Login: CyberNut';
    RAISE NOTICE 'Email: cybernut@galacticempire.local';
    RAISE NOTICE 'Password: admin123';
    RAISE NOTICE 'IMPORTANT: Change the default password after first login!';
    
END $$;

-- Verify the setup
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



