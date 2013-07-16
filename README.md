Kilink
======

The useful pastebin!

This is a pastebin with a lot of fascinating features:

  - FIXME


The API
-------

This is the version 1 of the API.

To create a new kilink:

    - type: POST
    - url: /api/1/kilinks/
    - data: content=<content>

To create a child of an existing kilink node:

    - type: POST
    - url: /api/1/kilinks/<kid>
    - data: content=<content>&parent=<parentrevno>

To get a specific kilink node:

    - type: GET
    - url: /api/1/kilinks/<kid>/<revno>

To get all the tree of a kilink:

    - type: GET
    - url: /api/1/kilinks/<kid>

As we don't know if the "get all the tree of a kilink" it's going to be used,
it's not implemented yet. But will have the previous API ;-)


How To Try It In Development
----------------------------

    $ virtualenv kilink
    $ cd kilink
    $ git clone https://github.com/facundobatista/kilink.git
    $ source bin/activate
    $ pip install -r requirements.txt
    $ ./test
    $ ./run

How To Deploy With Apache
-------------------------

Documentation based in http://flask.pocoo.org/docs/deploying/mod_wsgi/

We use a virtualenv to deploy the project and apache virtual host on Ubuntu
13.04, This configuration es very general, I guess that works in almost all
linux OS

Definitions:

 - **Project path:** */var/kilink_home/*
 - **Application path:** */var/kilink_home/kilink_app*
 - **VirtualEnv Path:** */var/kilink_home/kilink_virtualenv*
 - **User:** *www-data*

Create virtualenv and install the requirements:

    $ cd /var/kilink_home
    $ virtualenv kilink_virtualenv
    $ cd kilink_virtualenv
    $ source bin/activate
    $ pip install -r requirements.txt

Clone repository:
    
    $ cd /var/kilink_home/
    $ git clone https://github.com/facundobatista/kilink.git kilink_app
    $ cd kilink_app
    
Create WSGI configuration file
    
    $ vi /var/kilink_home/kilink_app/kilink/kilink.wsgi

And paste this:
    
    activate_this = '/var/kilink_home/kilink_virtualenv/bin/activate_this.py'
    execfile(activate_this, dict(__file__=activate_this))
    
    
    from kilink import app as application


Create a virtual host configuration file in /etc/apache2/sites-enabled/
with the name that you want, in this example "kilink"
    
    # vi /etc/apache2/sites-enabled/kilink

And paste this:

    <VirtualHost *>
        ServerName kilink.mydomain
    
        WSGIDaemonProcess kilink user=www-data group=www-data threads=5 python-path=/var/kilink_home/kilink_virtualen/lib/python2.7/site-packages/:/var/kilink_home/kilink_app/kilink/
        WSGIScriptAlias / /var/kilink_home/kilink_app/kilink/kilink.wsgi
        WSGIScriptReloading On
    
        <Directory /var/kilink_home/kilink_app/kilink/>
            WSGIProcessGroup kilink
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>
    
        AddDefaultCharset utf-8
        ServerSignature On
        LogLevel info
        
        ErrorLog  /var/log/apache2/kilink-error.log
        CustomLog /var/log/apache2/kilink-access.log combined
    
    </VirtualHost>
    
Restart Apache and Enjoy!

