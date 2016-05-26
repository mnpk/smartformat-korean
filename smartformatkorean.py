# -*- coding: utf-8 -*-
"""
   smartformat_korean
   ~~~~~~~~~~~~~~~~~~

   SmartFormat extensions for Korean.

   :copyright: (c) 2016 by What! Studio
   :license: BSD, see LICENSE for more details.

"""
import functools
import re

from bidict import bidict
from six import PY2, with_metaclass
from smartformat import ext


# Korean phonemes as known as "자소".
INITIALS = list(u'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ')
VOWELS = list(u'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ')
FINALS = [None]
FINALS.extend(u'ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ')

# Lengths of the phonemes.
NUM_INITIALS = len(INITIALS)
NUM_VOWELS = len(VOWELS)
NUM_FINALS = len(FINALS)

FIRST_HANGUL_OFFSET = ord(u'가')
ENDING_BRACKET_PATTERN = re.compile(r'\(.*?\)$')


def is_hangul(letter):
    return u'가' <= letter <= u'힣'


def split_phonemes(letter, initial=True, vowel=True, final=True):
    """Splits Korean phonemes as known as "자소" from a Hangul letter.

    :returns: (initial, vowel, final)
    :raises ValueError: `letter` is not a Hangul single letter.

    """
    if len(letter) != 1 or not is_hangul(letter):
        raise ValueError('Not Hangul letter: %r' % letter)
    offset = ord(letter) - FIRST_HANGUL_OFFSET
    phonemes = [None] * 3
    if initial:
        phonemes[0] = INITIALS[offset / (NUM_VOWELS * NUM_FINALS)]
    if vowel:
        phonemes[1] = VOWELS[(offset / NUM_FINALS) % NUM_VOWELS]
    if final:
        phonemes[2] = FINALS[offset % NUM_FINALS]
    return tuple(phonemes)


def join_phonemes(*args):
    """Joins a Hangul letter from Korean phonemes."""
    # Normalize arguments as initial, vowel, final.
    if len(args) == 1:
        # tuple of (initial, vowel[, final])
        args = args[0]
    if len(args) == 2:
        args += (None,)
    try:
        initial, vowel, final = args
    except ValueError:
        raise TypeError('join_phonemes() takes at most 3 arguments')
    offset = (
        (INITIALS.index(initial) * NUM_VOWELS + VOWELS.index(vowel)) *
        NUM_FINALS + FINALS.index(final)
    )
    return unichr(FIRST_HANGUL_OFFSET + offset)


def pick_final(letter):
    """Picks only a final Hangul consonant from a Hangul letter."""
    __, __, final = \
        split_phonemes(letter, initial=False, vowel=False, final=True)
    return final


class Particle(object):
    """Represents a Korean particle as known as "조사" in Korean."""

    def __init__(self, form1, form2, default=None):
        self.form1 = form1
        self.form2 = form2
        if default is None:
            self.default = self.combine_forms(form1, form2)
        else:
            self.default = default

    def __call__(self, word):
        """Selects an allomorphic form for the given word."""
        word = ENDING_BRACKET_PATTERN.sub(u'', word)
        try:
            final = pick_final(word[-1])
        except ValueError:
            return self.default
        else:
            return self.allomorph(final)

    def __iter__(self):
        """Iterates for all allomorphic forms."""
        return iter([self.default, self.form1, self.form2])

    def allomorph(self, final):
        """Determines one of allomorphic forms based on a Hangul jongseung."""
        return self.form2 if final is None else self.form1

    def __unicode__(self):
        return self.default

    def __repr__(self):
        return '<Particle: ' + (repr if PY2 else str)(self.default) + '>'

    @staticmethod
    def combine_forms(form1, form2):
        """Generates a general combination form for Korean particles."""
        return u'%s(%s)' % (form1, form2)


class SpecialParticleMeta(type):

    def __new__(meta, name, bases, attrs):
        base_meta = super(SpecialParticleMeta, meta)
        cls = base_meta.__new__(meta, name, bases, attrs)
        if bases == (Particle,):
            return cls
        # Instantiate directly instead of returning a class.
        return cls()


class SpecialParticle(with_metaclass(SpecialParticleMeta, Particle)):
    """The base class for special particles which have uncommon allomorphic
    rule.
    """

    def __init__(self, *args, **kwargs):
        pass

    def __repr__(self):
        arg = self.__class__.__name__ if PY2 else self.default
        return '<Particle(special): %s>' % arg


class Euro(SpecialParticle):
    """"으로" has a special allomorphic rule after final Rieul."""

    form1 = u'으로'
    form2 = u'로'
    default = u'(으)로'

    def allomorph(self, final):
        return self.form2 if final is None or final == u'ㄹ' else self.form1


class Ida(SpecialParticle):
    """"이다" is a verbal prticle.  Like other Korean verbs, it is also
    fusional.
    """

    form1 = u'이'
    form2 = u''
    default = u'(이)'

    j_injections = bidict({u'ㅓ': u'ㅕ', u'ㅔ': u'ㅖ'})
    allomorph = NotImplemented  # This method is not used.

    def normalize_verb(self, verb):
        """Normalizes a verb by removing initial "이" or "(이)"s."""
        return re.sub(u'^이|\(이\)', u'', verb)

    def __call__(self, word, verb):
        word = ENDING_BRACKET_PATTERN.sub(u'', word)
        verb = self.normalize_verb(verb)
        try:
            final = pick_final(word[-1])
        except ValueError:
            final = u''
        next_initial, next_vowel, next_final = split_phonemes(verb[0])
        if next_initial == u'ㅇ':
            if next_vowel == u'ㅣ':
                # No allomorphs when a verb starts with "이" and has a final.
                return verb
            mapping = None
            if final is None and next_vowel in self.j_injections:
                # Squeeze "이어" or "이에" to "여" or "예"
                # after a word which ends with a vowel.
                mapping = self.j_injections
            elif final is not None and next_vowel in self.j_injections.inv:
                # Lengthen "여" or "예" to "이어" or "이에"
                # after a word which ends with a consonant.
                mapping = self.j_injections.inv
            if mapping is not None:
                next_vowel = mapping[next_vowel]
                verb = join_phonemes(u'ㅇ', next_vowel, next_final) + verb[1:]
        # Select an allomorph.
        if final is None:
            return verb
        elif final == u'':
            return u'(이)' + verb
        else:
            return u'이' + verb


#: Allomorphic Korean particles.
PARTICLES = [
    # Simple allomorphic rule.
    Particle(u'은', u'는'),
    Particle(u'이', u'가'),
    Particle(u'을', u'를'),
    Particle(u'과', u'와'),
    # Vocative particles.
    Particle(u'아', u'야'),
    Particle(u'이여', u'여', u'(이)여'),
    Particle(u'이시여', u'시여', u'(이)시여'),
    # Special particles.
    Euro,
]


# Index particles by their forms.
_particle_index = {}
for p in PARTICLES:
    for form in p:
        if form in _particle_index:
            raise KeyError('Form %r duplicated' % form)
        _particle_index[form] = p


@ext(['ko', ''], pass_formatter=True)
def ko(formatter, value, name, option, format):
    """Chooses different allomorphic forms for Korean particles.

    Implicit Spec: `{:[-]post_position}`
    Explicit Spec: `{:ko(post_position):item}`

    Example::

       >>> smart.format(u'There {num:is an item|are {} items}.', num=1}
       There is an item.
       >>> smart.format(u'There {num:is an item|are {} items}.', num=10}
       There are 10 items.

    """
    if not name:
        if format.startswith(u'-'):
            __, __, option = format.partition(u'-')
            format = u''
        else:
            option, format = format, u'{}'
        if not option or not is_hangul(option[0]):
            return
    try:
        particle = _particle_index[option]
    except KeyError:
        particle = functools.partial(Ida, verb=option)
    return formatter.format(format, value) + particle(value)
