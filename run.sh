#!/bin/bash
# This script was built for starting run the python program using uWSGI

echo Starting...

# uwsgi --http :5009 --gevent 1000 --http-websockets --master --wsgi-file runserver.py --callable app --enable-threads --processes 2 --threads 4
uwsgi --ini uwsgiconfig.ini