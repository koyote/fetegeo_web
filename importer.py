from django.core import management
from django.core.management import call_command
import fetegeo_web.settings as settings
import os
import time
import subprocess
import shlex
import getopt
import sys
management.setup_environ(settings)
from django.db import connection


_TABLES = ['type', 'country', 'lang', 'place', 'postcode', 'place_name']
_IMPORT_DIR = os.path.join(os.path.dirname(__file__), 'import/').replace('\\', '/')

class Timer:    
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start
        

def open_file(txt):
    return open(_IMPORT_DIR+txt)

def import_data(cursor):
    for table in _TABLES:
        with open_file(table + '.txt') as f:
            print("Importing data for: " + table)
            cursor.copy_from(f, table)
            connection.commit()
            
def execute_postgis(cursor):
    with open_file('impdjango.sql') as f:
        print("Executing PostGIS statments...")
        query = ''
        comment = ''
        for line in f:
            if line.startswith("--"):
                comment = line.replace("--", "")
                continue
            
            query += line
            
            if ";" in line:
                print("Executing: " + comment.strip()) 
                with Timer() as t:
                    cursor.execute(query)
                print("Time: %.03f seconds.\n" % t.interval)
                query = comment = ''

def vacuum_analyze(cursor):
    old_iso_level = connection.connection.isolation_level
    connection.connection.set_isolation_level(0)
    print('Executing: VACUUM ANALYZE')
    cursor.execute('VACUUM ANALYZE')
    connection.connection.set_isolation_level(old_iso_level)
    
def usage(error):
    print(error)
    
if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:')
    except getopt.error as e:
        usage(str(e))
    osm_file = ''    
    for opt, arg in opts:
        if opt == '-f':
            osm_file = arg
    
    if not osm_file:
        usage("No file")
    else:
        osmosis_command = shlex.split('osmosis --fast-read-xml file="' + osm_file + '" --fimp outdir=' + _IMPORT_DIR)
        subprocess.check_output(osmosis_command)

    with Timer() as t:
        call_command('syncdb', interactive=False)  # Create DB _TABLES if they don't exist already.
        call_command('flush', interactive=False)  # Delete all data if there was data.
        cursor = connection.cursor()
        
        import_data(cursor)
        execute_postgis(cursor)
        vacuum_analyze(cursor)
    print("Total Time: %.03f seconds." % t.interval)
