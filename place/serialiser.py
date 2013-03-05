"""
 Copyright (C) 2013 Pit Apps

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to
 deal in the Software without restriction, including without limitation the
 rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 sell copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 IN THE SOFTWARE.
"""

from rest_framework import serializers

class LocationField(serializers.RelatedField):
    """
    Special location field that handles the 'show_all' option by returning a centroid if needed.
    """
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
    """
    Like the Result class in geo but agnostic about its type (postcode, place)
    """
    def __init__(self, place, pp):
        self.place = place
        self.pp = pp
        self.osm_id = place.osm_id
        self.location = place.location
        try:
            self.population = place.population
        except AttributeError:
            self.population = None