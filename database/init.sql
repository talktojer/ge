-- Galactic Empire Database Initialization
-- This file is executed when the PostgreSQL container starts

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

-- Create a simple test table to verify the database is working
CREATE TABLE IF NOT EXISTS game_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'initializing',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial status
INSERT INTO game_status (status) VALUES ('database_initialized') ON CONFLICT DO NOTHING;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_game_status_created_at ON game_status(created_at);

-- Grant permissions (in production, you'd want more restrictive permissions)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO postgres;
