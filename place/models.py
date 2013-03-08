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

from django.contrib.gis.db import models
from django.contrib.gis.db.models import Q

type_ids = {}


class Type(models.Model):
    name = models.TextField()

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()

    class Meta:
        db_table = 'type'


class Country(models.Model):
    iso3166_2 = models.CharField(null=True, max_length=2)
    iso3166_3 = models.CharField(null=True, max_length=3)
    name = models.TextField()

    objects = models.GeoManager()

    def __unicode__(self):
        return '{2}'.format(self.iso3166_2, self.iso3166_3, self.name)

    def __str__(self):
        return self.__unicode__()

    class Meta:
        db_table = 'country'
        verbose_name_plural = 'Countries'


class Lang(models.Model):
    iso639_1 = models.CharField(null=True, max_length=2)
    iso639_2 = models.CharField(null=True, max_length=3)
    name = models.TextField()

    objects = models.GeoManager()

    def __unicode__(self):
        return '{2}'.format(self.iso639_1, self.iso639_2, self.name)

    def __str__(self):
        return self.__unicode__()

    class Meta:
        db_table = 'lang'


class Place(models.Model):
    id = models.BigIntegerField(primary_key=True)
    osm_id = models.BigIntegerField()
    type = models.ForeignKey(Type, null=True)
    country = models.ForeignKey(Country, null=True)
    location = models.GeometryField(null=True)
    admin_level = models.IntegerField(null=True)
    population = models.BigIntegerField(null=True)
    parent = models.ForeignKey('self', null=True)
    area = models.FloatField(db_index=True, null=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return 'osm_Id: {0}'.format(self.osm_id)

    def __str__(self):
        return self.__unicode__()

    class Meta:
        db_table = 'place'


class Postcode(models.Model):
    id = models.BigIntegerField(primary_key=True)
    osm_id = models.BigIntegerField()
    type = models.ForeignKey(Type, null=True)
    location = models.GeometryField(null=True)
    main = models.TextField(null=True)
    sup = models.TextField(null=True)
    country = models.ForeignKey(Country, null=True)
    parent = models.ForeignKey(Place, null=True)
    area = models.FloatField(db_index=True, null=True)

    objects = models.GeoManager()

    def __unicode__(self):
        return '{1} {2}'.format(self.osm_id, self.main, self.sup)

    def __str__(self):
        return self.__unicode__()

    class Meta:
        db_table = 'postcode'


class PlaceName(models.Model):
    id = models.BigIntegerField(primary_key=True)
    place = models.ForeignKey(Place)
    lang = models.ForeignKey(Lang, null=True)
    type = models.ForeignKey(Type, null=True)
    name = models.TextField()
    name_hash = models.CharField(max_length=32)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.__unicode__()

    class Meta:
        db_table = 'place_name'

# Helper functions


def get_country_name_lang(query, langs):
    """
    Returns the country name in a specific language.
    If it can't find it it will return the name in English.
    """
    country = PlaceName.objects.filter(type__id=get_type_id('country'), name__iexact=query, lang__in=langs)  # TODO: Why no results?
    if not country:
        country = PlaceName.objects.filter(type__id=get_type_id('country'), name__iexact=query)
        if not country:
            country = Country.objects.filter(Q(iso3166_2__iexact=query) | Q(iso3166_3__iexact=query))
            if not country:
                return None, None

    try:
        return country[0].name, country.lang
    except AttributeError:
        return country[0].name, None


def get_type_id(type_name):
    """
    Return the id of a given type. The type is also saved in a 'cache'
    """
    if type_name not in type_ids:
        type_ids[type_name] = Type.objects.get(name=type_name).id
    return type_ids[type_name]


def get_place_name(place, langs):
    """
    Returns the place name in one of the given languages.
    If it can't find it in the language specified it will try and return the official name.
    If all else fails it will return any name attached to the place.
    """

    try:
        # Find name in language chosen
        return place.placename_set.filter(lang__in=langs)[0].name
    except IndexError:
        try:
            # Find the official name
            return place.placename_set.filter(type__id=get_type_id('name'))[0].name
        except IndexError:
            # Nothing found, return any name
            return place.placename_set.all()[0].name
