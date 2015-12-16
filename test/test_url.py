#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import webob
from urlpath import URL, JailedURL


class UrlTest(unittest.TestCase):

    def test_simple(self):
        original = 'http://www.example.com/path/to/file.ext?query#fragment'
        url = URL(original)

        self.assertEqual(str(url), original)
        self.assertEqual(url.as_uri(), original)
        self.assertEqual(url.as_posix(), original)
        self.assertEqual(url.drive, 'http://www.example.com')
        self.assertEqual(url.root, '/')
        self.assertEqual(url.anchor, 'http://www.example.com/')
        self.assertEqual(url.path, '/path/to/file.ext')
        self.assertEqual(url.name, 'file.ext')
        self.assertEqual(url.suffix, '.ext')
        self.assertListEqual(url.suffixes, ['.ext'])
        self.assertEqual(url.stem, 'file')
        self.assertTupleEqual(url.parts, ('http://www.example.com/', 'path', 'to', 'file.ext'))
        self.assertEqual(str(url.parent), 'http://www.example.com/path/to')
        self.assertEqual(url.scheme, 'http')
        self.assertEqual(url.netloc, 'www.example.com')
        self.assertEqual(url.query, 'query')
        self.assertEqual(url.fragment, 'fragment')

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
        self.assertEqual(str(url.with_userinfo(None, None)), 'http://www.example.com/path/to/file.exe?query?fragment')
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
        self.assertTupleEqual(url.form.get('field1'), ('value1', 'value2'))
        self.assertTupleEqual(url.form.get('field2'), ('hello, world&python', ))
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
        self.assertTupleEqual(url.form.get('field3'), ('value3', ))
        self.assertTupleEqual(url.form.get('field4'), ('1', '2', '3'))

    def test_query_field_order(self):
        url = URL('http://example.com/').with_query(field1='field1', field2='field2', field3='field3')

        self.assertEqual(str(url), 'http://example.com/?field1=field1&field2=field2&field3=field3')

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

        self.assertEqual(URL('htp://example.com/').trailing_sep, '')
        self.assertEqual(URL('htp://example.com/with/sep/').trailing_sep, '/')
        self.assertEqual(URL('htp://example.com/without/sep').trailing_sep, '')
        self.assertEqual(URL('htp://example.com/with/double-sep//').trailing_sep, '//')

    def test_webob(self):
        base_url = 'http://www.example.com'
        url = URL(webob.Request.blank('/webob/request', base_url=base_url))

        self.assertEqual(str(url), 'http://www.example.com/webob/request')
        self.assertEqual(str(url / webob.Request.blank('/replaced/path', base_url=base_url)),
                         'http://www.example.com/replaced/path')
        self.assertEqual(str(url / webob.Request.blank('/replaced/path')),
                         'http://localhost/replaced/path')

    def test_webob_jail(self):
        request = webob.Request.blank('/path/to/filename.ext', {'SCRIPT_NAME': '/app/root'})

        self.assertEqual(request.application_url, 'http://localhost/app/root')
        self.assertEqual(request.url, 'http://localhost/app/root/path/to/filename.ext')

        url = JailedURL(request)

        self.assertEqual(str(url.chroot), 'http://localhost/app/root')
        self.assertEqual(str(url), 'http://localhost/app/root/path/to/filename.ext')

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

    def test_init_with_empty_string(self):
        url = URL('')

        self.assertEqual(str(url), '')

    def test_encoding(self):
        self.assertEqual(URL('http://www.xn--alliancefranaise-npb.nu/').hostname, 'www.alliancefran\xe7aise.nu')
        self.assertEqual(str(URL('http://localhost/').with_hostinfo('www.alliancefran\xe7aise.nu')),
                         'http://www.xn--alliancefranaise-npb.nu/')

        url = URL('http://%75%73%65%72:%70%61%73%73%77%64@httpbin.org/basic-auth/user/passwd')
        self.assertEqual(url.username, 'user')
        self.assertEqual(url.password, 'passwd')

        username = 'foo@example.com'
        password = 'pa$$word'
        url = URL('http://example.com').with_userinfo(username, password)
        self.assertEqual(url.username, username)
        self.assertEqual(url.password, password)
        self.assertEqual(str(url), 'http://foo%40example.com:pa%24%24word@example.com')

        self.assertEqual(str(URL('http://example.com/日本語の/パス')),
                         'http://example.com/%E6%97%A5%E6%9C%AC%E8%AA%9E%E3%81%AE/%E3%83%91%E3%82%B9')

        original = 'http://example.com/\u3081\u3061\u3083\u304f\u3061\u3083\u306a/\u30d1\u30b9/%2F%23%3F'
        url = URL(original)
        self.assertEqual(str(url), 'http://example.com/%E3%82%81%E3%81%A1%E3%82%83%E3%81%8F%E3%81%A1%E3%82%83%E3%81%AA/'
                                   '%E3%83%91%E3%82%B9/%2F%23%3F')
        self.assertEqual(url.path, '/%E3%82%81%E3%81%A1%E3%82%83%E3%81%8F%E3%81%A1%E3%82%83%E3%81%AA/'
                                   '%E3%83%91%E3%82%B9/%2F%23%3F')
        self.assertEqual(url.name, '/#?')
        self.assertTupleEqual(url.parts, ('http://example.com/', '\u3081\u3061\u3083\u304f\u3061\u3083\u306a',
                                          '\u30d1\u30b9', '/#?'))

        self.assertEqual(str(URL('http://example.com/name').with_name('\u65e5\u672c\u8a9e/\u540d\u524d')),
                         'http://example.com/%E6%97%A5%E6%9C%AC%E8%AA%9E%2F%E5%90%8D%E5%89%8D')

        self.assertEqual(str(URL('http://example.com/name') / '\u65e5\u672c\u8a9e/\u540d\u524d'),
                         'http://example.com/name/%E6%97%A5%E6%9C%AC%E8%AA%9E/%E5%90%8D%E5%89%8D')

        self.assertEqual(str(URL('http://example.com/file').with_suffix('.///')), 'http://example.com/file.%2F%2F%2F')

    def test_idempotent(self):
        url = URL('http://\u65e5\u672c\u8a9e\u306e.\u30c9\u30e1\u30a4\u30f3.jp/'
                  'path/to/\u30d5\u30a1\u30a4\u30eb.ext?\u30af\u30a8\u30ea')

        self.assertEqual(url, URL(str(url)))
        self.assertEqual(url, URL('http://xn--u9ju32nb2abz6g.xn--eckwd4c7c.jp/'
                                  'path/to/\u30d5\u30a1\u30a4\u30eb.ext?\u30af\u30a8\u30ea'))

    def test_embed(self):
        url = URL('http://example.com/').with_fragment(URL('/param1/param2').with_query(f1=1, f2=2))
        self.assertEqual(str(url), 'http://example.com/#/param1/param2?f1=1&f2=2')


if __name__ == '__main__':
    unittest.main()
