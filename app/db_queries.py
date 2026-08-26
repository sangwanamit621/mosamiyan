"""
Raw parameterised SQL queries for user favorites and preferences.
"""

# Default anonymous user ID for MVP
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"

# Query to list all saved locations for a user (ordered by display order and creation)
GET_SAVED_LOCATIONS_SQL = """
SELECT id, user_id, city_name, country_code, latitude, longitude, display_order, created_at
FROM saved_locations
WHERE user_id = $1
ORDER BY display_order ASC, created_at ASC;
"""

# Query to check existing favorite location count for MVP limit (max 5)
COUNT_SAVED_LOCATIONS_SQL = """
SELECT COUNT(*) as count
FROM saved_locations
WHERE user_id = $1;
"""

# Query to insert a favorite location
INSERT_SAVED_LOCATION_SQL = """
INSERT INTO saved_locations (user_id, city_name, country_code, latitude, longitude, display_order)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (user_id, latitude, longitude) DO UPDATE 
SET city_name = EXCLUDED.city_name, country_code = EXCLUDED.country_code
RETURNING id, user_id, city_name, country_code, latitude, longitude, display_order, created_at;
"""

# Query to delete a favorite location by ID
DELETE_SAVED_LOCATION_SQL = """
DELETE FROM saved_locations
WHERE id = $1 AND user_id = $2
RETURNING id;
"""

# Health check SQL
DB_HEALTH_CHECK_SQL = "SELECT 1 as alive;"
