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
import json


class Result:
    def __init__(self, ri, dangling):
        self.ri = ri
        self.dangling = dangling


    def to_xml(self):
        return ("<result>"
                "{0}"
                "<dangling>{1}</dangling>"
                "</result>"
            ).format(self.ri.to_xml(), self.dangling)


class RCountry:
    def __init__(self, country, pp):
        self.id = country.id
        self.name = country.name
        self.pp = pp


    def to_xml(self):
        return ("<country>"
                "<id>{id}</id>"
                "<name>{name}</name>"
                "<pp>{pp}</pp>"
                "</country>"
            ).format(id=self.id, name=self.name, pp=self.pp)


class RPlace:
    def __init__(self, place, pp):
        self.place = place
        self.pp = pp


    def to_json(self):
        data = {'osm_id':self.place.osm_id, 'population':self.place.population, 'pp':self.pp, 'location':self.place.location}
        return json.dumps(data)
        
        
    def to_xml(self):

        if self.population is not None:
            population_txt = "<population>{0}</population>".format(self.place.population)
        else:
            population_txt = ""

        return ("<place>"
                "<id>{id}</id>"
                "<osm_id>{osm_id}</osm_id>"
                "<location>{location}</location>"
                "{population}"
                "<pp>{pp}</pp>"
                "</place>"
            ).format(id=self.place.id, osm_id=self.place.osm_id, location=self.place.location, population=population_txt, pp=self.pp)


class RPost_Code:
    def __init__(self, postcode, pp):
        self.postcode = postcode
        self.pp = pp

    
    def to_json(self):
        data = {'osm_id':self.postcode.osm_id, 'pp':self.pp, 'location':self.postcode.location}
        return json.dumps(data)

    def to_xml(self):
        return ("<postcode>"
                "<id>{id}</id>"
                "<osm_id>{osm_id}</osm_id>"
                "<location>{location}</location>"
                "<pp>{pp}</pp>"
                "</postcode>"
            ).format(id=self.postcode.id, location=self.postcode.location, pp=self.postcode.pp, osm_id=self.postcode.osm_id)
