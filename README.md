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

As we don't know if the "get all the tree of a kilink" it's going to be used, it's not implemented yet. But will have the previous API ;-)


How To Try It In Development
----------------------------

    $ virtualenv kilink
    $ cd kilink
    $ git clone git@github.com:facundobatista/kilink.git
    $ source bin/activate
    $ pip install -r requirements.tx
    $ ./test
    $ ./run
