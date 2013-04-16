"""
 Copyright (C) 2008 Laurence Tratt http://tratt.net/laurie/

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

from geo import Temp_Cache, FreeText
from place.models import PlaceName, get_type_id


class Queryier:
    def __init__(self):
        self.flush_caches()
        self.ft = FreeText.FreeText()

    def search(self, langs, find_all, allow_dangling, qs, host_country, admin_levels=[], start=None, limit=None):
        return self.ft.search(self, langs, find_all, allow_dangling, qs, host_country, admin_levels, start, limit)

    def flush_caches(self):
        self.country_id_iso2_cache = {}  # These are both too small
        self.country_iso2_id_cache = {}  # to bother with a cached dict.
        self.country_name_cache = {}
        self.place_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.place_name_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.place_pp_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.parent_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.results_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.limit_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.merged_location_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)

    def pp_place(self, place):
        """
        Pretty print for places. Loops through each place's parent and then sends the ids to pn().
        """
        langs = self.ft.langs
        cache_key = (tuple(langs), place)
        if cache_key in self.place_pp_cache:
            return self.place_pp_cache[cache_key]

        # Retrieve all parent ids
        place_ids = []
        while place:
            place_ids.append(place.id)
            place = place.parent

        pp = self._pretty_name(place_ids, langs)

        self.place_pp_cache[cache_key] = pp

        return pp

    def pp_postcode(self, postcode):
        """
        Pretty print for postcodes
        """
        if postcode.sup:
            name = " ".join([postcode.main, postcode.sup])
        else:
            name = postcode.main

        pp = {11: name}

        if postcode.parent is not None:
            pp.update(self.pp_place(postcode.parent))

        return pp

    def _pretty_name(self, ids, langs):
        """
        This complicated method greatly speeds up getting the names of specified parent ids in order.
        It returns a dict of names in order of importance (admin_level).
        """

        # We save each place name with its admin level (10 to 1).
        # The OSM admin level is sometimes set high for simple Nodes; we do not want that, so we define our own admin_level
        pp = {}
        al = 10
        names = [(n.place_id, n.type_id, n.name, n.lang) for n in PlaceName.objects.prefetch_related('lang').only().filter(place__id__in=ids)]
        for i in ids:
            best = False
            for n in [n for n in names if n[0] == int(i)]:
                if n[3] in langs:
                    pp[al] = n[2]
                    break
                elif n[1] == get_type_id('name'):
                    pp[al] = n[2]
                    best = True
                elif not best:
                    pp[al] = n[2]
            al -= 1

        return pp