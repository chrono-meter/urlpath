#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Object-oriented URL from `urllib.parse` and `pathlib`
"""
__version__ = '1.1.7'
__author__ = __author_email__ = 'chrono-meter@gmx.net'
__license__ = 'PSF'
__url__ = 'https://github.com/chrono-meter/urlpath'
__download_url__ = 'http://pypi.python.org/pypi/urlpath'
# http://pypi.python.org/pypi?%3Aaction=list_classifiers
__classifiers__ = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: Python Software Foundation License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Software Development :: Libraries :: Python Modules',
]
__all__ = ('URL',)

import collections.abc
import functools
import re
import urllib.parse
from pathlib import _PosixFlavour, PurePath

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import requests

try:
    import jmespath
except ImportError:
    jmespath = None

try:
    import webob
except ImportError:
    webob = None

missing = object()


# http://stackoverflow.com/a/2704866/3622941
class FrozenDict(collections.abc.Mapping):
    """Immutable dict object."""
    __slots__ = ('_d', '_hash')

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._hash = None

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)

    def __getitem__(self, key):
        return self._d[key]

    def __hash__(self):
        # It would have been simpler and maybe more obvious to
        # use hash(tuple(sorted(self._d.iteritems()))) from this discussion
        # so far, but this solution is O(n). I don't know what kind of
        # n we are going to run into, but sometimes it's hard to resist the
        # urge to optimize when it will gain improved algorithmic performance.
        if self._hash is None:
            self._hash = 0
            for pair in self.iteritems():
                self._hash ^= hash(pair)
        return self._hash

    def __repr__(self):
        return '<{} {{{}}}>'.format(self.__class__.__name__,
                                    ', '.join('{!r}: {!r}'.format(*i) for i in sorted(self._d.items())))


class MultiDictMixin:
    def get_one(self, key, default=None, predicate=None, type=None):
        # `predicate` comes from `inspect.getmembers`.
        try:
            values = self[key]
        except LookupError:
            pass
        else:
            for value in values:
                if not predicate or predicate(value):
                    return value if not type else type(value)

        return default


class FrozenMultiDict(MultiDictMixin, FrozenDict):
    pass


def cached_property(getter):
    """Limited version of `functools.lru_cache`. But `__hash__` is not required.
    """

    @functools.wraps(getter)
    def helper(self):
        key = '_cached_property_' + getter.__name__

        if key in self.__dict__:
            return self.__dict__[key]

        result = self.__dict__[key] = getter(self)
        return result

    return helper


def netlocjoin(username, password, hostname, port):
    """Helper function for building netloc string.

    :param str username: username string or `None`
    :param str password: password string or `None`
    :param str hostname: hostname string or `None`
    :param int port: port number or `None`
    :return: netloc string
    :rtype: str
    """
    result = ''

    if username is not None:
        result += urllib.parse.quote(username, safe='')

    if password is not None:
        result += ':' + urllib.parse.quote(password, safe='')

    if result:
        result += '@'

    if hostname is not None:
        result += hostname.encode('idna').decode('ascii')

    if port is not None:
        result += ':' + str(port)

    return result


class _URLFlavour(_PosixFlavour):
    has_drv = True  # drive is scheme + netloc
    is_supported = True  # supported in all platform

    def splitroot(self, part, sep=_PosixFlavour.sep):
        assert sep == self.sep
        assert '\\x00' not in part

        scheme, netloc, path, query, fragment = urllib.parse.urlsplit(part)

        # trick to escape '/' in query and fragment and trailing
        if not re.match(re.escape(sep) + '+$', path):
            path = re.sub('%s+$' % (re.escape(sep),), lambda m: '\\x00' * len(m.group(0)), path)
        path = urllib.parse.urlunsplit(('', '', path, query.replace('/', '\\x00'), fragment.replace('/', '\\x00')))

        drive = urllib.parse.urlunsplit((scheme, netloc, '', '', ''))
        root, path = re.match('^(%s*)(.*)$' % (re.escape(sep),), path).groups()

        return drive, root, path


class URL(urllib.parse._NetlocResultMixinStr, PurePath):
    _flavour = _URLFlavour()
    _parse_qsl_args = {}
    _urlencode_args = {'doseq': True}

    @classmethod
    def _parse_args(cls, args):
        return super()._parse_args((cls._canonicalize_arg(a) for a in args))

    @classmethod
    def _canonicalize_arg(cls, a):
        if isinstance(a, urllib.parse.SplitResult):
            return urllib.parse.urlunsplit(a)

        if isinstance(a, urllib.parse.ParseResult):
            return urllib.parse.urlunparse(a)

        if webob and isinstance(a, webob.Request):
            return a.url

        return a

    def _init(self):
        if self._parts:
            # trick to escape '/' in query and fragment and trailing
            self._parts[-1] = self._parts[-1].replace('\\x00', '/')

    def _make_child(self, args):
        # replace by parts that have no query and have no fragment
        with patch.object(self, '_parts', list(self.parts)):
            return super()._make_child(args)

    @cached_property
    def __str__(self):
        # NOTE: PurePath.__str__ returns '.' if path is empty.
        return urllib.parse.urlunsplit(self.components)

    @cached_property
    def __bytes__(self):
        return str(self).encode('utf-8')

    # TODO: sort self.query in __hash__

    @cached_property
    def as_uri(self):
        """Return URI."""
        return str(self)

    @property
    @cached_property
    def parts(self):
        """An object providing sequence-like access to the
        components in the filesystem path."""
        if self._drv or self._root:
            return tuple([self._parts[0]] + [urllib.parse.unquote(i) for i in self._parts[1:-1]] + [self.name])
        else:
            return tuple([urllib.parse.unquote(i) for i in self._parts[:-1]] + [self.name])

    @property
    @cached_property
    def components(self):
        """Url components, `(scheme, netloc, path, query, fragment)`."""
        return self.scheme, self.netloc, self.path, self.query, self.fragment

    _cparts = components

    @property
    @cached_property
    def scheme(self):
        """The scheme of url."""
        return urllib.parse.urlsplit(self._drv).scheme

    @property
    @cached_property
    def netloc(self):
        """The scheme of url."""
        return netlocjoin(self.username, self.password, self.hostname, self.port)

    @property
    @cached_property
    def _userinfo(self):
        return urllib.parse.urlsplit(self._drv)._userinfo

    @property
    @cached_property
    def _hostinfo(self):
        return urllib.parse.urlsplit(self._drv)._hostinfo

    @property
    @cached_property
    def hostinfo(self):
        """The hostinfo of url. "hostinfo" is hostname and port."""
        return netlocjoin(None, None, self.hostname, self.port)

    @property
    @cached_property
    def username(self):
        """The username of url."""
        # NOTE: username and password can be encoded by percent-encoding.
        #       http://%75%73%65%72:%70%61%73%73%77%64@httpbin.org/basic-auth/user/passwd
        result = super().username
        if result is not None:
            result = urllib.parse.unquote(result)
        return result

    @property
    @cached_property
    def password(self):
        """The password of url."""
        result = super().password
        if result is not None:
            result = urllib.parse.unquote(result)
        return result

    @property
    @cached_property
    def hostname(self):
        """The hostname of url."""
        result = super().hostname
        if result is not None:
            try:
                result = result.encode('ascii').decode('idna')
            except UnicodeEncodeError:
                pass
        return result

    @property
    @cached_property
    def path(self):
        """The path of url, it's with trailing sep."""

        # https://tools.ietf.org/html/rfc3986#appendix-A
        safe_pchars = '-._~!$&\'()*+,;=:@'

        begin = 1 if self._drv or self._root else 0

        return self._root \
               + self._flavour.sep.join(
            urllib.parse.quote(i, safe=safe_pchars) for i in self._parts[begin:-1] + [self.name]) \
               + self.trailing_sep

    @property
    @cached_property
    def name(self):
        """The final path component, if any."""
        return urllib.parse.unquote(urllib.parse.urlsplit(super().name).path.rstrip(self._flavour.sep))

    @property
    @cached_property
    def query(self):
        """The query of url."""
        return urllib.parse.urlsplit(super().name).query

    @property
    @cached_property
    def fragment(self):
        """The fragment of url."""
        return urllib.parse.urlsplit(super().name).fragment

    @property
    @cached_property
    def trailing_sep(self):
        """The trailing separator of url."""
        return re.search('(' + re.escape(self._flavour.sep) + '*)$', urllib.parse.urlsplit(super().name).path).group(0)

    @property
    @cached_property
    def form_fields(self):
        """The query parsed by `urllib.parse.parse_qsl` of url."""
        return tuple(urllib.parse.parse_qsl(self.query, **self._parse_qsl_args))

    @property
    @cached_property
    def form(self):
        """The query parsed by `urllib.parse.parse_qs` of url."""
        return FrozenMultiDict({k: tuple(v)
                                for k, v in urllib.parse.parse_qs(self.query, **self._parse_qsl_args).items()})

    def with_name(self, name):
        """Return a new url with the file name changed."""
        return super().with_name(urllib.parse.quote(name, safe=''))

    def with_suffix(self, suffix):
        """Return a new url with the file suffix changed (or added, if none)."""
        return super().with_suffix(urllib.parse.quote(suffix, safe='.'))

    def with_components(self, *, scheme=missing, netloc=missing, username=missing, password=missing, hostname=missing,
                        port=missing, path=missing, name=missing, query=missing, fragment=missing):
        """Return a new url with components changed."""
        if scheme is missing:
            scheme = self.scheme
        elif scheme is not None and not isinstance(scheme, str):
            scheme = str(scheme)

        if username is not missing or password is not missing or hostname is not missing or port is not missing:
            assert netloc is missing

            if username is missing:
                username = self.username
            elif username is not None and not isinstance(username, str):
                username = str(username)

            if password is missing:
                password = self.password
            elif password is not None and not isinstance(password, str):
                password = str(password)

            if hostname is missing:
                hostname = self.hostname
            elif hostname is not None and not isinstance(hostname, str):
                hostname = str(hostname)

            if port is missing:
                port = self.port

            netloc = netlocjoin(username, password, hostname, port)

        elif netloc is missing:
            netloc = self.netloc

        elif netloc is not None and not isinstance(netloc, str):
            netloc = str(netloc)

        if name is not missing:
            assert path is missing

            if not isinstance(name, str):
                name = str(name)

            path = urllib.parse.urljoin(self.path.rstrip(self._flavour.sep), urllib.parse.quote(name, safe=''))

        elif path is missing:
            path = self.path

        elif path is not None and not isinstance(path, str):
            path = str(path)

        if query is missing:
            query = self.query
        elif isinstance(query, collections.abc.Mapping):
            query = urllib.parse.urlencode(sorted(query.items()), **self._urlencode_args)
        elif isinstance(query, str):
            # TODO: Is escaping '#' required?
            # query = query.replace('#', '%23')
            pass
        elif isinstance(query, collections.abc.Sequence):
            query = urllib.parse.urlencode(query, **self._urlencode_args)
        elif query is not None:
            query = str(query)

        if fragment is missing:
            fragment = self.fragment
        elif fragment is not None and not isinstance(fragment, str):
            fragment = str(fragment)

        return self.__class__(urllib.parse.urlunsplit((scheme, netloc, path, query, fragment)))

    def with_scheme(self, scheme):
        """Return a new url with the scheme changed."""
        return self.with_components(scheme=scheme)

    def with_netloc(self, netloc):
        """Return a new url with the netloc changed."""
        return self.with_components(netloc=netloc)

    def with_userinfo(self, username, password):
        """Return a new url with the userinfo changed."""
        return self.with_components(username=username, password=password)

    def with_hostinfo(self, hostname, port=None):
        """Return a new url with the hostinfo changed."""
        return self.with_components(hostname=hostname, port=port)

    def with_query(self, query=None, **kwargs):
        """Return a new url with the query changed."""
        assert not (query and kwargs)
        return self.with_components(query=query or kwargs)

    def add_query(self, query=None, **kwargs):
        """Return a new url with the query ammended."""
        assert not (query and kwargs)
        query = query or kwargs
        if not query:
            return self.with_components()
        current = self.query
        if not current:
            return self.with_components(query=query)
        appendix = ''  # suppress lint warnings
        if isinstance(query, collections.abc.Mapping):
            appendix = urllib.parse.urlencode(sorted(query.items()), **self._urlencode_args)
        elif isinstance(query, collections.abc.Sequence):
            appendix = urllib.parse.urlencode(query, **self._urlencode_args)
        elif query is not None:
            appendix = str(query)
        if appendix:
            new = '%s&%s' % (current, appendix)
            return self.with_components(query=new)
        return self.with_components()

    def with_fragment(self, fragment):
        """Return a new url with the fragment changed."""
        return self.with_components(fragment=fragment)

    def resolve(self):
        """Resolve relative path of the path.
        """
        path = []

        for part in self.parts[1:] if self._drv or self._root else self.parts:
            if part == '.' or part == '':
                pass
            elif part == '..':
                if path:
                    del path[-1]
            else:
                path.append(part)

        if self._root:
            path.insert(0, self._root.rstrip(self._flavour.sep))

        path = self._flavour.join(path)
        return self.__class__(urllib.parse.urlunsplit((
            self.scheme, self.netloc, path, self.query, self.fragment
        )))

    @property
    def jailed(self):
        return JailedURL(self, root=self)

    def get(self, params=None, **kwargs):
        r"""Sends a GET request.

        :param params: (optional) Dictionary or bytes to be sent in the query string for the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        response = requests.get(url, params, **kwargs)
        return response

    def options(self, **kwargs):
        r"""Sends a OPTIONS request.

        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        return requests.options(url, **kwargs)

    def head(self, **kwargs):
        r"""Sends a HEAD request.

        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        return requests.options(url, **kwargs)

    def post(self, data=None, json=None, **kwargs):
        r"""Sends a POST request.

        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param json: (optional) json data to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        return requests.post(url, data=data, json=json, **kwargs)

    def put(self, data=None, **kwargs):
        r"""Sends a PUT request.

        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        return requests.put(url, data=data, **kwargs)

    def patch(self, data=None, **kwargs):
        r"""Sends a PATCH request.

        :param data: (optional) Dictionary, bytes, or file-like object to send in the body of the :class:`Request`.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        return requests.patch(url, data=data, **kwargs)

    def delete(self, **kwargs):
        r"""Sends a DELETE request.

        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :return: :class:`Response <Response>` object
        :rtype: requests.Response
        """

        url = str(self)
        return requests.delete(url, **kwargs)

    def get_text(self, name='', query='', pattern='', overwrite=False):
        """Runs a url with a specific query, amending query if necessary, and returns the resulting text"""
        q = query if overwrite else self.add_query(query).query if query else self.query
        url = self.joinpath(name) if name else self
        res = url.with_query(q).get()

        if res:
            if pattern:
                if isinstance(pattern, str):  # patterns should be a compiled transformer like a regex object
                    pattern = re.compile(pattern)

                return list(filter(pattern.match, res.text.split('\n')))

            return res.text

        return res

    def get_json(self, name='', query='', keys='', overwrite=False):
        """Runs a url with a specific query, amending query if necessary, and returns the result after applying a
        transformer"""
        q = query if overwrite else self.add_query(query).query if query else self.query
        url = self.joinpath(name) if name else self
        res = url.with_query(q).get()

        if res and keys:
            if not jmespath:
                raise ImportError('jmespath is not installed')

            if isinstance(keys, str):  # keys should be a compiled transformer like a jamespath object
                keys = jmespath.compile(keys)

            return keys.search(res.json())

        return res.json()


class JailedURL(URL):
    _chroot = None

    def __new__(cls, *args, root=None):
        if root is not None:
            root = URL(root)
        elif cls._chroot is not None:
            root = cls._chroot
        elif webob and len(args) >= 1 and isinstance(args[0], webob.Request):
            root = URL(args[0].application_url)
        else:
            root = URL(*args)

        assert root.scheme and root.netloc and not root.query and not root.fragment, 'malformed root: %s' % (root,)

        if not root.path:
            root = root / '/'

        return type(cls.__name__, (cls,), {'_chroot': root})._from_parts(args)

    def _make_child(self, args):
        drv, root, parts = self._parse_args(args)
        chroot = self._chroot

        if drv:
            # check in _init
            pass

        elif root:
            drv, root, parts = chroot._drv, chroot._root, list(chroot.parts) + parts[1:]

        else:
            drv, root, parts = chroot._drv, chroot._root, list(self.parts) + parts

        return self._from_parsed_parts(drv, root, parts)

    def _init(self):
        chroot = self._chroot

        if self._parts[:len(chroot.parts)] != list(chroot.parts):
            self._drv, self._root, self._parts = chroot._drv, chroot._root, chroot._parts[:]

        super()._init()

    def resolve(self):
        chroot = self._chroot

        with patch.object(self, '_root', chroot.path), \
             patch.object(self, '_parts', [''.join(chroot._parts)] + self._parts[len(chroot._parts):]):
            return super().resolve()

    @property
    def chroot(self):
        return self._chroot
