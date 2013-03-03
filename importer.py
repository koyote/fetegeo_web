from django.core import management
from django.core.management import call_command
import fetegeo_web.settings as settings
import os
import time
import subprocess
import shlex
import argparse
management.setup_environ(settings)
from django.db import connection


_TABLES = ['type', 'country', 'lang', 'place', 'postcode', 'place_name']
_IMPORT_DIR = os.path.join(os.path.dirname(__file__), 'import/').replace('\\', '/')

class Timer:    
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
    for table in _TABLES:
        with open(_IMPORT_DIR + table + '.txt') as f:
            print("Importing: " + table)
            cursor.copy_from(f, table)
            connection.commit()
            
def _execute_postgis(cursor):
    with open(_IMPORT_DIR + 'impdjango.sql') as f:
        query = ''
        comment = ''
        for line in f:
            if line.startswith("--"):
                comment = line.replace("--", "")
                continue
            
            query += line
            
            if ";" in line:
                print(comment.strip()) 
                with Timer():
                    cursor.execute(query)
                    connection.commit()
                query = comment = ''

def _vacuum_analyze(cursor):
    old_iso_level = connection.connection.isolation_level
    connection.connection.set_isolation_level(0)
    cursor.execute('VACUUM ANALYZE')
    connection.commit()
    connection.connection.set_isolation_level(old_iso_level)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--osm-file', type=str, help='Specify an OSM file to process with osmosis.')
    args = parser.parse_args()
       
    if not args.osm_file:
        print("No OSM file mentioned. Add one with the -f command.")
    else:
        osmosis_command = shlex.split('osmosis --fast-read-xml file="' + args.osm_file + '" --fimp outdir=' + _IMPORT_DIR)
        subprocess.check_output(osmosis_command)

    with Timer():
        call_command('syncdb', interactive=False)  # Create DB _TABLES if they don't exist already.
        call_command('flush', interactive=False)  # Delete all data if there was data.
        cursor = connection.cursor()
        
        print("\nImporting data...")
        _import_data(cursor)
        
        print("\nExecuting PostGIS statments...")
        _execute_postgis(cursor)
        
        print('\nVACUUM ANALYZE')
        _vacuum_analyze(cursor)
