-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    unit_preference VARCHAR(10) DEFAULT 'metric' CHECK (unit_preference IN ('metric', 'imperial')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Saved Locations Table
CREATE TABLE IF NOT EXISTS saved_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    city_name VARCHAR(150) NOT NULL,
    country_code VARCHAR(10) NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    display_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, latitude, longitude)
);

-- 3. Web Push Subscriptions Table
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,
    auth_key TEXT NOT NULL,
    latitude NUMERIC(8, 5) NOT NULL,
    longitude NUMERIC(8, 5) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Severe Weather Alerts History (Audit & Deduplication)
CREATE TABLE IF NOT EXISTS weather_alerts (
    id VARCHAR(100) PRIMARY KEY, -- Hash of provider alert ID
    event_title VARCHAR(255) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    headline TEXT,
    description TEXT,
    instructions TEXT,
    boundary_geojson JSONB,
    starts_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create default anonymous/demo user for MVP
INSERT INTO users (id, email, unit_preference)
VALUES ('00000000-0000-0000-0000-000000000001', 'demo@mosamiyan.app', 'metric')
ON CONFLICT (email) DO NOTHING;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_saved_locations_user ON saved_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subs_coords ON push_subscriptions(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_alerts_expiry ON weather_alerts(expires_at);
