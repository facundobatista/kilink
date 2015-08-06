Kilink
======

Linkode is the useful pastebin!

It's a kind of "short living collaboration space", a "dynamic pastebin".

It's live right now in **http://linkode.org/**, give it a try!

Some awesome details:

* you can create linkodes anywhere, whenever, and effortlessly.
* editable texts, not static!
* every new edition creates a child: you have a tree
* code/text type automatic detection (and coloring!)
* permanent linkodes (the owner can still remove them)
* absolutely anonymous (unless you login, which is dead simple)
* private URLs: because you can not guess UUIDs


Collaboration
-------------

Code and issues is in GitHub:

`https://github.com/facundobatista/kilink`

We also have a mailing list:

`http://listas.python.org.ar/mailman/listinfo/kilink`

And you can also get help by IRC, in Freenode: #linkode


The API
-------

Get the API details from the HTML file::

`kilink/templates/_tools.html`

In a future this will be in a Doc file (source of that HTML).


How To Try It In Development
----------------------------

```bash
virtualenv kilink
cd kilink
git clone https://github.com/facundobatista/kilink.git
source bin/activate
pip install -r requirements.txt
cp configs/{development,active}.yaml
./test
./run
```

Customization
-------------

The file `active.yaml` inside the `config/` folder is the entry point for
configuration customization. It's not versioned, so you will have to create it
after installing the site (it's omitted from the repo).

This file can extend another yaml file by adding to it (preferably at the top):
```
extends: some-other-file.yaml
```
The files `development.yaml` and
`production.yaml` are examples your active.yaml can copy or actually extend.
In turn, both files extend `base.html`.

Configuration files are interpolated, so you can refer to some other setting
(whether it is defined in your file or in any file in the extend chain) using
Jinja syntax, e.g.:

    db_name: kilink
    db_engine: sqlite:///tmp/{{ db_name }}.db

In fact, if you are extending `production.yaml` make sure your `active.yaml`
file includes your database's real user and password.


How to Translate
----------------

When including translatable text in the code, make sure to always wrap it in the
`gettext` function. Within templates it's already available and bound to `_`,
e.g.:

`<span>{{ _("Text to translate") }}</span>`

In Python files you need to import it from Flask, e.g.:
```python
from flask.ext.base import gettext as _

def views():
    flash( _("Text to translate") )
```

Later, to produce language catalogs:

1. Extract the translation texts:

   ```
   cd kilink
   pybabel extract -F babel.cfg -o messages.pot translations
   ```

2. Generate an individual language message catalog. E.g. for Italian (it) you
   would do:

   `pybabel init -i messages.pot -d translations -l it`

   That should leave a `messages.po` file nested under the directory specified
   by the given `-d` argument (e.g.: `translations/it/LC_MESSAGES/messages.po`);

3. Open it in your favorite text editor and translate the collected messages;

4. Repeat steps 1-3 for each target language;

4. When finished, compile with:

   `pybabel compile -d translations`

5. Finally, add the newly available languages to the `config.py` file, as
   follows:

   ```
   LANGUAGES = {
        ...
        'it': 'Italian',
        ...
    }
    ```

You'll need to follow again these steps each time you add or change some text in
the code. See the [Flask-Babel Tutorial](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n)
for more on this subject.


How To Deploy With Apache
-------------------------

Documentation based in http://flask.pocoo.org/docs/deploying/mod_wsgi/

We use a virtualenv to deploy the project and apache virtual host on Ubuntu
13.04, This configuration es very general, I guess that works in almost all
linux OS

Definitions:

 * **Project path:** */var/linkode_home/*
 * **Application path:** */var/linkode_home/linkode_app*
 * **VirtualEnv Path:** */var/linkode_home/linkode_virtualenv*
 * **User:** *www-data*

Create virtualenv:

```
cd /var/linkode_home
virtualenv linkode_virtualenv
cd linkode_virtualenv
source bin/activate
```

Clone repository:

```
cd /var/linkode_home/
git clone https://github.com/facundobatista/kilink.git linkode_app
```

Install the requirements:

```
cd linkode_app
pip install -r requirements.txt
```

    
The WSGI configuration file is already in the project, ready to use; for develop 
or debugging you can add to it:

```
application.debug = True
# Needs install paste via pip "pip install paste"
# For More information:
# http://code.google.com/p/modwsgi/wiki/DebuggingTechniques#Browser_Based_Debugger
from paste.evalexception.middleware import EvalException
application = EvalException(application)
```

Create a virtual host configuration file in /etc/apache2/sites-enabled/
with the name that you want, in this case "linkode"
    
`sudo vi /etc/apache2/sites-enabled/linkode`

And paste this:

```
<VirtualHost *>
    ServerName linkode.mydomain

    WSGIDaemonProcess linkode user=www-data group=www-data threads=5
    WSGIScriptAlias / /var/linkode_home/linkode.wsgi
    WSGIScriptReloading On

    <Directory /var/linkode_home/linkode_app/kilink/>
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
```

Restart Apache and enjoy!


Clients
-------

* **GUI**, Graphical: https://github.com/juancarlospaco/linkode-gui#linkode-gui
* **CLI**, Command Line: https://github.com/humitos/linkodeit#linkodeit
