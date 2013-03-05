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


from geo import Results
from place.models import Postcode, Country
import re

_RE_US_ZIP = re.compile("^[0-9]{5}$")
_RE_US_ZIP_PLUS4 = re.compile("^[0-9]{5}-[0-9]{4}$")


def postcode_match(ft, i):
    for match, new_i in _sub_pc_match(ft, i):
        yield match, new_i


def _sub_pc_match(ft, i):
    us = Country.objects.get(iso3166_2="US")
    if _RE_US_ZIP_PLUS4.match(ft.split[i]):
        main, sup = ft.split[i].split('-')
    elif _RE_US_ZIP.match(ft.split[i]):
        main, sup = ft.split[i], None
    else:
        return

    if sup is not None:
        p = Postcode.objects.filter(main__iexact=main, sup__iexact=sup, country=us)
    if sup is None or not p:
        p = Postcode.objects.filter(main__iexact=main, country=us)

    for cnd in p.all():

        match = Results.RPost_Code(ft, cnd)
        yield match, i - 1
