#!/usr/bin/env python3

"""
 Copyright (C) 2013 Pit Apps

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

from urllib.parse import urlencode, quote
import argparse
import json
import sys
import textwrap

import httplib2


_VERSION = "0.3"

_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000
_DEFAULT_LANG = ["EN"]  # English

_DESCRIPTION = 'Fetegeo Geocoder ' + _VERSION
_QUERY_HELP = 'An address or part of an address you want to conduct a search on.'
_A_HELP = 'Find only matches in the host country.'
_L_HELP = 'Specify the preferred language(s) for results to be returned in. Multiple -l options can be specified; they will be treated in descending order of preference.'
_SA_HELP = 'If enabled it will print out the whole area as opposed to only the centroid.'
_D_HELP = 'If enabled the search will discard the left parts of the query that did not match.'
_C_HELP = 'Search only for places in the specified country (ISO code).'


class Fetegeoc:
    def __init__(self):
        self._conn = httplib2.Http('.cache')
        self._parse_args()

    def _parse_args(self):
        """
        Argument parser using argparse library.
        Automatically calls the function attached to the specified command.
        """

        # Main Parser
        parser = argparse.ArgumentParser(description=_DESCRIPTION, prog='Fetegeo')
        parser.add_argument('--version', action='version', version='%(prog)s ' + _VERSION)
        parser.add_argument('-s', '--host', type=str, help='Host', default=_DEFAULT_HOST)
        parser.add_argument('-p', '--port', type=str, help='Port', default=_DEFAULT_PORT)
        parser.add_argument('-l', '--lang', action='append', help=_L_HELP)
        subparsers = parser.add_subparsers()

        # Query parser used as parent by subparsers
        query_parser = argparse.ArgumentParser(add_help=False)
        query_parser.add_argument('qs', metavar='Query', nargs='+', help=_QUERY_HELP)

        # Parser for 'country'
        parser_ctry = subparsers.add_parser('country', help='Country Query', parents=[query_parser])
        parser_ctry.set_defaults(func=self._q_ctry)

        # Parser for 'geo'
        parser_geo = subparsers.add_parser('geo', help='Geo Query', parents=[query_parser])
        parser_geo.add_argument('-a', '--find-all', action='store_false', help=_A_HELP)
        parser_geo.add_argument('--fl', '--full-location', action='store_true', help=_SA_HELP)
        parser_geo.add_argument('-d', '--allow-dangling', action='store_true', help=_D_HELP)
        parser_geo.add_argument('-c', '--country', type=str, help=_C_HELP)
        parser_geo.set_defaults(func=self._q_geo)

        args = parser.parse_args()
        if not args.lang:  # roundabout way for circumventing bug in argsparse that adds _DEFAULT_LANG to lang even when it's been set
            args.lang = _DEFAULT_LANG

        try:  # it would be nice to know how to set subparsers to be required
            args.func(args)
        except AttributeError:
            sys.stderr.write("Error: Please specify a query mode ('geo', 'country').\n\n")
            print(parser.format_help())

    def _pp_geo(self, data):
        """
        Pretty prints results from a 'geo' query.
        """

        self._handle_error(data)

        i = 1
        for result in data:
            if i != 1:
                print()
            print("Match #{}".format(i))
            self._print_wrap("{0}: {1}\n".format("Pretty Print", result["pp"]))
            self._print_wrap("{0}: {1}\n".format("OSM ID", result["osm_id"]))
            self._print_wrap("{0}: {1}\n".format("Location Type", result["location"][0]["type"]))
            self._print_wrap("{0}: {1}\n".format("Location Coordinates", result["location"][1]["coordinates"]))
            population = result["population"]
            if population:
                self._print_wrap("{0}: {1}".format("Population", population))
            i += 1

    def _pp_ctry(self, data):
        """
        Pretty prints results from a 'country' query.
        """

        self._handle_error(data)

        print("Match:")
        self._print_wrap("{0}: {1}\n".format("Query", data["query"]))
        self._print_wrap("{0}: {1}\n".format("Name", data["result"]))
        lang = data["lang"]
        if lang:
            self._print_wrap("{0}: {1}\n".format("Language", lang))

    def _print_wrap(self, text):
        """
        Uses textwrap to make sure wrapped lines are indented (useful for long location lists).
        """

        print(textwrap.fill(text, initial_indent=' ', subsequent_indent='     '))

    def _handle_error(self, data):
        if 'error' in data:
            print("No match found for {}.".format(data["query"]))
            sys.exit(0)

    def _handle_status(self, status):
        if status != 200:
            if status == 404:
                sys.stderr.write("404. Check your config host name and port.\n")
                sys.exit(1)
            elif status == 500:
                sys.stderr.write("Server error. Please try again later.\n")
                sys.exit(1)
            sys.stderr.write("Error: " + str(status) + "\n")
            sys.exit(1)

    def _q_geo(self, args):
        """
        Geo command that calls the JSON API using the specified options.
        """

        query = quote(" ".join(args.qs))
        options = dict(find_all=args.find_all, dangling=args.allow_dangling, langs=args.lang, show_all=args.fl, country=args.country)
        url = 'http://{host}:{port}/api/geo/{query}.json'.format(host=args.host, port=args.port, query=query)
        response, content = self._conn.request(url, 'POST', urlencode(options), {'Content-type': 'application/x-www-form-urlencoded'})

        self._handle_status(response.status)
        data = json.loads(content.decode('utf-8'))

        self._pp_geo(data)

    def _q_ctry(self, args):
        """
        Country command that calls the JSON API using the specified options.
        """

        query = quote(" ".join(args.qs))
        options = dict(langs=args.lang)
        url = 'http://{host}:{port}/api/ctry/{query}.json'.format(host=args.host, port=args.port, query=query)
        response, content = self._conn.request(url, 'POST', urlencode(options), {'Content-type': 'application/x-www-form-urlencoded'})

        self._handle_status(response.status)
        data = json.loads(content.decode('utf-8'))

        self._pp_ctry(data)


if __name__ == "__main__":
    Fetegeoc()

