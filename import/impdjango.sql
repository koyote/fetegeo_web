CLUSTER place_location_id ON place;
CLUSTER postcode_location_id ON postcode;

UPDATE postcode
SET location = ST_BuildArea(location)
WHERE ST_BuildArea(location) IS NOT NULL;

UPDATE place
SET location = ST_BuildArea(location)
WHERE ST_BuildArea(location) IS NOT NULL;

UPDATE place
SET location = ST_CollectionHomogenize(location);

UPDATE postcode
SET location = ST_CollectionHomogenize(location);

UPDATE place
SET location = null
WHERE NOT ST_IsValid(location);

UPDATE postcode
SET location = null
WHERE NOT ST_IsValid(location);

UPDATE postcode
SET country_id = place.country_id
FROM place
WHERE place.country_id IS NOT NULL AND ST_Covers(place.location, postcode.location);

UPDATE place
SET country_id = p2.country_id
FROM place as p2
WHERE p2.country_id IS NOT NULL AND ST_Covers(p2.location, place.location);

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