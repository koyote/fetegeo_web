from rest_framework import serializers

class LocationField(serializers.RelatedField):
    def to_native(self, value):
        return {"type":value.geom_type}, {"coordinates":value.coords}

class ResultSerialiser(serializers.Serializer):
    osm_id = serializers.IntegerField()
    population = serializers.IntegerField()
    location = LocationField()
    pp = serializers.CharField()
