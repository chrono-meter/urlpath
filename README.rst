urlpath provides URL manipulator class that extends `pathlib.PurePath <https://docs.python.org/3/library/pathlib.html#pure-paths>`_.
====================================================================================================================================

.. image:: https://img.shields.io/travis/chrono-meter/urlpath.svg
    :target: https://travis-ci.org/chrono-meter/urlpath

.. image:: https://img.shields.io/pypi/v/urlpath.svg
    :target: https://pypi.python.org/pypi/urlpath

.. image:: https://img.shields.io/pypi/l/urlpath.svg
    :target: http://python.org/psf/license

Dependencies
------------

* Python 3.4, 3.5, 3.6, 3.7, 3.8
* `pathlib <https://pypi.python.org/pypi/pathlib>`_ (Standard library in Python 3.4)
* `unittest.mock <https://docs.python.org/3/library/unittest.mock.html>`_ (Standard library in Python 3.3, or install
  `mock <https://pypi.python.org/pypi/mock>`_)
* `Requests <http://docs.python-requests.org/>`_
* `JMESPath <https://pypi.org/project/jmespath/>`_ (Optional)
* `WebOb <http://webob.org/>`_ (Optional)

Install
-------

``pip install urlpath``

Examples
--------

Import::

    >>> from urlpath import URL

Create object::

    >>> url = URL(
    ...     'https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment')

Representation::

    >>> url
    URL('https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment')
    >>> print(url)
    https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment
    >>> url.as_uri()
    'https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment'
    >>> url.as_posix()
    'https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment'

Access `pathlib.PurePath` compatible properties::

    >>> url.drive
    'https://username:password@secure.example.com:1234'
    >>> url.root
    '/'
    >>> url.anchor
    'https://username:password@secure.example.com:1234/'
    >>> url.path
    '/path/to/file.ext'
    >>> url.name
    'file.ext'
    >>> url.suffix
    '.ext'
    >>> url.suffixes
    ['.ext']
    >>> url.stem
    'file'
    >>> url.parts
    ('https://username:password@secure.example.com:1234/', 'path', 'to', 'file.ext')
    >>> url.parent
    URL('https://username:password@secure.example.com:1234/path/to')

Access scheme::

    >>> url.scheme
    'https'

Access netloc::

    >>> url.netloc
    'username:password@secure.example.com:1234'
    >>> url.username
    'username'
    >>> url.password
    'password'
    >>> url.hostname
    'secure.example.com'
    >>> url.port
    1234

Access query::

    >>> url.query
    'field1=1&field2=2&field1=3'
    >>> url.form_fields
    (('field1', '1'), ('field2', '2'), ('field1', '3'))
    >>> url.form
    <FrozenMultiDict {'field1': ('1', '3'), 'field2': ('2',)}>
    >>> url.form.get_one('field1')
    '1'
    >>> url.form.get_one('field3') is None
    True

Access fragment::

    >>> url.fragment
    'fragment'

Path operation::

    >>> url / 'suffix'
    URL('https://username:password@secure.example.com:1234/path/to/file.ext/suffix')
    >>> url / '../../rel'
    URL('https://username:password@secure.example.com:1234/path/to/file.ext/../../rel')
    >>> (url / '../../rel').resolve()
    URL('https://username:password@secure.example.com:1234/path/rel')
    >>> url / '/'
    URL('https://username:password@secure.example.com:1234/')
    >>> url / 'http://example.com/'
    URL('http://example.com/')

Replace components::

    >>> url.with_scheme('http')
    URL('http://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment')
    >>> url.with_netloc('www.example.com')
    URL('https://www.example.com/path/to/file.ext?field1=1&field2=2&field1=3#fragment')
    >>> url.with_userinfo('joe', 'pa33')
    URL('https://joe:pa33@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#fragment')
    >>> url.with_hostinfo('example.com', 8080)
    URL('https://username:password@example.com:8080/path/to/file.ext?field1=1&field2=2&field1=3#fragment')
    >>> url.with_fragment('new fragment')
    URL('https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2&field1=3#new fragment')
    >>> url.with_components(username=None, password=None, query='query', fragment='frag')
    URL('https://secure.example.com:1234/path/to/file.ext?query#frag')

Replace query::

    >>> url.with_query({'field3': '3', 'field4': [1, 2, 3]})
    URL('https://username:password@secure.example.com:1234/path/to/file.ext?field3=3&field4=1&field4=2&field4=3#fragment')
    >>> url.with_query(field3='3', field4=[1, 2, 3])
    URL('https://username:password@secure.example.com:1234/path/to/file.ext?field3=3&field4=1&field4=2&field4=3#fragment')
    >>> url.with_query('query')
    URL('https://username:password@secure.example.com:1234/path/to/file.ext?query#fragment')
    >>> url.with_query(None)
    URL('https://username:password@secure.example.com:1234/path/to/file.ext#fragment')

Ammend query::

    >>> url.with_query(field1='1').add_query(field2=2)
    URL('https://username:password@secure.example.com:1234/path/to/file.ext?field1=1&field2=2#fragment')
 
Do HTTP requests::

    >>> url = URL('https://httpbin.org/get')
    >>> url.get()
    <Response [200]>

    >>> url = URL('https://httpbin.org/post')
    >>> url.post(data={'key': 'value'})
    <Response [200]>

    >>> url = URL('https://httpbin.org/delete')
    >>> url.delete()
    <Response [200]>

    >>> url = URL('https://httpbin.org/patch')
    >>> url.patch(data={'key': 'value'})
    <Response [200]>

    >>> url = URL('https://httpbin.org/put')
    >>> url.put(data={'key': 'value'})
    <Response [200]>

Jail::

    >>> root = 'http://www.example.com/app/'
    >>> current = 'http://www.example.com/app/path/to/content'
    >>> url = URL(root).jailed / current
    >>> url / '/root'
    JailedURL('http://www.example.com/app/root')
    >>> (url / '../../../../../../root').resolve()
    JailedURL('http://www.example.com/app/root')
    >>> url / 'http://localhost/'
    JailedURL('http://www.example.com/app/')
    >>> url / 'http://www.example.com/app/file'
    JailedURL('http://www.example.com/app/file')

Trailing separator will be remained::

    >>> url = URL('http://www.example.com/path/with/trailing/sep/')
    >>> str(url).endswith('/')
    True
    >>> url.trailing_sep
    '/'
    >>> url.name
    'sep'
    >>> url.path
    '/path/with/trailing/sep/'
    >>> url.parts[-1]
    'sep'

    >>> url = URL('http://www.example.com/path/without/trailing/sep')
    >>> str(url).endswith('/')
    False
    >>> url.trailing_sep
    ''
    >>> url.name
    'sep'
    >>> url.path
    '/path/without/trailing/sep'
    >>> url.parts[-1]
    'sep'

