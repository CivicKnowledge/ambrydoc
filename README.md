ambrydoc
========

Documentation server and datafile search application

Run with gunicorn: 

    gunicorn ambrydoc:app -b 0.0.0.0:80

gunicorn 19.1.1 seems to be broken, so run with version 18:

    pip install gunicorn==18
