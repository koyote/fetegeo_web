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


class Result:
    def __init__(self, ri, dangling):
        self.ri = ri
        self.dangling = dangling

    def print_pp(self, pretty_print, admin_levels=[]):
        """
        Return a string that only contains names whose admin levels are found in admin_levels and in order of highest admin level to lowest.
        If admin_levels is empty, return a string of all the names.
        :param admin_levels: list of admin levels to add to the String
        """

        pp = pretty_print(self.ri.place)
        res = [pp[max(pp)]]
        for k in sorted(pp, reverse=True):
            if k != max(pp) and (k in admin_levels or not admin_levels):
                res.append(pp[k])
        return ", ".join(res)


class RPlace:
    def __init__(self, place):
        self.place = place
        self.osm_id = place.osm_id
        self.location = place.location
        self.population = place.population


class RPost_Code:
    def __init__(self, postcode):
        self.place = postcode
        self.location = postcode.location
        self.osm_id = postcode.osm_id
