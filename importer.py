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

import os
import time
import subprocess
import shlex
import argparse
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'fetegeo_web.settings'
from django.db import connection
from django.core.management import call_command


_TABLES = ['type', 'country', 'lang', 'place', 'postcode', 'place_name']
_IMPORT_DIR = os.path.join(os.path.dirname(__file__), 'import/').replace('\\', '/')


class Timer:
    """
    Handy timer class used for timing various methods.
    """

    def __enter__(self):
        self.start = time.time()

    def __exit__(self, *args):
        interval = time.time() - self.start
        if interval < 60:
            print("Time: {:.2f} seconds.".format(interval))
        elif interval < 3600:
            m, s = divmod(interval, 60)
            print("Time: {:.0f} minutes, {:.0f} seconds.".format(m, s))
        else:
            m, s = divmod(interval, 60)
            h, m = divmod(m, 60)
            print("Time: {:.0f} hours, {:.0f} minutes and {:.0f} seconds.".format(h, m, s))


def _import_data(cursor):
    """
    Import the data created by osmosis found in the 'import' dir to postgres.
    """
    for table in _TABLES:
        try:
            with open(_IMPORT_DIR + table + '.txt') as f:
                print("Importing: " + table)
                cursor.copy_from(f, table)
                connection.commit()
        except IOError:
            sys.stderr.write('Could not open import files. Please make sure Osmosis managed to create them properly!\n')
            sys.exit(1)


def _execute_postgis(cursor):
    """
    Run PostGIS commands on the databse for cleaning up geometry objects and calculating relationships
    between different locations.
    """
    try:
        with open(_IMPORT_DIR + 'impdjango.sql') as f:
            query = comment = ''
            for line in f:
                if line.startswith("--"):
                    comment = line.replace("--", "").strip()
                    if 'Vacuum Analyse' in comment:
                        _vacuum_analyze(cursor)
                    continue

                query += line

                if ";" in line:
                    print(comment)
                    with Timer():
                        cursor.execute(query)
                        connection.commit()

                    query = ''

    except IOError:
        sys.stderr.write('Could not open impdjango.sql. Please make sure it can be found in ' + _IMPORT_DIR + '\n')
        sys.exit(1)


def _vacuum_analyze(cursor):
    """
    Vacuum analyze needs to be run from a different isolation level.
    """
    print('Vacuum Analyze')
    with Timer():
        old_iso_level = connection.connection.isolation_level
        connection.connection.set_isolation_level(0)
        cursor.execute('VACUUM ANALYZE')
        connection.commit()
        connection.connection.set_isolation_level(old_iso_level)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--osm-file', type=str, help='Specify an OSM file to process with osmosis. (.pbf highly preferred!)')
    args = parser.parse_args()

    # Osmosis
    if not args.osm_file:
        print("No OSM file specified. Add one with the -f command.")
    else:
        if args.osm_file.endswith(('.bz2', '.osm')):
            read = '--fast-read-xml'
        elif args.osm_file.endswith('.pbf'):
            read = '--read-pbf-fast'
        else:
            sys.stderr.write("Osmosis file must be in bz2, xml or pbg format.\n")
            sys.exit(1)

        osmosis_command = shlex.split('osmosis {read} file={file} --fimp outdir={outdir}'.format(read=read, file=args.osm_file, outdir=_IMPORT_DIR))
        subprocess.check_output(osmosis_command)

    # Psql import
    with Timer():
        call_command('syncdb', interactive=False)  # Create DB _TABLES if they don't exist already.
        call_command('flush', interactive=False)  # Delete all data if there was data.
        cursor = connection.cursor()

        print("\nImporting data...")
        _import_data(cursor)
        print("\nExecuting PostGIS statments...")
        _execute_postgis(cursor)
        _vacuum_analyze(cursor)
