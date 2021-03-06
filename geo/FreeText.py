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

import hashlib
import re

from django.contrib.gis.db.models import Q
from unidecode import unidecode
from django.core.cache import cache

from place.models import PlaceName, Country, Postcode, Lang, get_type_id, Place
from geo import Results
from geo.postcodes import UK, US


_RE_IRRELEVANT_CHARS = re.compile("[,\\n\\r\\t;()]")
_RE_SQUASH_SPACES = re.compile(" +")
_RE_SPLIT = re.compile("[ ,/]")
_RE_EU_ZIP = re.compile('^[A-Za-z]{1,3}-[0-9]{3,10}$')


class FreeText:
    def search(self, queryier, langs, find_all, allow_dangling, qs, host_country, admin_levels, start, limit):
        self.queryier = queryier
        self.qs = _cleanup(qs)
        self.split, self.split_indices = _split(self.qs)

        self.langs = [Lang.objects.get(id=lang) for lang in langs]
        self.find_all = find_all
        self.allow_dangling = allow_dangling
        self.host_country = host_country
        self.admin_levels = admin_levels

        if limit:
            limit += start

        results_cache_key = (tuple(langs), find_all, allow_dangling, self.qs, host_country, start, limit)
        if results_cache_key in queryier.results_cache:
            return queryier.results_cache[results_cache_key]

        # If we're just retrieving the next pair of results, we don't want to recompute everything, so the prior results should be in the cache somewhere.
        limit_cache_key = (tuple(langs), find_all, allow_dangling, self.qs, host_country)
        if limit_cache_key in queryier.limit_cache:
            merged_places, result_map, total_results = queryier.limit_cache[limit_cache_key]

            place_names, postcode_names, sorted_places = self._process_pp(merged_places, result_map, start, limit)
            queryier.results_cache[results_cache_key] = place_names, postcode_names, sorted_places, total_results
            return place_names, postcode_names, sorted_places, total_results

        # _matches is a list of lists storing all the matched places (and postcodes etc.) at a given
        # point in the split. self._longest_match is a convenience integer which records the longest
        # current match. Note that since we start from the right hand side of the split (see below)
        # and work left, shorter values of _longest_match are "better".

        self._longest_match = len(self.split)
        self._matches = [[] for _ in range(len(self.split))]

        # _matched_places is a set storing (place_id, i) pairs recording that a place was found at
        # position 'i' in the split. This weeds out duplicates *unless* we're doing loose matching
        # when we might conceivably match the same place twice but with different bits of "loose"
        # text to the left of the match.
        self._matched_places = set()
        self._matched_postcodes = set()  # Analogous to _matched_places.

        # The basic idea of the search is to start from the right hand side of the string and try and
        # match first the country, then any postcodes and places. Note that postcodes and places can
        # come in any order.
        #
        # This is done by splitting the string up into its constituent words and using the current
        # right-hand most word as a candidate match. This copes with the fact that many countries /
        # administrative units have spaces in them.

        for country, i in self._iter_country():
            if i == -1:
                continue
            for _, postcode, j in self._iter_places(i, country):
                if postcode is not None and j + 1 <= self._longest_match:
                    done_key = (postcode.osm_id, j)
                    if done_key in self._matched_postcodes:
                        continue

                    self._matched_postcodes.add(done_key)
                    self._longest_match = j + 1
                    self._matches[j + 1].append(postcode)

        if self._longest_match == len(self.split):
            # Nothing matched.
            queryier.results_cache[results_cache_key] = []
            return []

        if self._longest_match > 0 and not self.allow_dangling:
            queryier.results_cache[results_cache_key] = []
            return []

        # OK, we've now done all the matching, so we can select the best matches and turn them into
        # full results.
        results = self._matches[self._longest_match]

        # Create a new list only having places that match our host country.
        if self.host_country is not None and not self.find_all:
            results[:] = [r for r in results if r.place.country == self.host_country]

        # Find dangling if present
        if self._longest_match > 0:
            dangling = self.qs[:self.split_indices[self._longest_match - 1][1]]
        else:
            dangling = ""

        # Build map of id to Results
        result_map = {m.osm_id: Results.Result(m, dangling) for m in results}

        # Merge results and cache
        merged_places = self._merge_results(result_map)
        total_results = len(merged_places)
        queryier.limit_cache[limit_cache_key] = merged_places, result_map, total_results

        # Sort results
        place_names, postcode_names, sorted_places = self._process_pp(merged_places, result_map, start, limit)
        queryier.results_cache[results_cache_key] = place_names, postcode_names, sorted_places, total_results

        return place_names, postcode_names, sorted_places, total_results

    def _iter_country(self):
        if self.host_country is not None:
            # First of all, we try and do the search as if we're in the host country. This is to
            # catch cases where the name (possibly abbreviated) of an administrative area of the
            # country appears to be the same as another countries name. e.g. California as CA also
            # looks like CA for Canada.

            yield self.host_country, len(self.split) - 1

        # Then see if the user has specified an ISO 2 code of a country name.
        if len(self.split[-1]) == 2:
            iso2_cnd = self.split[-1]
            if iso2_cnd == "uk":
                # As a bizarre special case, the ISO 2 code for the UK is GB, but people might
                # reasonably be expected to specify "UK" so we hack that in.
                iso2_cnd = "gb"

            country = Country.objects.filter(iso3166_2__iexact=iso2_cnd)
            if country.exists():
                yield country[0], len(self.split) - 2

        # Finally try and match a full country name. Note that we're agnostic over the language used to
        # specify the country name.
        sub_hash = _hash_wd(self.split[-1])
        norm_hash = _hash_wd(unidecode(self.split[-1]))
        country_list = PlaceName.objects.prefetch_related('place').filter(Q(name_hash=sub_hash) | Q(name_hash=norm_hash), Q(type__id=get_type_id("country")))

        done = set()
        for cnd in country_list:
            new_i = _match_end_split([unidecode(x) for x in self.split], len(self.split) - 1, unidecode(cnd.name))
            country = cnd.place.country
            done_key = (country, new_i)
            if done_key in done:
                continue

            if new_i is not None:
                yield country, new_i
                done.add(done_key)

        # Apparently none of the above was a good enough match...
        yield None, len(self.split) - 1

    def _iter_places(self, i, country, parent_places=[], postcode=None):

        for j in range(0, i + 1):
            # We will create two hashes, one of the string as it is, and the other of a 'normalised' version of the string.
            # The normalised version will have no accents. The database contains hashes of the normalised version for all roman alphabet-based names.
            sub_hash = _hash_list(self.split[j:i + 1])
            norm_hash = _hash_list([unidecode(x) for x in self.split[j:i + 1]])
            cache_key = (country, sub_hash)
            if cache_key in self.queryier.place_cache:
                place_names = self.queryier.place_cache[cache_key]
            else:
                if country is not None:
                    place_names = PlaceName.objects.prefetch_related('place').filter(Q(name_hash=sub_hash) | Q(name_hash=norm_hash),
                                                                                     place__country=country).distinct('place', 'name')
                else:
                    place_names = PlaceName.objects.prefetch_related('place').filter(Q(name_hash=sub_hash) | Q(name_hash=norm_hash)).distinct('place', 'name')
                self.queryier.place_cache[cache_key] = place_names

            for p in place_names:
                # Don't get caught out by e.g. a capital city having the same name as a state.
                if p.place in parent_places:
                    continue
                if postcode is not None:
                    # We've got a match, but we've also previously matched a postcode.
                    # First of all, try and weed out whether the postcode and the place we've
                    # tentatively matched contradict each other. Ideally we'd like to match
                    # parent IDs and so on; at the moment we can only check that the postcode
                    # and place come from the same country.
                    if postcode.country_id != p.place.country_id:
                        continue

                # Ensure that if there are parent places, then this candidate is a valid child.
                if parent_places and not self._find_parent(parent_places[0], p.place):
                    continue

                new_i = _match_end_split([unidecode(x) for x in self.split], i, unidecode(p.name))
                if not new_i:
                    new_i = _match_end_split([x for x in self.split], i, p.name)
                assert new_i < i
                new_parent_places = [p.place] + parent_places
                record_match = False
                if new_i == -1:
                    record_match = True
                    yield new_parent_places, postcode, new_i
                elif new_i is not None:
                    record_match = True
                    for sub_places, sub_postcode, k in self._iter_places(new_i, p.place.country, new_parent_places, postcode):
                        assert k < new_i
                        record_match = False
                        yield sub_places, sub_postcode, k
                    yield new_parent_places, postcode, new_i
                if record_match and postcode is None:
                    if new_i + 1 > self._longest_match:
                        # Although we've got a potential match, it's got more dangling text than some
                        # previous matches, so there's no point trying to go any further with it.
                        continue

                    # OK, we've got a match; check to see if we've matched it before.
                    done_key = (p.place_id, new_i)
                    if done_key in self._matched_places:
                        continue
                    self._matched_places.add(done_key)

                    self._longest_match = new_i + 1

                    self._matches[new_i + 1].append(Results.RPlace(p.place))

            if postcode is None:
                for sub_postcode, k in self._iter_postcode(i, country):
                    assert k < i
                    if k == -1:
                        done_key = (sub_postcode, k)
                        if done_key in self._matched_postcodes:
                            continue
                        self._matched_postcodes.add(done_key)

                        self._longest_match = 0
                        self._matches[0].append(sub_postcode)
                    else:
                        yield parent_places, sub_postcode, k

                        # Now we need to cope with the fact that "London SW1" is a valid descriptor i.e.
                        # a place can come before a postcode. We therefore need to check the places to
                        # the left of the postcode.

                        for sub_places, sub_sub_postcode, k in self._iter_places(k, country, parent_places, sub_postcode):
                            assert sub_sub_postcode is sub_postcode
                            yield sub_places, sub_sub_postcode, k

    def _iter_postcode(self, i, country):
        uk = UK.COUNTRIES
        us = [Country.objects.get(iso3166_2="US")]
        pc_candidate = self.split[i]

        if country in uk + [None]:
            for sub_postcode, j in UK.postcode_match(self, i):
                yield sub_postcode, j

        if country in us + [None]:
            for sub_postcode, j in US.postcode_match(self, i):
                yield sub_postcode, j

        # In Europe, postcodes are sometimes written as C-NNNN Where C is a country car code and N are digits
        if _RE_EU_ZIP.match(pc_candidate):
            pc_candidate = pc_candidate.split('-')[1]

        if country is not None:
            p = Postcode.objects.prefetch_related('country').only().filter(main__iexact=pc_candidate, country=country)
        else:
            p = Postcode.objects.prefetch_related('country').only().filter(main__iexact=pc_candidate)

        for cnd in p:
            if cnd.country in (uk or us):
                continue

            match = Results.RPost_Code(cnd)
            yield match, i - 1

    def _find_parent(self, find, place):
        """
        Return True if 'find' is a parent of 'place'.
        """
        cache_key = (find, place)
        if cache_key in self.queryier.parent_cache:
            return self.queryier.parent_cache[cache_key]

        if place.parent is None:
            self.queryier.parent_cache[cache_key] = False
            return False
        elif place.parent == find:
            self.queryier.parent_cache[cache_key] = True
            return True
        else:
            r = self._find_parent(find, place.parent)
            self.queryier.parent_cache[cache_key] = r
            return r

    def _merge_results(self, q_res):
        """
        Method takes a dict of osm_id:results produced by the search command.
        It will try and merge LineStrings that are close enough to other LineStrings to be considered part of the same street.
        It will also ignore any duplicate places.
        The method returns a list of merged places.
        """
        ls = {}
        places = []

        for r in q_res.values():
            place = r.ri.place
            if place.location is None:
                continue
                # Find lines and merge (union) them if their distance is close enough to be considered the same location
            if place.location.geom_type in ('LineString', 'MultiLineString'):
                for i, p in ls.items():

                    # We don't want to merge different postcodes
                    if isinstance(r.ri, Results.RPost_Code) and place.sup != p.sup:
                        continue
                    if place.location.distance(p.location) < 0.025:
                        ls[i].location = p.location.union(place.location)
                        break
                else:
                    ls[place.id] = place

            else:
                places.append(place)

        places.extend(ls.values())
        return places

    def _process_pp(self, places, q_res, start, limit):
        """
        Computes the pretty print names for a given list of places.
        Returns a list of sorted places and a dict of place.id's to pretty print place_names
        """
        place_names = {}
        postcode_names = {}
        final_places = []

        # We sort the results here.
        # It would speed up the process if the results were sorted and limited before entering this method; alas the sorting algorithm would not take the
        # newly merged locations into account.
        soraa = self._sort_results(places)
        for p in soraa[start:limit]:
            # Cache locations in order to retrieve them easily onclick in the webview.
            key = str(p.id) + p.__class__.__name__  # we append the result type as a postcode might have the same id as a place
            cache.set(key, p.location.geojson, 99999)

            # Find the pretty print names for the places
            if isinstance(p, Place):
                pp = q_res[p.osm_id].print_pp(self.queryier.pp_place, self.admin_levels)
                place_names[p.id] = pp
                final_places.append(p)
            else:
                pp = q_res[p.osm_id].print_pp(self.queryier.pp_postcode, self.admin_levels)
                if pp not in postcode_names.values():
                    postcode_names[p.id] = pp
                    final_places.append(p)

        return place_names, postcode_names, final_places

    def _sort_results(self, results):
        """
        Generic sorter sorts the results list giving high populations priority.
        Next it sorts in decreasing length size.
        If places are in the host_country, those will be at the top of the list.
        """

        results.sort(
            key=lambda x: (-x.population if isinstance(x, Place) and x.population else 0, -x.location.length if (x.location and x.location.length) else 0))

        # Put results from the host_country first.
        if self.host_country is not None:
            results.sort(key=lambda x: (x.country is None, x.country == self.host_country))

        return results

#
# Cleanup input strings, stripping extraneous spaces etc.
#


def _cleanup(s):
    s = s.strip()
    s = _RE_IRRELEVANT_CHARS.sub(" ", s)
    s = _RE_SQUASH_SPACES.sub(" ", s)

    return s


def _split(s):
    sp = []
    sp_indices = []
    i = 0
    while True:
        m = _RE_SPLIT.search(s, i)
        if m is None:
            break

        sp.append(s[i:m.start()].lower())
        sp_indices.append((i, m.start()))

        i = m.end()

    sp.append(s[i:].lower())

    return sp, sp_indices


def _hash_wd(s):
    return hashlib.md5(s.encode('UTF-8')).hexdigest()


def _hash_list(sL):
    return hashlib.md5(" ".join(sL).encode('UTF-8')).hexdigest()


#
# Given a split name 'split', see if the string 'name' matches the split ending at position i.
# Returns the post-matched position if it succeeds or None if it doesn't. For example:
#
#   _match_end_split(["a", "b", "c", "d", "e"], 3, "c d") == 1
#   _match_end_split(["a", "b", "c", "d", "e"], 3, "a b c") == None
#

def _match_end_split(split, i, name):
    split_name, _ = _split(name)
    if split_name == split[i - len(split_name) + 1: i + 1]:
        return i - len(split_name)

    return None
