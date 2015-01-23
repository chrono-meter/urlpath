#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import webob
from urlpath import URL


class UrlTest(unittest.TestCase):

    def test_simple(self):
        original = 'http://www.example.com/path/to/file.ext?query#fragment'
        url = URL(original)
        self.assertEqual(str(url), original)
        self.assertEqual(url.as_uri(), original)
        self.assertEqual(url.as_posix(), original)
        self.assertEqual(url.scheme, 'http')
        self.assertEqual(url.netloc, 'www.example.com')
        self.assertEqual(url.path, '/path/to/file.ext')
        self.assertEqual(url.query, 'query')
        self.assertEqual(url.fragment, 'fragment')
        self.assertEqual(url.drive, 'http://www.example.com')
        self.assertEqual(url.root, '/')
        self.assertTupleEqual(url.parts, ('http://www.example.com/', 'path', 'to', 'file.ext'))
        self.assertEqual(str(url.parent), 'http://www.example.com/path/to')

    def test_netloc_mixin(self):
        url = URL('https://username:password@secure.example.com:1234/secure/path?query#fragment')

        self.assertEqual(url.drive, 'https://username:password@secure.example.com:1234')
        self.assertEqual(url.scheme, 'https')
        self.assertEqual(url.netloc, 'username:password@secure.example.com:1234')
        self.assertEqual(url.username, 'username')
        self.assertEqual(url.password, 'password')
        self.assertEqual(url.hostname, 'secure.example.com')
        self.assertEqual(url.port, 1234)

    def test_join(self):
        url = URL('http://www.example.com/path/to/file.ext?query#fragment')
        self.assertEqual(str(url / 'https://secure.example.com/path'), 'https://secure.example.com/path')
        self.assertEqual(str(url / '/changed/path'), 'http://www.example.com/changed/path')
        self.assertEqual(str(url.with_name('other_file')), 'http://www.example.com/path/to/other_file')

    def test_path(self):
        url = URL('http://www.example.com/path/to/file.ext?query#fragment')
        self.assertEqual(url.path, '/path/to/file.ext')

    def test_with(self):
        url = URL('http://www.example.com/path/to/file.exe?query?fragment')
        self.assertEqual(str(url.with_scheme('https')), 'https://www.example.com/path/to/file.exe?query?fragment')
        self.assertEqual(str(url.with_netloc('localhost')), 'http://localhost/path/to/file.exe?query?fragment')
        self.assertEqual(str(url.with_userinfo('username', 'password')),
                         'http://username:password@www.example.com/path/to/file.exe?query?fragment')
        self.assertEqual(str(url.with_hostinfo('localhost', 8080)),
                         'http://localhost:8080/path/to/file.exe?query?fragment')

        self.assertEqual(str(URL('http://example.com/base/') / 'path/to/file'), 'http://example.com/base/path/to/file')

        self.assertEqual(str(URL('http://example.com/path/?q') / URL('http://localhost/app/?q') / URL('to/content')),
                         'http://localhost/app/to/content')

    def test_query(self):
        query = 'field1=value1&field1=value2&field2=hello,%20world%26python'
        url = URL('http://www.example.com/form?' + query)

        self.assertEqual(url.query, query)
        self.assertSetEqual(set(url.form), {'field1', 'field2'})
        self.assertEqual(url.form.get('field1'), ['value1', 'value2'])
        self.assertEqual(url.form.get('field2'), ['hello, world&python'])
        self.assertIn('field1', url.form)
        self.assertIn('field2', url.form)
        self.assertNotIn('field3', url.form)
        self.assertNotIn('field4', url.form)

        url = url.with_query({'field3': 'value3', 'field4': [1, 2, 3]})
        self.assertSetEqual(set(url.form), {'field3', 'field4'})
        self.assertNotIn('field1', url.form)
        self.assertNotIn('field2', url.form)
        self.assertIn('field3', url.form)
        self.assertIn('field4', url.form)
        self.assertEqual(url.form.get('field3'), ['value3'])
        self.assertEqual(url.form.get('field4'), ['1', '2', '3'])

    def test_fragment(self):
        url = URL('http://www.example.com/path/to/file.ext?query#fragment')
        self.assertEqual(url.fragment, 'fragment')
        url = url.with_fragment('new fragment')
        self.assertEqual(str(url), 'http://www.example.com/path/to/file.ext?query#new fragment')
        self.assertEqual(url.fragment, 'new fragment')

    def test_resolve(self):
        url = URL('http://www.example.com//./../path/./..//./file/')
        self.assertEqual(str(url.resolve()), 'http://www.example.com/file')

    def test_trailing_sep(self):
        original = 'http://www.example.com/path/with/trailing/sep/'
        url = URL(original)
        self.assertEqual(str(url), original)
        self.assertEqual(url.name, 'sep')
        self.assertEqual(url.parts[-1], 'sep')

    def test_webob(self):
        base_url = 'http://www.example.com'

        url = URL(webob.Request.blank('/webob/request', base_url=base_url))
        self.assertEqual(str(url), 'http://www.example.com/webob/request')
        self.assertEqual(str(url / webob.Request.blank('/replaced/path', base_url=base_url)),
                         'http://www.example.com/replaced/path')
        self.assertEqual(str(url / webob.Request.blank('/replaced/path')),
                         'http://localhost/replaced/path')

    def test_jail(self):
        root = 'http://www.example.com/app/'
        current = 'http://www.example.com/app/path/to/content'
        url = URL(root).jailed / current
        self.assertEqual(str(url), current)
        self.assertEqual(str(url.chroot), root)
        self.assertEqual(str(url / 'appendix'), 'http://www.example.com/app/path/to/content/appendix')
        self.assertEqual(str(url / './appendix'), 'http://www.example.com/app/path/to/content/appendix')
        self.assertEqual(str(url / '/root'), 'http://www.example.com/app/root')
        self.assertEqual(str(url / 'http://other.domain/'), 'http://www.example.com/app/')
        self.assertEqual(str((url / '../file').resolve()), 'http://www.example.com/app/path/to/file')
        self.assertEqual(str((url / '../../../../../root').resolve()), 'http://www.example.com/app/root')
        self.assertEqual(str((url / '/../../../../../root').resolve()), 'http://www.example.com/app/root')
        self.assertEqual(str(url / 'http://www.example.com/app/path'), 'http://www.example.com/app/path')
