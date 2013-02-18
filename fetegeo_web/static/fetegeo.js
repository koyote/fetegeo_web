var map, marker, polyline, polygon, result = {};
function initialize(lat_ng) {
	var mapOptions = {
		center : new google.maps.LatLng(lat_ng[0], lat_ng[1]),
		zoom : 8,
		mapTypeId : google.maps.MapTypeId.ROADMAP
	};
	map = new google.maps.Map(document.getElementById('map'), mapOptions);
}

function getBounds(coorArray) {
	var bounds = new google.maps.LatLngBounds();
	for ( i = 0, len = coorArray.length; i < len; i++) {
		bounds.extend(coorArray[i]);
	}
	return bounds;
}

function getResult(id, type) {
	// Cache key
	r = id + type;
	if (!result[r]) {
		$.ajax({
			type : "POST",
			url : "/api/loc/" + id + ".json",
			data : {
				'type' : type
			},
			async : false,
			dataType : 'json'
		}).done(function(data) {
			if (!data["error"]) {
				result[r] = {
					lat : data["x"],
					lng : data["y"],
					type : data["type"],
					centerLat : data["centroidX"],
					centerLng : data["centroidY"]
				};
			}
		});
	}
	return result[r];
};

function populateMap(result) {
	var coorArray = [];
	for ( i = 0; i < result.lat.length; i++) {
		coorArray[i] = new google.maps.LatLng(result.lat[i], result.lng[i]);
	}
	switch (result.type) {
		case 'Point':
			var coor = new google.maps.LatLng(result.lat, result.lng);
			if (marker)
				marker.setMap();
			marker = new google.maps.Marker({
				map : map,
				position : coor
			});
			map.setZoom(15);
			break;
		case 'LineString':
		case 'MultiLineString':
			if (polyline)
				polyline.setMap();
			polyline = new google.maps.Polyline({
				path : coorArray,
				strokeColor : '#FF0000',
				strokeOpacity : 1.0,
				strokeWeight : 2,
				map : map
			});
			map.fitBounds(getBounds(coorArray));
			break;
		case 'Polygon':
		case 'MultiPolygon':
			if (polygon)
				polygon.setMap();
			polygon = new google.maps.Polygon({
				paths : coorArray,
				strokeColor : '#FF0000',
				strokeOpacity : '1.0',
				strokeWeight : 2,
				fillColor : '#FF0000',
				fillOpacity : 0.35,
				map : map
			});
			map.fitBounds(getBounds(coorArray));
			break;
	}
	center = new google.maps.LatLng(result.centerLat, result.centerLng);
	map.panTo(center);
}


$(document).ready(function() {
	function resultOnclick() {
		$('div[class^=results]').each(function() {
			$(this).click(function() {
				var result = getResult(this.id, $(this).attr('name'));
				if (result)
					populateMap(result);
			}).hover(function() {
				this.className = this.className.replace('OFF', 'ON');
			}, function() {
				this.className = this.className.replace('ON', 'OFF');
			});
		})
	}

	resultOnclick();
});
