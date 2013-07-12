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

    - type: POST
    - url: /api/1/kilinks/<kid>/<revno>

To get all the tree of a kilink:

    - type: POST
    - url: /api/1/kilinks/<kid>


How To Try It In Development
----------------------------

    $ virtualenv kilink
    $ cd kilink
    $ git clone git@github.com:facundobatista/kilink.git
    $ source bin/activate
    $ pip install -r requirements.tx
    $ ./test
    $ ./run
