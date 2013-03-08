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
from place.models import get_place_name, PlaceName, get_type_id
from django.db import connection


class Queryier:
    def __init__(self):
        self.flush_caches()
        self.ft = FreeText.FreeText()

    def search(self, langs, find_all, allow_dangling, qs, host_country):
        return self.ft.search(self, langs, find_all, allow_dangling, qs, host_country)

    def flush_caches(self):
        self.country_id_iso2_cache = {}  # These are both too small
        self.country_iso2_id_cache = {}  # to bother with a cached dict.
        self.country_name_cache = {}
        self.place_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.place_name_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.place_pp_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.parent_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)
        self.results_cache = Temp_Cache.Cached_Dict(Temp_Cache.SMALL_CACHE_SIZE)
        self.merged_location_cache = Temp_Cache.Cached_Dict(Temp_Cache.LARGE_CACHE_SIZE)

    def pp_place(self, place):
        langs = self.ft.langs
        cache_key = (tuple(langs), place)
        if cache_key in self.place_pp_cache:
            return self.place_pp_cache[cache_key]

        # Recursive query to get all parents (faster than letting django do place.parent.parent.parent etc.)
        # This query returns a list of ids in descending order which is essentially the path from place to its parents.
        c = connection.cursor()
        c.execute(
            "WITH RECURSIVE places_cte(id, parent_id, path) "
            "AS (SELECT tp.id, tp.parent_id, tp.id::TEXT AS path "
            "FROM place AS tp WHERE tp.parent_id IS NULL UNION ALL "
            "SELECT c.id,  c.parent_id, (p.path || ',' || c.id) "
            "FROM places_cte AS p, place AS c WHERE c.parent_id = p.id) "
            "SELECT path FROM places_cte AS n WHERE n.id = {};".format(place.id)
        )

        place_ids = c.fetchone()[0].split(',')
        pp = self.pn(place_ids, langs)

        self.place_pp_cache[cache_key] = pp

        return pp

    def pn(self, ids, langs):
        """
        This complicated method greatly speeds up getting the names of specified parent ids in order.
        It returns a dict of names in order of importance (admin_level).
        """

        # We save each place name with its admin level (10 to 1).
        # The OSM admin level is sometimes set high for simple Nodes; we do not want that, so we define our own admin_level
        pp = {}
        al = 10
        names = [(n.place.id, n.type.id, n.name, n.lang) for n in PlaceName.objects.prefetch_related('place', 'type', 'lang').filter(place__id__in=ids)]
        for i in reversed(ids):
            n_sub = [n for n in names if n[0] == int(i)]
            for n in n_sub:
                if n[3] in langs:
                    pp[al] = n[2]
                    break
                elif n[1] == get_type_id('name'):
                    pp[al] = n[2]
                    break
                else:
                    pp[al] = n[2]
            al -= 1

        return pp

    def pp_postcode(self, postcode):
        if postcode.sup:
            name = "-".join([postcode.main, postcode.sup])
        else:
            name = postcode.main

        pp = {11: name}

        if postcode.parent is not None:
            pp.update(self.pp_place(postcode.parent))

        return pp
