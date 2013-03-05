var map, marker, result = {};

/* Initialise the Google Maps map. */
function initialise(latLng) {
    var mapOptions = {
        center: new google.maps.LatLng(latLng[0], latLng[1]),
        zoom: 8,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    map = new google.maps.Map(document.getElementById('map'), mapOptions);
}

/* Returns a bounding area that encompasses the coordinates in the given array. */
function getBounds(coorArray) {
    var bounds = new google.maps.LatLngBounds();
    for (var i = 0; i < coorArray.length; i++) {
        if ($.isArray(coorArray[i])) {
            for (var j = 0; j < coorArray[i].length; j++) {
                bounds.extend(coorArray[i][j]);
            }
        } else {
            bounds.extend(coorArray[i]);
        }
    }
    return bounds;
}

/* Send an API call to get a cached JSON object of a specified place/postcode's location. */
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
                           if (!data["error"]) {
                               result[r] = {
                                   lat: data["x"],
                                   lng: data["y"],
                                   type: data["type"],
                                   centerLat: data["centroidX"],
                                   centerLng: data["centroidY"]
                               };
                           }
                       });
    }
    return result[r];
}

/* Handle different location results and process them. */
function populateMap(result) {
    var coorArray = [];
    if (result.type == 'MultiPolygon') {
        for (var i = 0; i < result.lat.length; i++) {
            var path = [];
            for (var j = 0; j < result.lat[i].length; j++) {
                path[j] = new google.maps.LatLng(result.lat[i][j], result.lng[i][j]);
            }
            coorArray[i] = path;
        }
    } else {
        for (var i = 0; i < result.lat.length; i++) {
            coorArray[i] = new google.maps.LatLng(result.lat[i], result.lng[i]);
        }
    }
    switch (result.type) {
        case 'Point':
            var coor = new google.maps.LatLng(result.lat, result.lng);
            if (marker) {
                marker.setMap();
            }
            marker = new google.maps.Marker({
                                                map: map,
                                                position: coor
                                            });
            map.setZoom(15);
            break;
        case 'LineString':
        case 'MultiLineString':
            if (marker) {
                marker.setMap();
            }
            marker = new google.maps.Polyline({
                                                  path: coorArray,
                                                  strokeColor: '#FF0000',
                                                  strokeOpacity: 1.0,
                                                  strokeWeight: 2,
                                                  map: map
                                              });
            map.fitBounds(getBounds(coorArray));
            break;
        case 'Polygon':
        case 'MultiPolygon':
            if (marker) {
                marker.setMap();
            }
            marker = new google.maps.Polygon({
                                                 paths: coorArray,
                                                 strokeColor: '#FF0000',
                                                 strokeOpacity: '1.0',
                                                 strokeWeight: 2,
                                                 fillColor: '#FF0000',
                                                 fillOpacity: 0.35,
                                                 map: map
                                             });
            map.fitBounds(getBounds(coorArray));
            break;
    }
    var center = new google.maps.LatLng(result.centerLat, result.centerLng);
    map.panTo(center);
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
        })
    }

    resultOnclick();
});
