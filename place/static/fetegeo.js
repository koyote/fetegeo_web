var map, vector, geojsonFormat, result = {};

// Initialise the map.
function initialise(lonLat) {
    var proj = new OpenLayers.Projection("EPSG:4326"); // Transform from WGS 1984
    var googLayer = new OpenLayers.Layer.Google(
        "Google Maps",
        {type: google.G_PHYSICAL_MAP}
    );
    vector = new OpenLayers.Layer.Vector('Result Vector', {
        style: {
            strokeColor: 'black',
            strokeWidth: 2.5,
            strokeOpacity: 0.7,
            fillOpacity: 0.2
        }
    });
    map = new OpenLayers.Map('map');
    map.addControl(new OpenLayers.Control.LayerSwitcher());
    map.addLayers([new OpenLayers.Layer.OSM(), googLayer, vector]);
    map.setCenter(new OpenLayers.LonLat(lonLat).transform(proj, map.getProjectionObject()), 8);
    geojsonFormat = new OpenLayers.Format.GeoJSON({'internalProjection': map.getProjectionObject(), 'externalProjection': proj});
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
                               result[r] = data.geometry;
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
            {
                "geometry": jQuery.parseJSON(result),
                "type": "Feature",
                "properties": {}
            }
        ]
    };
    vector.removeAllFeatures();
    vector.addFeatures(geojsonFormat.read(feature));
    map.zoomToExtent(vector.getDataExtent());
}

// Click handler for results list
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