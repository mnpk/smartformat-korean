# -*- coding: utf-8 -*-
import pytest
from smartformat import SmartFormatter

from smartformatkorean import ko


@pytest.fixture
def smart():
    formatter = SmartFormatter()
    formatter.register([ko])
    return formatter


def test_explicit(smart):
    f = smart.format
    assert f(u'{:ko(아):{}} 안녕', u'피카츄') == u'피카츄야 안녕'
    assert f(u'{:ko(아):{}} 안녕', u'버터플') == u'버터플아 안녕'
    assert f(u'{:ko(아):{}} 안녕', u'고라파덕') == u'고라파덕아 안녕'
    assert f(u'{:ko(을):*{}*} 깎는다.', u'사과') == u'*사과*를 깎는다.'
    assert f(u'{:ko(을):}', u'수박') == u'을'


def test_implicit(smart):
    f = smart.format
    assert f(u'{:아} 안녕', u'피카츄') == u'피카츄야 안녕'
    assert f(u'{:아} 안녕', u'버터플') == u'버터플아 안녕'
    assert f(u'{:아} 안녕', u'고라파덕') == u'고라파덕아 안녕'
    assert f(u'{:을} 칼로 깎는다.', u'사과') == u'사과를 칼로 깎는다.'
    assert f(u'{:-을}', u'수박') == u'을'


def test_euro(smart):
    f = smart.format
    assert f(u'{:ko(으로):{}}', u'피카츄') == u'피카츄로'
    assert f(u'{:ko(으로):{}}', u'버터플') == u'버터플로'
    assert f(u'{:ko(으로):{}}', u'고라파덕') == u'고라파덕으로'
    assert f(u'{:ko(으로):{}}', u'Pikachu') == u'Pikachu(으)로'


def test_braket(smart):
    f = smart.format
    assert f(u'{:ko(으로):{}}', u'피카츄(Lv.25)') == u'피카츄(Lv.25)로'
    assert f(u'{:ko(으로):{}}', u'피카(?)츄') == u'피카(?)츄로'
