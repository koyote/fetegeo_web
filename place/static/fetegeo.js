var map, vector, geojson_format, result = {}, osm;

// Initialise the  map.
function initialise(lngLat) {
    console.log(lngLat);
    var proj = new OpenLayers.Projection("EPSG:4326"); // Transform from WGS 1984
    map = new OpenLayers.Map('map');
    osm = new OpenLayers.Layer.OSM();
    map.addLayer(osm);
    map.setCenter(new OpenLayers.LonLat(lngLat[0], lngLat[1]).transform(proj, map.getProjectionObject()), 8);
    geojson_format = new OpenLayers.Format.GeoJSON({'internalProjection': map.getProjectionObject(), 'externalProjection': proj});
    vector = new OpenLayers.Layer.Vector();
    map.addLayer(vector);
}

// Send an API call to get a cached JSON object of a specified place/postcode's location.
function getResult(id, type) {
    // Cache key
    var r = id + type;
    if (!result[r]) {
        $.ajax({
                   type: "GET",
                   url: "/api/loc/" + type + "/" + id + ".json",
                   async: false,
                   dataType: 'json'
               }).done(function (data) {
                           if (!data.error) {
                               result[r] = {
                                   geometry: data.geometry,
                                   centroid: data.centroid
                               };
                           }
                       });
    }
    return result[r];
}

// Handle different location results and process them.
function populateMap(result) {
    var feature = {
        "type": "FeatureCollection",
        "features": [
            {"geometry": jQuery.parseJSON(result.geometry),
                "type": "Feature",
                "properties": {}}
        ]
    };
    vector.addFeatures(geojson_format.read(feature));
}

$(document).ready(function () {
    function resultOnclick() {
        $('div[class^=results]').each(function () {
            $(this).click(function () {
                var result = getResult(this.id, $(this).attr('name'));
                if (result) {
                    populateMap(result);
                }
            }).hover(function () {
                         this.className = this.className.replace('OFF', 'ON');
                     }, function () {
                         this.className = this.className.replace('ON', 'OFF');
                     });
        });
    }

    resultOnclick();
});

/*

 // Returns a bounding area that encompasses the coordinates in the given array.
 function getBounds(coorArray) {
 var bounds = new google.maps.LatLngBounds();
 for (var i = 0, cLen = coorArray.length; i < cLen; i++) {
 if ($.isArray(coorArray[i])) {
 for (var j = 0, jLen = coorArray[i].length; j < jLen; j++) {
 bounds.extend(coorArray[i][j]);
 }
 } else {
 bounds.extend(coorArray[i]);
 }
 }
 return bounds;
 }
 */