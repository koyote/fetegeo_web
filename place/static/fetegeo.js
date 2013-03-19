var map, vector, geojsonFormat, result = {};
var form = $("#searchForm"), startEl = $("#id_start"), limit = $("#id_limit").val();

var spinOpts = {
    lines: 9, // The number of lines to draw
    length: 0, // The length of each line
    width: 4, // The line thickness
    radius: 10, // The radius of the inner circle
    corners: 1, // Corner roundness (0..1)
    rotate: 26, // The rotation offset
    speed: 1.4, // Rounds per second
    trail: 60, // Afterglow percentage
    top: 10 // Top position relative to parent in px
};

// Initialise the map.
function initialise(lonLat) {
    var proj = new OpenLayers.Projection("EPSG:4326"); // Transform from WGS 1984
    var googLayer = new OpenLayers.Layer.Google(
        "Google Maps",
        {
            type: google.G_PHYSICAL_MAP
        }
    );
    vector = new OpenLayers.Layer.Vector('Result Vector', {
        style: {
            strokeColor: 'black',
            strokeWidth: 2.5,
            strokeOpacity: 0.7,
            fillOpacity: 0.2,
            externalGraphic: 'http://www.openlayers.org/dev/img/marker.png',
            graphicWidth: 25,
            graphicHeight: 25
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
function resultOnclick() {
    $('div[class^=results]').each(function () {
        $(this).click(function () {
            var result = getResult(this.id, $(this).attr('name'));
            if (result) {
                populateMap(result);
            }
        });
    });
}

// Click handler for page numbers
function pageOnclick() {
    $('div[class^=page]').each(function () {
        var pageNum = parseInt($(this).text());
        $(this).click(function (e) {
            startEl.val(limit * (pageNum - 1));
            form.submit();
            startEl.val(0); // needed for the search button to operate properly again
        });
    });
}

// Populate Results List with ajax
$(function () {
      var sb = $("#searchButton");
      var ajw = $("#ajaxwrapper");

      form.submit(function (e) {
          sb.attr('disabled', true);
          ajw.empty();
          ajw.spin(spinOpts);
          ajw.load(
              '/ #ajaxwrapper',
              form.serializeArray(),
              function () {
                  sb.attr('disabled', false);
                  resultOnclick();
                  pageOnclick();
              }
          );
          e.preventDefault();
      });
  }
);

// JQuery plugin for spinner
$.fn.spin = function (opts) {
    this.each(function () {
        var $this = $(this),
            data = $this.data();

        if (data.spinner) {
            data.spinner.stop();
            delete data.spinner;
        }
        if (opts !== false) {
            data.spinner = new Spinner($.extend({color: $this.css('color')}, opts)).spin(this);
        }
    });
    return this;
};
