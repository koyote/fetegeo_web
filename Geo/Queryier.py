# Copyright (C) 2008 Laurence Tratt http://tratt.net/laurie/
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


from .import Temp_Cache, Free_Text
from place.models import get_place_name, Place

# Here we set a custom set of parents to be added to the pretty print.
# http://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative might help choosing which levels we need for
# each country.
_ADMIN_LEVELS = {"LU": (2, 6, 8), "GB": (2, 4, 6, 8)}
_DEFAULT_LEVEL = (2, 4, 6, 8)


class Queryier:
    def __init__(self):
        self.flush_caches()
        
    def search(self, langs, find_all, allow_dangling, qs, host_country):
        return Free_Text.Free_Text().name_to_lat_long(self, langs, find_all, allow_dangling, qs, host_country)


    def flush_caches(self):
        self.country_id_iso2_cache = {}  # These are both too small
        self.country_iso2_id_cache = {}  # to bother with a cached dict.
        self.country_name_cache = {}
        self.place_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.place_name_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.place_pp_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.parent_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.results_cache = Temp_Cache.Cached_Dict(Temp_Cache.SMALL_CACHE_SIZE)

    def pp_place(self, ft, place):
        cache_key = (tuple(ft.langs), ft.host_country, place)
        if self.place_pp_cache.has_key(cache_key):
            return self.place_pp_cache[cache_key]
        
        iso2 = ''
        if place.country:
            iso2 = place.country.iso3166_2
        
        if iso2 in _ADMIN_LEVELS:
            fmt = _ADMIN_LEVELS[iso2]
        else:
            fmt = _DEFAULT_LEVEL

        pp = get_place_name(place, ft.langs)
        parent = place.parent
        
        while parent is not None:
            p = Place.objects.get(id=parent.id)
            assert(p.parent != parent)

            if p.admin_level in fmt:
                pp = "{0}, {1}".format(pp, get_place_name(parent, ft.langs))

            parent = p.parent

        self.place_pp_cache[cache_key] = pp

        return pp
