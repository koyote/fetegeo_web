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

import re

from geo import Results

from place.models import Postcode, Country


_RE_UK_PARTIAL_POSTCODE = re.compile(
    "^((?:[a-z][0-9])|(?:[a-z][0-9][0-9])|(?:[a-z][0-9][a-z])|(?:[a-z][a-z][0-9])|(?:[a-z][a-z][0-9][0-9])|(?:[a-z][a-z][0-9][a-z]))$",
    re.I)

_RE_UK_FULL_POSTCODE = re.compile(
    "^((?:[a-z][0-9])|(?:[a-z][0-9][0-9])|(?:[a-z][0-9][a-z])|(?:[a-z][a-z][0-9])|(?:[a-z][a-z][0-9][0-9])|(?:[a-z][a-z][0-9][a-z])) *([0-9][a-z][a-z])?$",
    re.I)

# Not all UK postcodes belong to GB (Isle of Man for example)
_UK_CODES = ["GB", "IM", "GY", "JE", "AI", "IO", "FK", "GI", "PN", "GS", "SH", "TC"]
COUNTRIES = [Country.objects.get(iso3166_2=code) for code in _UK_CODES]


def postcode_match(ft, i):
    assert i > -1

    m = _RE_UK_PARTIAL_POSTCODE.match(ft.split[i])
    if m is not None:
        # We got something that looks as if it might plausibly be the solitary first half of a
        # postcode (e.g. AA9A). Lets return everything we can find!

        p = Postcode.objects.filter(country__in=COUNTRIES, main__iexact=ft.split[i])

        for pc in p.all():
            # We might have got multiple matches, in which case we arbitrarily pick the first one.
            match = Results.RPost_Code(pc)
            yield match, i - 1

    if i == 0:
        # If we were at the beginning of the split and nothing above matched, then there's no chance
        # of matching anything hereon in.
        return

    # OK, we're now going to try and match a "full postcode" (e.g. of the form SW1 2AA).
    main = ft.split[i - 1]
    sup = ft.split[i]

    # We now try and match a "full postcode" (e.g. of the form SW1 2AA). Because we only have partial
    # UK postcode data, we first of all try matching exactly what is given, gradually backing off if
    # that isn't possible.
    m = _RE_UK_FULL_POSTCODE.match("{0} {1}".format(main, sup))
    if m is not None:
        p = Postcode.objects.filter(country__in=COUNTRIES, main__iexact=main, sup__iexact=sup)

        for pc in p.all():
            match = Results.RPost_Code(pc)
            yield match, i - 2

        # Couldn't find exact postcode, lets try and find a partial sup for the postcode by reducing sup by one each time.
        if not p.exists():
            i = 1
            while i < 3 and not p.exists():
                p = Postcode.objects.filter(country__in=COUNTRIES, main__iexact=main, sup__istartswith=sup[:i])
                for pc in p.all():
                    match = Results.RPost_Code(pc)
                    yield match, i - 2
                i += 1
        return

    # Only a partial sup was given as a query (SW3 4, for example), so let's try and find all postcodes that match this.
    p = Postcode.objects.filter(country__in=COUNTRIES, main__iexact=main, sup__istartswith=sup)
    for pc in p.all():
        match = Results.RPost_Code(pc)
        yield match, i - 2

    # Now we're struggling - try matching the main part of the postcode and ignore the supplementary
    # part (i.e. we're ignoring the sup part and will just search for the main part)
    if not p.exists():
        p = Postcode.objects.filter(country__in=COUNTRIES, main__iexact=main)

        for pc in p.all():
            match = Results.RPost_Code(pc)
            yield match, i - 2