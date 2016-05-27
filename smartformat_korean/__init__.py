# -*- coding: utf-8 -*-
"""
   smartformat.ext.korean
   ~~~~~~~~~~~~~~~~~~~~~~

   A SmartFormat extension for Korean.

   :copyright: (c) 2016 by What! Studio
   :license: BSD, see LICENSE for more details.

"""
import functools

from smartformat import extension

from .hangul import is_hangul
from .particles import Euro, Ida, Particle


__all__ = ['ko']


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


@extension(['ko', ''])
def ko(formatter, value, name, option, format):
    """Chooses different allomorphic forms for Korean particles.

    Implicit Spec: `{:[-]post_position}`
    Explicit Spec: `{:ko(post_position):item}`

    Example::

       >>> smart.format(u'{pokemon:은} {skill:을} 시전했다!',
       ...              pokemon=u'피카츄', skill=u'전광석화')
       피카츄는 전광석화를 시전했다!
       >>> smart.format(u'{subj:는} {obj:다}.',
       ...              subj=u'대한민국', obj=u'민주공화국')
       대한민국은 민주공화국이다.

    """
    if not name:
        if format.startswith(u'-'):
            __, __, option = format.partition(u'-')
            format = u''
        else:
            option, format = format, u'{}'
        if not option or not all(is_hangul(l) for l in option):
            # All option letters have to be Hangul
            # to use this extension implicitly.
            return
    try:
        # Choose a known particle.
        particle = _particle_index[option]
    except KeyError:
        # Or "이다" by default.
        particle = functools.partial(Ida, verb=option)
    return formatter.format(format, value) + particle(value)