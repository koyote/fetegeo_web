-- Building postcode areas
UPDATE postcode
SET location = ST_BuildArea(location)
WHERE ST_BuildArea(location) IS NOT NULL;

-- Building place areas
UPDATE place
SET location = ST_BuildArea(location)
WHERE ST_BuildArea(location) IS NOT NULL;

-- Homogenising place locations
UPDATE place
SET location = ST_CollectionHomogenize(location);

-- Homogenising postcode locations
UPDATE postcode
SET location = ST_CollectionHomogenize(location);

-- Removing invalid postcode locations
UPDATE postcode
SET location = null
WHERE NOT ST_IsValid(location);

-- Removing invalid place locations
UPDATE place
SET location = null
WHERE NOT ST_IsValid(location);

-- Clustering place location
CLUSTER place_location_id ON place;

-- Clustering postcode location
CLUSTER postcode_location_id ON postcode;

-- Updating postcode countries
UPDATE postcode
SET country_id = place.country_id
FROM place
WHERE place.country_id IS NOT NULL AND ST_Covers(place.location, postcode.location);

-- Updating place countries
UPDATE place
SET country_id = p2.country_id
FROM place as p2
WHERE p2.country_id IS NOT NULL AND ST_Covers(p2.location, place.location);

-- Set postcode area
UPDATE postcode
SET area = ST_Area(location);

-- Set place area
UPDATE place
SET area = ST_Area(location);

-- Create postcode area index
CREATE INDEX on postcode(area);

-- Create place area index
CREATE INDEX on place(area);

-- Vacuum Analyse

-- Computing postcode parents
UPDATE postcode
SET parent_id = b_id
FROM (
  SELECT small.id as s_id, big.id as b_id
  FROM postcode as small, place as big
  WHERE big.area = (
	  SELECT MIN(b2.area)
	  FROM place as b2
	  WHERE ST_Covers(b2.location, small.location)
	  AND NOT ST_Equals(b2.location, small.location)
	  AND ST_GeometryType(b2.location) IN ('ST_Polygon', 'ST_MultiPolygon')
	  )
) pp
WHERE id = s_id;

-- Computing place parents
UPDATE place
SET parent_id = b_id
FROM (
  SELECT small.id as s_id, big.id as b_id
  FROM place as small, place as big
  WHERE big.area = (
	  SELECT MIN(b2.area)
	  FROM place as b2
	  WHERE ST_Covers(b2.location, small.location)
	  AND NOT ST_Equals(b2.location, small.location)
	  AND ST_GeometryType(b2.location) IN ('ST_Polygon', 'ST_MultiPolygon')
	  )
) pp
WHERE id = s_id;