from rest_framework import serializers

class LocationField(serializers.RelatedField):
    def to_native(self, value):
        if self.context['show_all']:
            return {"type":value.geom_type}, {"coordinates":value.coords}
        else:
            return {"type":value.geom_type}, {"coordinates":value.centroid.coords}
        

class ResultSerialiser(serializers.Serializer):
    osm_id = serializers.IntegerField()
    population = serializers.IntegerField()
    location = LocationField()
    pp = serializers.CharField()

class SerialisableResult():
    def __init__(self, place, pp):
        self.place = place
        self.pp = pp
        self.osm_id = place.osm_id
        self.location = place.location
        try:
            self.population = place.population
        except AttributeError:
            self.population = None