
#!/bin/bash
APP_ROOT=/home/victor/coding/projects/iotoro-web
APP_ENV=/home/victor/coding/projects/iotoro-web/iotoro

cd /home/victor/coding/projects/iotoro-web
source env/bin/activate

cd /home/victor/coding/projects/iotoro-web/iotoro_web
python manage.py livereload & python manage.py runserver

