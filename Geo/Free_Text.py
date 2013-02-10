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

import re, hashlib
from .import Results, UK, US
from place.models import PlaceName, Country, Postcode, get_place_name, get_type


_RE_IRRELEVANT_CHARS = re.compile("[,\\n\\r\\t;()]")
_RE_SQUASH_SPACES = re.compile(" +")
_RE_SPLIT = re.compile("[ ,/]")


class Free_Text:
    def name_to_lat_long(self, queryier, langs, find_all, allow_dangling, show_area, qs, host_country):
        self.queryier = queryier
        self.langs = langs
        self.find_all = find_all
        self.allow_dangling = allow_dangling
        self.show_area = show_area
        self.qs = _cleanup(qs)
        self.split, self.split_indices = _split(self.qs)
        self.host_country = host_country
        self.country_type = get_type("country")
        
        results_cache_key = (tuple(langs), find_all, allow_dangling, show_area, self.qs, host_country)
        if queryier.results_cache.has_key(results_cache_key):
            return queryier.results_cache[results_cache_key]

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
        self._matched_postcodes = set() # Analagous to _matched_places.

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
                    done_key = (postcode.id, j)
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

        if self.host_country is not None and not self.find_all:
            # If we're only trying to find matches within a given country, then remove any
            # matches that come from other countries. This may seem inefficient, but it's
            # easier than having this logic every bit of code that adds matches.
            i = 0
            while i < len(results):
                if results[i].country_id != self.host_country.id:
                    del results[i]
                else:
                    i += 1

        print([p.pp for p in results])
        # Sort the results into alphabetical order.
        results.sort(key=lambda x: x.pp)

        # Now we try to find the best match.

        found_best = False
        if self.host_country is not None:
            # If a host country is specified, we first of all find the best match within the country.
            # If there are no results at all within the country then the generic best finder below
            # will kick into action.
            best_i = None
            for i in range(len(results)):
                if results[i].country_id == self.host_country.id:
                    if best_i is None:
                        best_i = i
                    elif isinstance(results[best_i], Results.RPlace) and\
                         isinstance(results[i], Results.RPlace):
                        if not results[best_i].population and results[i].population:
                            best_i = i
                        elif results[best_i].population and results[i].population:
                            if results[best_i].population < results[i].population:
                                best_i = i
                    elif isinstance(results[best_i], Results.RPost_Code) and\
                         isinstance(results[i], Results.RPlace):
                        best_i = i
                    elif isinstance(results[best_i], Results.RPost_Code) and\
                         isinstance(results[i], Results.RPost_Code):
                        pass

            if best_i is not None:
                best = results[best_i]
                del results[best_i]
                results.insert(0, best)
                found_best = True

        if not found_best:
            # Generic 'best finder'.
            best_i = None
            for i in range(len(results)):
                if best_i is None:
                    best_i = i
                elif isinstance(results[best_i], Results.RPlace) and\
                     isinstance(results[i], Results.RPlace):
                    if not results[best_i].population and results[i].population:
                        best_i = i
                    elif results[best_i].population and results[i].population:
                        if results[best_i].population < results[i].population:
                            best_i = i
                elif isinstance(results[best_i], Results.RPost_Code) and\
                     isinstance(results[i], Results.RPlace):
                    best_i = i
                elif isinstance(results[best_i], Results.RPost_Code) and\
                     isinstance(results[i], Results.RPost_Code):
                    pass

            if best_i is not None:
                best = results[best_i]
                del results[best_i]
                results.insert(0, best)

        if self._longest_match > 0:
            dangling = self.qs[:self.split_indices[self._longest_match - 1][1]]
        else:
            dangling = ""

        final_results = [Results.Result(m, dangling) for m in results]
        
        queryier.results_cache[results_cache_key] = final_results

        return final_results


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
            if country.count() > 0:
                country = country[0]
                yield country, len(self.split) - 2


        # Finally try and match a full country name. Note that we're agnostic over the language used to
        # specify the country name.

        country_list = PlaceName.objects.filter(type=self.country_type, name_hash=_hash_wd(self.split[-1]))

        done = set()
        for cnd in country_list.all():
            new_i = _match_end_split(self.split, len(self.split) - 1, cnd.name)
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
            sub_hash = _hash_list(self.split[j:i + 1])
            print("Sub_hash " + str(self.split[j:i + 1]) + ": " + sub_hash)
            cache_key = (country, sub_hash, self.show_area)
            if self.queryier.place_cache.has_key(cache_key):
                place_names = self.queryier.place_cache[cache_key]
            else:
                if country is not None:
                    place_names = PlaceName.objects.filter(name_hash=sub_hash, place__country=country).distinct('place','name')
                else:
                    place_names = PlaceName.objects.filter(name_hash=sub_hash).distinct('place','name')
     
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
                    if postcode.country != p.place.country:
                        continue

                # Ensure that if there are parent places, then this candidate is a valid child.
                if len(parent_places) > 0 and not self._find_parent(parent_places[0], p.place):
                    continue

                new_i = _match_end_split(self.split, i, p.name)
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
                    done_key = (p.place, new_i)
                    if done_key in self._matched_places:
                        continue
                    self._matched_places.add(done_key)

                    local_name = get_place_name(p.place, self.langs)

                    pp = self.queryier.pp_place(self, p.place)

                    self._longest_match = new_i + 1

                    self._matches[new_i + 1].append(Results.RPlace(p.place, local_name, pp))

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


    #
    # Return True if 'find_id' is a parent of 'place_id'.
    #

    def _find_parent(self, find, place):
        cache_key = (find, place)
        if self.queryier.parent_cache.has_key(cache_key):
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


    def _iter_postcode(self, i, country):  
        uk = [Country.objects.get(iso3166_2=code) for code in UK._UK_CODES]
        us = [Country.objects.get(iso3166_2="US")]

        if country in uk:
            for sub_postcode, j in UK.postcode_match(self, i):
                yield sub_postcode, j

        if country in us:
            for sub_postcode, j in US.postcode_match(self, i):
                yield sub_postcode, j


        if country is not None:
            p = Postcode.objects.filter(main__iexact=self.split[i], country=country)
        else:
            p = Postcode.objects.filter(main__iexact=self.split[i])

        for cnd in p.all():

            if cnd.country in uk or cnd.country == us:
                # We search for UK/US postcodes elsewhere.
                continue

            # Search for a parent place
            parent = cnd.parent

            if parent:
                pp = "{0}, {1}".format(cnd.main, self.queryier.pp_place(self, parent))

            match = Results.RPost_Code(cnd, pp)
            yield match, i - 1

        if country in uk:
            for sub_postcode, j in UK.postcode_match(self, i):
                yield sub_postcode, j

        if country in us:
            for sub_postcode, j in US.postcode_match(self, i):
                yield sub_postcode, j


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
