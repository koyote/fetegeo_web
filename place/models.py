from django.contrib.gis.db import models 

    
class Type(models.Model):
    name = models.TextField()
    objects = models.GeoManager()
   
    def __unicode__(self):
        return self.name
    
    class Meta:
        db_table = 'type'

class Country(models.Model):
    iso3166_2 = models.CharField(blank=True, null=True, max_length=2)
    iso3166_3 = models.CharField(blank=True, null=True, max_length=3)
    name = models.TextField(blank=True)
    objects = models.GeoManager()
   
    def __unicode__(self):
        return '{2}'.format(self.iso3166_2, self.iso3166_3, self.name)
    
    class Meta:
        db_table = 'country'
        verbose_name_plural='Countries'


class Lang(models.Model):
    iso639_1 = models.CharField(blank=True, null=True, max_length=2)
    iso639_2 = models.CharField(blank=True, null=True, max_length=3)
    name = models.TextField(blank=True)
    objects = models.GeoManager()

    def __unicode__(self):
        return '{2}'.format(self.iso639_1, self.iso639_2, self.name)
    
    class Meta:
        db_table = 'lang'
        
class Postcode(models.Model):
    id = models.BigIntegerField(primary_key=True)
    osm_id = models.BigIntegerField(blank=True, null=True)
    type = models.ForeignKey(Type, blank=True, null=True)
    location = models.GeometryField(blank=True, null=True)
    main = models.TextField(blank=True, null=True)
    sup = models.TextField(blank=True, null=True)
    #country_id = models.BigIntegerField(blank=True, null=True)
    #parent_id = models.BigIntegerField(blank=True, null=True)
    #area = models.FloatField(blank=True, null=True)
    objects = models.GeoManager()
    
    def __unicode__(self):
        return '{1} {2}'.format(self.osm_id, self.main, self.sup)
    
    class Meta:
        db_table = 'postcode'

class Place(models.Model):
    id = models.BigIntegerField(primary_key=True)
    osm_id = models.BigIntegerField(blank=True, null=True)
    type = models.ForeignKey(Type, blank=True, null=True)
    postcode = models.ForeignKey(Postcode, blank=True, null=True)
    country = models.ForeignKey(Country, blank=True, null=True)
    location = models.GeometryField(blank=True, null=True)
    admin_level = models.IntegerField(blank=True, null=True)
    population = models.BigIntegerField(blank=True, null=True)
    #parent_id = models.ForeignKey('self', blank=True, null=True)
    #area = models.FloatField(blank=True, null=True)
    objects = models.GeoManager()
          
    def __unicode__(self):
        return 'osm_Id: {0}'.format(self.osm_id)
    
    class Meta:
        db_table = 'place'

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
    
    class Meta:
        db_table = 'place_name'

