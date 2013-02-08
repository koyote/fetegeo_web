from django.contrib.gis import admin 
from place.models import Place, PlaceName 
    
admin.site.register(Place, admin.OSMGeoAdmin)
admin.site.register(PlaceName, admin.OSMGeoAdmin)