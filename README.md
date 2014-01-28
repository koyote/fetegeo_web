fetegeo_web
=============

fetegeo_web is an almost complete rewrite of the [Fetegeo open-source geocoding framework](https://github.com/ltratt/fetegeo).
It was built to handle data from the OpenStreetMap project instead of the existing GeoNames data Fetegeo currently supports.
This enables Fetegeo to handle a much vaster dataset including street names, postcodes and geometric representations of all locations.

This new Fetegeo relies on Django and its ORM for all queries sent to the database resulting in a much more portable and database-agnostic code. 
Fetegeo's old socket-based API has also been rewritten in order to support RESTFul queries dynamically returning results in either JSON or XML.
At the moment the excellent Django plugin [Django REST framework](http://django-rest-framework.org/) has been used to achieve this.

On the client side the Fetegeo command line client (fetegeoc) has been completely rewritten to support the new HTTP-based API.
An additional web client running on Django has also been created. This uses [OpenLayers](http://openlayers.org/) to display search results on a map.

A working Demo can (sometimes) be found at [Fetegeo Webview](http://www.pitapps.com).


##Requirements:
 - Python 3+
 - everything in requirements.txt
 - [FetegeoImport plugin for Osmosis](https://github.com/koyote/FetegeoImport)
 - PostgreSQL 9.2+, PostGIS 2.0+

##Installation
- After setting up PostgreSQL and PostGIS, create a new database and install the PostGIS extension with the folliwng command
```
CREATE EXTENSION postgis;
```

- Use pip to install all of the requirements (this can be done in a virtualenv if wanted):
```
pip install -r requirements.txt
```

- Edit ```fetegeo_web/settings.py``` and set your database username, password and the name of the database created above.
  It is also important that you change the SECRET_KEY if you plan on running the webserver in production.

- Populate the database with data retrieved from the OpenStreetMap project by running the importer python script:
```
python importer.py -f file_to_be_imported.osm.pbf
```
  The processed PostgreSQL import files can be found in ```import/```.
  If the Osmosis task has already been run, the database import script can be run without arguments to do a simple database import from the files inside ```import/```.
  ###WARNING
  The importer might take hours on a large dataset due to the database postprocessing commands.
- Finally, the Django webview uses an API called [Pygeoip](http://appliedsec.github.com/pygeoip/) which is used to determine the home country of a visitor. This library is based on the MaxMind API and requires the MaxMind dataset. As such GeoLiteCity.dat should be downloaded from [here](http://dev.maxmind.com/geoip/geolite) and placed into ```place/geoip/```.

##Usage
fetegeo_web can be started like any other Django application, either locally with ```python manage.py runserver``` or using WSGI plugins and a webserver like Apache or Nginx.


##Licence
    Copyright (C) 2013 Pit Apps
  
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation 
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, 
    and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all copies or substantial portions 
    of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED 
    TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL 
    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
    CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
    IN THE SOFTWARE.
