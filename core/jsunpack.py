"""
    urlresolver XBMC Addon
    Copyright (C) 2013 Bstrdsmkr
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    Adapted for use in xbmc from:
    https://github.com/einars/js-beautify/blob/master/python/jsbeautifier/unpackers/packer.py
    
    usage:
    if detect(some_string):
        unpacked = unpack(some_string)
Unpacker for Dean Edward's p.a.c.k.e.r
"""
import re
def detect(source):
    """Detects whether `source` is P.A.C.K.E.R. coded."""
    source = source.replace(' ', '')
    if re.search('eval\(function\(p,a,c,k,e,(?:r|d)', source):
        return True
    else:
        return False
def unpack(source):
    """Unpacks P.A.C.K.E.R. packed js code."""
    payload, symtab, radix, count = _filterargs(source)
    if count != len(symtab):
        raise UnpackingError('Malformed p.a.c.k.e.r. symtab.')
    try:
        unbase = Unbaser(radix)
    except TypeError:
        raise UnpackingError('Unknown p.a.c.k.e.r. encoding.')
    def lookup(match):
        """Look up symbols in the synthetic symtab."""
        word = match.group(0)
        return symtab[unbase(word)] or word
    source = re.sub(r'\b\w+\b', lookup, payload)
    return _replacestrings(source)
def _filterargs(source):
    """Juice from a source file the four args needed by decoder."""
    juicers = [(r"}\('(.*)', *(\d+), *(\d+), *'(.*)'\.split\('\|'\), *(\d+), *(.*)\)\)"),
               (r"}\('(.*)', *(\d+), *(\d+), *'(.*)'\.split\('\|'\)"),
               (r"} *\( *(.*?) *, *(\d+) *, *(\d+) *, *\(['\s]*([^'\)]*)['\s]*.*?\) *\.split\([\"'\s]*(.*?)[\"'\s]*\)")
               ]
    for i, juicer in enumerate(juicers):
        args = re.search(juicer, source, re.DOTALL)
        if args:
            a = args.groups()
            try:
                if i < len(juicers) - 1:
                    return a[0], a[3].split('|'), int(a[1]), int(a[2])
                else:
                    return openload_clean(a[0]), a[3].split(a[4]), int(a[1]), int(a[2])
            except ValueError:
                raise UnpackingError('Corrupted p.a.c.k.e.r. data.')
    # could not find a satisfying regex
    raise UnpackingError('Could not make sense of p.a.c.k.e.r data (unexpected code structure)')
def _replacestrings(source):
    """Strip string lookup table (list) and replace values in source."""
    match = re.search(r'var *(_\w+)\=\["(.*?)"\];', source, re.DOTALL)
    if match:
        varname, strings = match.groups()
        startpoint = len(match.group(0))
        lookup = strings.split('","')
        variable = '%s[%%d]' % varname
        for index, value in enumerate(lookup):
            source = source.replace(variable % index, '"%s"' % value)
        return source[startpoint:]
    return source

def openload_clean(string):
    import urllib2
    if "function" in string:
        matches = re.findall(r"=\"([^\"]+).*?} *\((\d+)\)", string, re.DOTALL)[0]

        def substr(char):
            char = char.group(0)
            number = ord(char) + int(matches[1])
            if char <= "Z":
                char_value = 90
            else:
                char_value = 122
            if char_value >= number:
                return chr(ord(char))
            else:
                return chr(number - 26)

        string = re.sub(r"[A-z]", substr, matches[0])
        string = urllib2.unquote(string)

    return string

class Unbaser(object):
    """Functor for a given base. Will efficiently convert
    strings to natural numbers."""
    ALPHABET = {
        62: '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
        95: (' !"#$%&\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ'
             '[\]^_`abcdefghijklmnopqrstuvwxyz{|}~')
    }
    def __init__(self, base):
        self.base = base
        # If base can be handled by int() builtin, let it do it for us
        if 2 <= base <= 36:
            self.unbase = lambda string: int(string, base)
        else:
            if base < 62:
                self.ALPHABET[base] = self.ALPHABET[62][0:base]
            elif 62 < base < 95:
                self.ALPHABET[base] = self.ALPHABET[95][0:base]
            # Build conversion dictionary cache
            try:
                self.dictionary = dict((cipher, index) for index, cipher in enumerate(self.ALPHABET[base]))
            except KeyError:
                raise TypeError('Unsupported base encoding.')
            self.unbase = self._dictunbaser
    def __call__(self, string):
        return self.unbase(string)
    def _dictunbaser(self, string):
        """Decodes a  value to an integer."""
        ret = 0
        for index, cipher in enumerate(string[::-1]):
            ret += (self.base ** index) * self.dictionary[cipher]
        return ret


class UnpackingError(Exception):
    """Badly packed source or general error. Argument is a
    meaningful description."""
    pass

