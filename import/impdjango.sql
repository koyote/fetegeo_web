-- Clustering place location
CLUSTER place_location_id ON place;

-- Clustering postcode location
CLUSTER postcode_location_id ON postcode;

-- Building postcode areas
UPDATE postcode
SET location = ST_BuildArea(location)
WHERE ST_BuildArea(location) IS NOT NULL;

-- Building place areas
UPDATE place
SET location = ST_BuildArea(location)
WHERE ST_BuildArea(location) IS NOT NULL;

-- Building homogenising place locations
UPDATE place
SET location = ST_CollectionHomogenize(location);

-- Building homogenising postcode locations
UPDATE postcode
SET location = ST_CollectionHomogenize(location);

-- Removing invalid place locations
UPDATE place
SET location = null
WHERE NOT ST_IsValid(location);

-- Removing invalid postcode locations
UPDATE postcode
SET location = null
WHERE NOT ST_IsValid(location);

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

-- Updating place parents
UPDATE place
SET parent_id = b_id
FROM (
  SELECT small.id as s_id, big.id as b_id
  FROM place as small, place as big
  WHERE ST_Area(big.location) = (
	  SELECT MIN(ST_Area(b2.location))
	  FROM place as b2
	  WHERE ST_Covers(b2.location, small.location)
	  AND NOT ST_Equals(b2.location, small.location)
	  AND ST_GeometryType(b2.location) IN ('ST_Polygon', 'ST_MultiPolygon')
	  )
) pp
WHERE id = s_id;

-- Updating postcode parents
UPDATE postcode
SET parent_id = b_id
FROM (
  SELECT small.id as s_id, big.id as b_id
  FROM postcode as small, place as big
  WHERE ST_Area(big.location) = (
	  SELECT MIN(ST_Area(b2.location))
	  FROM place as b2
	  WHERE ST_Covers(b2.location, small.location)
	  AND NOT ST_Equals(b2.location, small.location)
	  AND ST_GeometryType(b2.location) IN ('ST_Polygon', 'ST_MultiPolygon')
	  )
) pp
WHERE id = s_id;