from rest_framework import serializers

class ResultSerialiser(serializers.Serializer):
    osm_id = serializers.IntegerField()
    population = serializers.IntegerField()
    location = serializers.CharField()
    pp = serializers.CharField()