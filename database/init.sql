-- Galactic Empire Database Initialization
-- This file is executed when the PostgreSQL container starts
-- Based on the original C code data structures

-- Create the database if it doesn't exist (this is handled by POSTGRES_DB env var)
-- But we can create additional schemas or extensions here

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for different game components
CREATE SCHEMA IF NOT EXISTS game;
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS ships;
CREATE SCHEMA IF NOT EXISTS planets;
CREATE SCHEMA IF NOT EXISTS teams;

-- Set default schema
SET search_path TO public, game, users, ships, planets, teams;

-- ============================================================================
-- USER ACCOUNT SYSTEM (Based on WARUSR structure)
-- ============================================================================

-- Users table (WARUSR structure)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    userid VARCHAR(25) UNIQUE NOT NULL,
    score BIGINT DEFAULT 0,
    noships INTEGER DEFAULT 0,
    topshipno INTEGER DEFAULT 0,
    kills INTEGER DEFAULT 0,
    planets INTEGER DEFAULT 0,
    cash BIGINT DEFAULT 0,
    debt BIGINT DEFAULT 0,
    plscore BIGINT DEFAULT 0,
    klscore BIGINT DEFAULT 0,
    population BIGINT DEFAULT 0,
    teamcode BIGINT DEFAULT 0,
    team_id INTEGER,
    scan_names BOOLEAN DEFAULT TRUE,
    scan_home BOOLEAN DEFAULT TRUE,
    scan_full BOOLEAN DEFAULT FALSE,
    msg_filter BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- User accounts table (extended user information)
CREATE TABLE IF NOT EXISTS user_accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_sysop BOOLEAN DEFAULT FALSE,
    preferred_ship_class INTEGER DEFAULT 1,
    auto_repair BOOLEAN DEFAULT FALSE,
    auto_shield BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SHIP MANAGEMENT SYSTEM (Based on WARSHP structure)
-- ============================================================================

-- Ship types table (SHIP structure)
CREATE TABLE IF NOT EXISTS ship_types (
    id SERIAL PRIMARY KEY,
    typename VARCHAR(50) NOT NULL,
    shipname VARCHAR(50) NOT NULL,
    max_shields INTEGER DEFAULT 0,
    max_phasers INTEGER DEFAULT 0,
    max_torpedoes INTEGER DEFAULT 0,
    max_missiles INTEGER DEFAULT 0,
    has_decoy BOOLEAN DEFAULT FALSE,
    has_jammer BOOLEAN DEFAULT FALSE,
    has_zipper BOOLEAN DEFAULT FALSE,
    has_mine BOOLEAN DEFAULT FALSE,
    max_attack INTEGER DEFAULT 0,
    max_cloak INTEGER DEFAULT 0,
    max_acceleration INTEGER DEFAULT 0,
    max_warp INTEGER DEFAULT 0,
    max_tons BIGINT DEFAULT 0,
    max_price BIGINT DEFAULT 0,
    max_points INTEGER DEFAULT 0,
    max_type INTEGER DEFAULT 0,
    scan_range INTEGER DEFAULT 0,
    cybs_can_attack BOOLEAN DEFAULT TRUE,
    lowest_to_attack INTEGER DEFAULT 1,
    no_claim BOOLEAN DEFAULT FALSE,
    total_to_create INTEGER DEFAULT 0,
    tough_factor INTEGER DEFAULT 0,
    damage_factor INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ship classes table
CREATE TABLE IF NOT EXISTS ship_classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    ship_type_id INTEGER REFERENCES ship_types(id),
    class_number INTEGER NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Ships table (WARSHP structure)
CREATE TABLE IF NOT EXISTS ships (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    shipno INTEGER NOT NULL,
    shipname VARCHAR(35) NOT NULL,
    ship_class_id INTEGER REFERENCES ship_classes(id),
    shpclass INTEGER DEFAULT 1,
    heading FLOAT DEFAULT 0.0,
    head2b FLOAT DEFAULT 0.0,
    speed FLOAT DEFAULT 0.0,
    speed2b FLOAT DEFAULT 0.0,
    x_coord FLOAT DEFAULT 0.0,
    y_coord FLOAT DEFAULT 0.0,
    damage FLOAT DEFAULT 0.0,
    energy FLOAT DEFAULT 0.0,
    phaser_strength FLOAT DEFAULT 0.0,
    phaser_type INTEGER DEFAULT 0,
    kills INTEGER DEFAULT 0,
    last_fired INTEGER DEFAULT 0,
    shield_type INTEGER DEFAULT 0,
    shield_status INTEGER DEFAULT 0,
    shield_charge INTEGER DEFAULT 0,
    cloak INTEGER DEFAULT 0,
    tactical INTEGER DEFAULT 0,
    helm INTEGER DEFAULT 0,
    train INTEGER DEFAULT 0,
    where INTEGER DEFAULT 0,
    jammer INTEGER DEFAULT 0,
    freq_subspace INTEGER DEFAULT 0,
    freq_hyperspace INTEGER DEFAULT 0,
    freq_planetary INTEGER DEFAULT 0,
    hostile BOOLEAN DEFAULT FALSE,
    cant_exit INTEGER DEFAULT 0,
    repair BOOLEAN DEFAULT FALSE,
    hypha BOOLEAN DEFAULT FALSE,
    fire_control BOOLEAN DEFAULT FALSE,
    destruct INTEGER DEFAULT 0,
    status INTEGER DEFAULT 0,
    cyb_mine BOOLEAN DEFAULT FALSE,
    cyb_skill INTEGER DEFAULT 0,
    cyb_update INTEGER DEFAULT 0,
    tick INTEGER DEFAULT 0,
    emulate BOOLEAN DEFAULT FALSE,
    mines_near BOOLEAN DEFAULT FALSE,
    lock INTEGER DEFAULT 0,
    hold_course INTEGER DEFAULT 0,
    top_speed INTEGER DEFAULT 0,
    warn_counter INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- PLANET/SECTOR SYSTEM (Based on GALPLNT and GALSECT structures)
-- ============================================================================

-- Sectors table (GALSECT structure)
CREATE TABLE IF NOT EXISTS sectors (
    id SERIAL PRIMARY KEY,
    xsect INTEGER NOT NULL,
    ysect INTEGER NOT NULL,
    plnum INTEGER DEFAULT 0,
    type INTEGER DEFAULT 1,
    num_planets INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Planets table (GALPLNT structure)
CREATE TABLE IF NOT EXISTS planets (
    id SERIAL PRIMARY KEY,
    sector_id INTEGER REFERENCES sectors(id),
    xsect INTEGER NOT NULL,
    ysect INTEGER NOT NULL,
    plnum INTEGER NOT NULL,
    type INTEGER DEFAULT 2,
    x_coord FLOAT DEFAULT 0.0,
    y_coord FLOAT DEFAULT 0.0,
    owner_id INTEGER REFERENCES users(id),
    userid VARCHAR(25) NOT NULL,
    name VARCHAR(20) NOT NULL,
    environment INTEGER DEFAULT 0,
    resource INTEGER DEFAULT 0,
    cash BIGINT DEFAULT 0,
    debt BIGINT DEFAULT 0,
    tax BIGINT DEFAULT 0,
    tax_rate INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    password VARCHAR(10) DEFAULT '',
    last_attacker VARCHAR(25) DEFAULT '',
    spy_owner VARCHAR(25) DEFAULT '',
    technology INTEGER DEFAULT 0,
    team_code BIGINT DEFAULT 0,
    beacon_message VARCHAR(75) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_attack TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- TEAM/ALLIANCE SYSTEM (Based on TEAM structure)
-- ============================================================================

-- Teams table (TEAM structure)
CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    teamcode BIGINT UNIQUE NOT NULL,
    teamname VARCHAR(31) NOT NULL,
    teamcount INTEGER DEFAULT 0,
    teamscore BIGINT DEFAULT 0,
    password VARCHAR(11) DEFAULT '',
    secret VARCHAR(11) DEFAULT '',
    flag INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    max_members INTEGER DEFAULT 50,
    leader_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- MAIL/MESSAGING SYSTEM (Based on MAIL and MAILSTAT structures)
-- ============================================================================

-- Mail table (MAIL structure)
CREATE TABLE IF NOT EXISTS mail (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id),
    recipient_id INTEGER REFERENCES users(id),
    userid VARCHAR(25) NOT NULL,
    class_type INTEGER NOT NULL,
    type INTEGER DEFAULT 0,
    stamp INTEGER DEFAULT 0,
    dtime VARCHAR(20) DEFAULT '',
    topic VARCHAR(30) DEFAULT '',
    string1 VARCHAR(80) DEFAULT '',
    name1 VARCHAR(25) DEFAULT '',
    name2 VARCHAR(25) DEFAULT '',
    int1 INTEGER DEFAULT 0,
    int2 INTEGER DEFAULT 0,
    int3 INTEGER DEFAULT 0,
    long1 BIGINT DEFAULT 0,
    long2 BIGINT DEFAULT 0,
    long3 BIGINT DEFAULT 0,
    is_read BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Mail status table (MAILSTAT structure)
CREATE TABLE IF NOT EXISTS mail_status (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    userid VARCHAR(25) NOT NULL,
    class_type INTEGER NOT NULL,
    type INTEGER DEFAULT 0,
    stamp INTEGER DEFAULT 0,
    dtime VARCHAR(20) DEFAULT '',
    topic VARCHAR(30) DEFAULT '',
    name1 VARCHAR(25) DEFAULT '',
    int1 INTEGER DEFAULT 0,
    int2 INTEGER DEFAULT 0,
    cash BIGINT DEFAULT 0,
    debt BIGINT DEFAULT 0,
    tax BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ITEM/COMMODITY SYSTEM (Based on ITEM structure with 14 item types)
-- ============================================================================

-- Item types table (14 item types from original code)
CREATE TABLE IF NOT EXISTS item_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    keyword VARCHAR(20) NOT NULL UNIQUE,
    description TEXT,
    base_price BIGINT DEFAULT 0,
    max_quantity FLOAT DEFAULT 0.0,
    weight BIGINT DEFAULT 0,
    value BIGINT DEFAULT 0,
    man_hours BIGINT DEFAULT 0,
    category VARCHAR(50) DEFAULT 'general',
    is_consumable BOOLEAN DEFAULT FALSE,
    is_weapon BOOLEAN DEFAULT FALSE,
    is_equipment BOOLEAN DEFAULT FALSE,
    is_resource BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Items table (ITEM structure)
CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    item_type_id INTEGER REFERENCES item_types(id),
    owner_id INTEGER REFERENCES users(id),
    quantity BIGINT DEFAULT 0,
    rate INTEGER DEFAULT 0,
    sell_to_allies BOOLEAN DEFAULT FALSE,
    reserve INTEGER DEFAULT 0,
    markup_to_allies INTEGER DEFAULT 0,
    sold_to_allies BIGINT DEFAULT 0,
    location_type VARCHAR(20) DEFAULT 'user',
    location_id INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Planet items association table
CREATE TABLE IF NOT EXISTS planet_items (
    planet_id INTEGER REFERENCES planets(id),
    item_id INTEGER REFERENCES items(id),
    quantity BIGINT DEFAULT 0,
    rate INTEGER DEFAULT 0,
    sell_to_allies BOOLEAN DEFAULT FALSE,
    reserve INTEGER DEFAULT 0,
    markup_to_allies INTEGER DEFAULT 0,
    sold_to_allies BIGINT DEFAULT 0,
    PRIMARY KEY (planet_id, item_id)
);

-- ============================================================================
-- MINE SYSTEM (Based on MINE structure)
-- ============================================================================

-- Mines table (MINE structure)
CREATE TABLE IF NOT EXISTS mines (
    id SERIAL PRIMARY KEY,
    channel INTEGER NOT NULL,
    timer INTEGER DEFAULT 0,
    x_coord FLOAT DEFAULT 0.0,
    y_coord FLOAT DEFAULT 0.0,
    owner_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    damage_potential INTEGER DEFAULT 100,
    mine_type INTEGER DEFAULT 0,
    is_armed BOOLEAN DEFAULT TRUE,
    is_visible BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    armed_at TIMESTAMP WITH TIME ZONE,
    exploded_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- BEACON SYSTEM (Based on BEACONTAB structure)
-- ============================================================================

-- Beacons table (BEACONTAB structure)
CREATE TABLE IF NOT EXISTS beacons (
    id SERIAL PRIMARY KEY,
    x_coord FLOAT NOT NULL,
    y_coord FLOAT NOT NULL,
    plnum INTEGER DEFAULT 0,
    beacon_message VARCHAR(75) DEFAULT '',
    owner_id INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE,
    beacon_type INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- WORMHOLE SYSTEM (Based on GALWORM and WORMTAB structures)
-- ============================================================================

-- Wormholes table (GALWORM structure)
CREATE TABLE IF NOT EXISTS wormholes (
    id SERIAL PRIMARY KEY,
    xsect INTEGER NOT NULL,
    ysect INTEGER NOT NULL,
    plnum INTEGER DEFAULT 0,
    type INTEGER DEFAULT 3,
    x_coord FLOAT DEFAULT 0.0,
    y_coord FLOAT DEFAULT 0.0,
    dest_x_coord FLOAT DEFAULT 0.0,
    dest_y_coord FLOAT DEFAULT 0.0,
    visible BOOLEAN DEFAULT FALSE,
    name VARCHAR(20) DEFAULT '',
    is_active BOOLEAN DEFAULT TRUE,
    is_stable BOOLEAN DEFAULT TRUE,
    energy_required INTEGER DEFAULT 0,
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Wormhole table (WORMTAB structure)
CREATE TABLE IF NOT EXISTS wormhole_table (
    id SERIAL PRIMARY KEY,
    x_coord FLOAT NOT NULL,
    y_coord FLOAT NOT NULL,
    dest_x_coord FLOAT NOT NULL,
    dest_y_coord FLOAT NOT NULL,
    wormhole_id INTEGER REFERENCES wormholes(id),
    is_active BOOLEAN DEFAULT TRUE,
    table_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- User indexes
CREATE INDEX IF NOT EXISTS idx_users_userid ON users(userid);
CREATE INDEX IF NOT EXISTS idx_users_teamcode ON users(teamcode);
CREATE INDEX IF NOT EXISTS idx_users_score ON users(score);

-- Ship indexes
CREATE INDEX IF NOT EXISTS idx_ships_user_id ON ships(user_id);
CREATE INDEX IF NOT EXISTS idx_ships_shipno ON ships(shipno);
CREATE INDEX IF NOT EXISTS idx_ships_coords ON ships(x_coord, y_coord);

-- Planet indexes
CREATE INDEX IF NOT EXISTS idx_planets_sector_id ON planets(sector_id);
CREATE INDEX IF NOT EXISTS idx_planets_owner_id ON planets(owner_id);
CREATE INDEX IF NOT EXISTS idx_planets_coords ON planets(x_coord, y_coord);
CREATE INDEX IF NOT EXISTS idx_planets_userid ON planets(userid);

-- Team indexes
CREATE INDEX IF NOT EXISTS idx_teams_teamcode ON teams(teamcode);
CREATE INDEX IF NOT EXISTS idx_teams_leader_id ON teams(leader_id);

-- Mail indexes
CREATE INDEX IF NOT EXISTS idx_mail_sender_id ON mail(sender_id);
CREATE INDEX IF NOT EXISTS idx_mail_recipient_id ON mail(recipient_id);
CREATE INDEX IF NOT EXISTS idx_mail_class_type ON mail(class_type);

-- Item indexes
CREATE INDEX IF NOT EXISTS idx_items_item_type_id ON items(item_type_id);
CREATE INDEX IF NOT EXISTS idx_items_owner_id ON items(owner_id);
CREATE INDEX IF NOT EXISTS idx_items_location ON items(location_type, location_id);

-- Mine indexes
CREATE INDEX IF NOT EXISTS idx_mines_owner_id ON mines(owner_id);
CREATE INDEX IF NOT EXISTS idx_mines_coords ON mines(x_coord, y_coord);
CREATE INDEX IF NOT EXISTS idx_mines_channel ON mines(channel);

-- Beacon indexes
CREATE INDEX IF NOT EXISTS idx_beacons_owner_id ON beacons(owner_id);
CREATE INDEX IF NOT EXISTS idx_beacons_coords ON beacons(x_coord, y_coord);

-- Wormhole indexes
CREATE INDEX IF NOT EXISTS idx_wormholes_coords ON wormholes(x_coord, y_coord);
CREATE INDEX IF NOT EXISTS idx_wormholes_dest_coords ON wormholes(dest_x_coord, dest_y_coord);
CREATE INDEX IF NOT EXISTS idx_wormholes_visible ON wormholes(visible);

-- ============================================================================
-- INSERT INITIAL DATA
-- ============================================================================

-- Insert the 14 item types from the original game
INSERT INTO item_types (name, keyword, description, base_price, weight, value, is_weapon, is_equipment, is_resource) VALUES
('Men', 'men', 'Crew members for ships and planets', 1000, 1, 1000, FALSE, FALSE, FALSE),
('Missile', 'missile', 'Offensive missile weapon', 5000, 2, 5000, TRUE, FALSE, FALSE),
('Torpedo', 'torpedo', 'Heavy torpedo weapon', 10000, 5, 10000, TRUE, FALSE, FALSE),
('Ion Cannon', 'ioncannon', 'Ion cannon weapon system', 15000, 3, 15000, TRUE, FALSE, FALSE),
('Flux Pod', 'fluxpod', 'Energy storage device', 2000, 1, 2000, FALSE, TRUE, FALSE),
('Food', 'food', 'Essential supplies for crew', 100, 1, 100, FALSE, FALSE, TRUE),
('Fighter', 'fighter', 'Small fighter craft', 25000, 10, 25000, TRUE, TRUE, FALSE),
('Decoys', 'decoys', 'Defensive decoy systems', 3000, 1, 3000, FALSE, TRUE, FALSE),
('Troops', 'troops', 'Ground combat troops', 500, 1, 500, FALSE, FALSE, FALSE),
('Zippers', 'zippers', 'Teleportation devices', 50000, 2, 50000, FALSE, TRUE, FALSE),
('Jammers', 'jammers', 'Electronic jamming equipment', 8000, 2, 8000, FALSE, TRUE, FALSE),
('Mine', 'mine', 'Space mine weapon', 12000, 3, 12000, TRUE, FALSE, FALSE),
('Gold', 'gold', 'Precious metal currency', 1, 1, 1, FALSE, FALSE, TRUE),
('Spy', 'spy', 'Intelligence operative', 10000, 1, 10000, FALSE, FALSE, FALSE)
ON CONFLICT (keyword) DO NOTHING;

-- Insert basic ship types
INSERT INTO ship_types (typename, shipname, max_shields, max_phasers, max_torpedoes, max_missiles, has_decoy, has_jammer, has_zipper, has_mine, max_attack, max_cloak, max_acceleration, max_warp, max_tons, max_price, scan_range) VALUES
('Scout', 'Scout Ship', 5, 3, 1, 1, FALSE, FALSE, FALSE, FALSE, 50, 10, 100, 5, 1000, 50000, 5000),
('Fighter', 'Fighter', 8, 5, 2, 2, TRUE, FALSE, FALSE, FALSE, 75, 15, 120, 6, 2000, 100000, 6000),
('Destroyer', 'Destroyer', 12, 8, 3, 3, TRUE, TRUE, FALSE, TRUE, 100, 20, 80, 4, 5000, 250000, 8000),
('Cruiser', 'Cruiser', 15, 10, 4, 4, TRUE, TRUE, TRUE, TRUE, 125, 25, 60, 3, 10000, 500000, 10000),
('Battleship', 'Battleship', 20, 15, 6, 6, TRUE, TRUE, TRUE, TRUE, 150, 30, 40, 2, 20000, 1000000, 15000)
ON CONFLICT DO NOTHING;

-- Create a simple test table to verify the database is working
CREATE TABLE IF NOT EXISTS game_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'initializing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial status
INSERT INTO game_status (status) VALUES ('database_initialized') ON CONFLICT DO NOTHING;

-- Grant permissions (in production, you'd want more restrictive permissions)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;