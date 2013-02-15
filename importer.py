from django.core import management
from django.core.management import call_command
import fetegeo_web.settings as settings
import os
import time
management.setup_environ(settings)
from django.db import connection


tables = ['type', 'country', 'lang', 'place', 'postcode', 'place_name']

class Timer:    
    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

def open_file(txt):
    return open(os.path.join(os.path.dirname(__file__), 'import/' + txt).replace('\\', '/'))

def import_data(cursor):
    for table in tables:
        with open_file(table + '.txt') as f:
            print("Importing data for: " + table)
            cursor.copy_from(f, table)
            connection.commit()
            
def execute_postgis(cursor):
    with open_file('impdjango.sql') as f:
        print("Executing PostGIS statments...")
        query = ''
        for line in f:
            query += line
            if ";" in line:
                print("Executing: " + query) 
                with Timer() as t:
                    cursor.execute(query)
                print("Time: %.03f seconds" % t.interval)
                query = ''

def vacuum_analyze(cursor):
    old_iso_level = connection.connection.isolation_level
    connection.connection.set_isolation_level(0)
    print('Executing VACUUM ANALYZE')
    cursor.execute('VACUUM ANALYZE')
    connection.connection.set_isolation_level(old_iso_level)
    
if __name__ == "__main__":
    with Timer() as t:
        call_command('syncdb', interactive=False)  # Create DB tables if they don't exist already.
        call_command('flush', interactive=False)  # Delete all data if there was data.
        cursor = connection.cursor()
        
        import_data(cursor)
        execute_postgis(cursor)
        vacuum_analyze(cursor)
    print("Total Time: %.03f minutes" % t.interval/60.0)
