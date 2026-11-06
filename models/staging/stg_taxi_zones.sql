{{ config(materialized='view') }}

-- ==============================================================================
-- STAGING MODEL: stg_taxi_zones
-- Vrstva: Staging (Číselník zón)
-- ==============================================================================

WITH source_data AS (
    SELECT * FROM {{ source('raw', 'taxi_zones') }}
)

SELECT
    LocationID AS location_id,
    Borough AS borough,
    Zone AS zone_name,
    service_zone
FROM source_data
