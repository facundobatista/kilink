Linkode
=======

Linkode is the useful pastebin! 

It's a kind of "short living collaboration space", a "dynamic pastebin".

It's live right now in **http://linkode.org/**, give it a try!

Some awesome detailes:

    - you can create linkodes anywhere, whenever, and effortesly.
    - editable texts, not static!
    - every new edition creates a child: you have a tree
    - code/text type autodetection (and coloring!)
    - permantent linkodes (but still the owner can remove them)
    - absolutely anonymous (unless you login, which is dead simple)
    - private URLs: because you can not guess UUIDs


Collaboration
-------------

Code and issues is in GitHub:

    https://github.com/facundobatista/kilink

We also have a mailing list:

    http://listas.python.org.ar/mailman/listinfo/kilink

And you can also get help by IRC, in Freenode: #linkode


The API
-------

Get the API details from the HTML file::

    kilink/templates/_tools.html

In a future this will be in a Doc file (source of that HTML).


How To Try It In Development
----------------------------

    $ virtualenv linkode
    $ cd linkode
    $ git clone https://github.com/facundobatista/linkode.git
    $ source bin/activate
    $ pip install -r requirements.txt
    $ ./test
    $ ./run


How to traslate
---------------

Extract the traslations text

    pybabel extract -F babel.cfg -o messages.pot translations


Generate a language catalog

    pybabel init -i messages.pot -d translations -l it


The command create a .po file in the directory especified by "-d"

    translations/it/LC_MESSAGES/messages.po

You edit this messages.po file and then compile

    pybabel compile -d translations


If you add new text, you need to wrapp it with "_" function

In templates:

    <span>{{ _("Text to traslate") }}</span>

In python files:

    from flask.ext.base import gettext as _

    def views():
        flash( _("Text to traslate") )

Updating translations

    pybabel extract -F babel.cfg -o messages.pot translations


Add the language code to available languages in the config.py file

    LANGUAGES = {
        …
        'it': 'Italian',
        …
    }

[Flask-Babel Tutorial](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n)

How To Deploy With Apache
-------------------------

Documentation based in http://flask.pocoo.org/docs/deploying/mod_wsgi/

We use a virtualenv to deploy the project and apache virtual host on Ubuntu
13.04, This configuration es very general, I guess that works in almost all
linux OS

Definitions:

 - **Project path:** */var/linkode_home/*
 - **Application path:** */var/linkode_home/linkode_app*
 - **VirtualEnv Path:** */var/linkode_home/linkode_virtualenv*
 - **User:** *www-data*

Create virtualenv and install the requirements:

    $ cd /var/linkode_home
    $ virtualenv linkode_virtualenv
    $ cd linkode_virtualenv
    $ source bin/activate
    $ pip install -r requirements.txt

Clone repository:
    
    $ cd /var/linkode_home/
    $ git clone https://github.com/facundobatista/linkode.git linkode_app
    $ cd linkode_app
    
The WSGI configuration file is already in the project, ready to use; for develop 
or debuging you can add to it:

    application.debug = True
    
    # Needs install paste via pip "pip install paste"
    # For More information:
    # http://code.google.com/p/modwsgi/wiki/DebuggingTechniques#Browser_Based_Debugger
    from paste.evalexception.middleware import EvalException
    application = EvalException(application)


Create a virtual host configuration file in /etc/apache2/sites-enabled/
with the name that you want, in this example "linkode"
    
    # vi /etc/apache2/sites-enabled/linkode

And paste this:

    <VirtualHost *>
        ServerName linkode.mydomain
    
        WSGIDaemonProcess linkode user=www-data group=www-data threads=5
        WSGIScriptAlias / /var/linkode_home/linkode.wsgi
        WSGIScriptReloading On
    
        <Directory /var/linkode_home/linkode_app/linkode/>
            WSGIProcessGroup linkode
            WSGIApplicationGroup %{GLOBAL}
            Order deny,allow
            Allow from all
        </Directory>
    
        AddDefaultCharset utf-8
        ServerSignature On
        LogLevel info
        
        ErrorLog  /var/log/apache2/linkode-error.log
        CustomLog /var/log/apache2/linkode-access.log combined
    
    </VirtualHost>
    
Restart Apache and Enjoy!


Clients
-------

- **GUI**, Graphical/Grafico: https://github.com/juancarlospaco/linkode-gui#linkode-gui
- **CLI**, Command Line/Linea de Comando: https://github.com/humitos/linkodeit#linkodeit
