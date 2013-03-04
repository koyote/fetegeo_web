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
from place.models import get_place_name

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
        if self.place_pp_cache.has_key(cache_key):
            return self.place_pp_cache[cache_key]
        
        # We save each place name with its admin level (10 to 1).
        # If no admin level is found we'll just use one that is one less than the last.
        al = 11
        pp = {}
        
        while place is not None:
            al = place.admin_level or al - 1
            pp[al] = get_place_name(place, langs)
            place = place.parent

        self.place_pp_cache[cache_key] = pp

        return pp
    
    def pp_postcode(self, postcode):
        if postcode.sup:
            name = "-".join([postcode.main, postcode.sup])
        else:
            name = postcode.main
        
        pp = {11:name}
    
        if postcode.parent is not None:
            pp.update(self.pp_place(postcode.parent))

        return pp
