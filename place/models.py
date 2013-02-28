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
    iso3166_2 = models.CharField(blank=True, null=True, max_length=2)
    iso3166_3 = models.CharField(blank=True, null=True, max_length=3)
    name = models.TextField(blank=True)
    
    objects = models.GeoManager()
   
    def __unicode__(self):
        return '{2}'.format(self.iso3166_2, self.iso3166_3, self.name)
    
    def __str__(self):
        return self.__unicode__()
    
    class Meta:
        db_table = 'country'
        verbose_name_plural = 'Countries'


class Lang(models.Model):
    iso639_1 = models.CharField(blank=True, null=True, max_length=2)
    iso639_2 = models.CharField(blank=True, null=True, max_length=3)
    name = models.TextField(blank=True)
    
    objects = models.GeoManager()

    def __unicode__(self):
        return '{2}'.format(self.iso639_1, self.iso639_2, self.name)
    
    def __str__(self):
        return self.__unicode__()
    
    class Meta:
        db_table = 'lang'

class Place(models.Model):
    id = models.BigIntegerField(primary_key=True)
    osm_id = models.BigIntegerField(blank=True, null=True)
    type = models.ForeignKey(Type, blank=True, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)
    location = models.GeometryField(blank=True, null=True)
    admin_level = models.IntegerField(blank=True, null=True)
    population = models.BigIntegerField(blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    
    objects = models.GeoManager()
          
    def __unicode__(self):
        return 'osm_Id: {0}'.format(self.osm_id)
    
    def __str__(self):
        return self.__unicode__()
    
    class Meta:
        db_table = 'place'
        
class Postcode(models.Model):
    id = models.BigIntegerField(primary_key=True)
    osm_id = models.BigIntegerField(blank=True, null=True)
    type = models.ForeignKey(Type, blank=True, null=True)
    location = models.GeometryField(blank=True, null=True)
    main = models.TextField(blank=True, null=True)
    sup = models.TextField(blank=True, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)
    parent = models.ForeignKey(Place, blank=True, null=True)
    
    objects = models.GeoManager()
    
    def __unicode__(self):
        return '{1} {2}'.format(self.osm_id, self.main, self.sup)
    
    def __str__(self):
        return self.__unicode__()
    
    class Meta:
        db_table = 'postcode'

class PlaceName(models.Model):
    id = models.BigIntegerField(primary_key=True)
    place = models.ForeignKey(Place, blank=True, null=True)
    lang = models.ForeignKey(Lang, blank=True, null=True)
    type = models.ForeignKey(Type, blank=True, null=True)
    name = models.TextField(blank=True)
    name_hash = models.CharField(blank=True, max_length=32)
    
    objects = models.GeoManager()
        
    def __unicode__(self):
        return self.name
    
    def __str__(self):
        return self.__unicode__()
    
    class Meta:
        db_table = 'place_name'

# Helper functions

def get_country_name_lang(query, langs):
    country = PlaceName.objects.filter(type__id=get_type_id('country'), name__iexact=query, lang__in=langs)  # TODO: Why no results?
    if country is not None:
        country = PlaceName.objects.filter(type__id=get_type_id('country'), name__iexact=query)
        if country is not None:
            country = Country.objects.filter(Q(iso3166_2__iexact=query) | Q(iso3166_3__iexact=query))
    if country is not None:
        return None, None
    
    try:
        return country[0].name, country.lang
    except AttributeError:
        return country[0].name, None

def get_type_id(type_name):
    if type_name not in type_ids:
        type_ids[type_name] = Type.objects.get(name=type_name).id
    return type_ids[type_name]

def get_place_name(place, langs):
        
    result = place.placename_set.filter(lang__in=langs)
    
    if result is not None:
        # Often the default name has no language set
        # We specify 'name' as a type because sometimes we might have two names of lang null, one being a prefix p.ex
        result = place.placename_set.filter(lang__isnull=True, type__id=get_type_id('name'))
        
        if result is not None:
            result = place.placename_set.all()  # Any old language will have to do
        
    return result[0].name
