=======
Dojo2py
=======

------------
Dependencies
------------

Dependencies (server):
~~~~~~~~~~~~~~~~~~~~~~

- Python
- Twisted
- Flask (for client control)


Dependencies (client):
~~~~~~~~~~~~~~~~~~~~~~

- Browser with webscokets support


-------
Running
-------

Temporary production:
~~~~~~~~~~~~~~~~~~~~~

First, make sure you set the ``SALT`` variable to an string in 
"dojo2py/server/config.py" and "dojo2py/client/client.py", for example::

    SALT = '2[_ -d]}{sa'

Second, up the websockets server::

    cd dojo2py/server
    python server.py

So, open dojo2py/client/index.html on your webbrowser (google chrome or safari)


Development:
~~~~~~~~~~~~

First, make sure you change ``SALT`` variable to an emtpy string in 
"dojo2py/server/config.py" and "dojo2py/client/client.py" as following::

    SALT = ''

Second, up the websockets server::

    cd dojo2py/server
    python server.py

Third, up flask server::

    cd dojo2py/client
    python client.py

So, open http://127.0.0.1:5000 on your webbrowser (google chrome or safari)


---------------
Important links
---------------

- `ACE's API <https://github.com/ajaxorg/ace/wiki/Embedding---API>`_
- `Diff-Match-Patch's API <http://code.google.com/p/google-diff-match-patch/wiki/API>`_
