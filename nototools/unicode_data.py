#!/usr/bin/python
#
# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Bleeding-edge version of Unicode Character Database.

Provides an interface similar to Python's own unicodedata package, but with
the bleeding-edge data. The implementation is not efficienct at all, it's
just done this way for the ease of use. The data is coming from bleeding
edge version of the Unicode Standard not yet published, so it is expected to
be unstable and sometimes inconsistent.
"""

__author__ = (
    "roozbeh@google.com (Roozbeh Pournader) and "
    "cibu@google.com (Cibu Johny)")

import os
from os import path
import re
import unicodedata  # Python's internal library


_data_is_loaded = False
_property_value_aliases_data = {}
_character_names_data = {}
_general_category_data = {}
_combining_class_data = {}
_decomposition_data = {}
_bidi_mirroring_characters = set()
_script_data = {}
_script_extensions_data = {}
_block_data = {}
_age_data = {}
_bidi_mirroring_glyph_data = {}
_core_properties_data = {}
_defined_characters = set()
_script_code_to_long_name = {}
_script_long_name_to_code = {}
_lower_to_upper_case = {}

def load_data():
    """Loads the data files needed for the module.

    Could be used by processes who care about controlling when the data is
    loaded. Otherwise, data will be loaded the first time it's needed.
    """
    global _data_is_loaded

    if not _data_is_loaded:
        _load_property_value_aliases_txt()
        _load_unicode_data_txt()
        _load_scripts_txt()
        _load_script_extensions_txt()
        _load_blocks_txt()
        _load_derived_age_txt()
        _load_derived_core_properties_txt()
        _load_bidi_mirroring_txt()
        _data_is_loaded = True


def name(char, *args):
    """"Returns the name of a character.

    Raises a ValueError exception if the character is undefined, unless an
    extra argument is given, in which cast it will return that argument.
    """
    if type(char) is int:
        char = unichr(char)
    # First try and get the name from unidata, which is faster and supports
    # CJK and Hangul automatic names
    try:
        return unicodedata.name(char)
    except ValueError as val_error:
        load_data()
        if ord(char) in _character_names_data:
            return _character_names_data[ord(char)]
        elif args:
            return args[0]
        else:
            raise val_error


def _char_to_int(char):
    """Converts a potential character to its scalar value."""
    if type(char) in [str, unicode]:
        return ord(char)
    else:
        return char


def category(char):
    """Returns the general category of a character."""
    load_data()
    char = _char_to_int(char)
    try:
        return _general_category_data[char]
    except KeyError:
        return "Cn"  # Unassigned


def combining(char):
    """Returns the canonical combining class of a character."""
    load_data()
    char = _char_to_int(char)
    try:
        return _combining_class_data[char]
    except KeyError:
        return 0


def to_upper(char):
    """Returns the upper case for a lower case character.
    This is not full upper casing, but simply reflects the 1-1
    mapping in UnicodeData.txt."""
    load_data()
    cp = _char_to_int(char)
    try:
        if _general_category_data[cp] == 'Ll':
            return unichr(_lower_to_upper_case[cp])
    except KeyError:
        pass
    return char


def canonical_decomposition(char):
    """Returns the canonical decomposition of a character as a Unicode string.
    """
    load_data()
    char = _char_to_int(char)
    try:
        return _decomposition_data[char]
    except KeyError:
        return u""


def script(char):
    """Returns the script property of a character as a four-letter code."""
    load_data()
    char = _char_to_int(char)
    try:
        return _script_data[char]
    except KeyError:
        return "Zzzz"  # Unknown


def script_extensions(char):
    """Returns the script extensions property of a character.

    The return value is a frozenset of four-letter script codes.
    """
    load_data()
    char = _char_to_int(char)
    try:
        return _script_extensions_data[char]
    except KeyError:
        return frozenset(script(char))


def block(char):
    """Returns the block property of a character."""
    load_data()
    char = _char_to_int(char)
    try:
        return _block_data[char]
    except KeyError:
        return "No_Block"


def age(char):
    """Returns the age property of a character as a string.

    Returns None if the character is unassigned."""
    load_data()
    char = _char_to_int(char)
    try:
        return _age_data[char]
    except KeyError:
        return None


def is_default_ignorable(char):
    """Returns true if the character has the Default_Ignorable property."""
    load_data()
    if type(char) in [str, unicode]:
        char = ord(char)
    return char in _core_properties_data["Default_Ignorable_Code_Point"]


def is_defined(char):
    """Returns true if the character is defined in the Unicode Standard."""
    load_data()
    if type(char) in [str, unicode]:
        char = ord(char)
    return char in _defined_characters


def is_private_use(char):
    """Returns true if the characters is a private use character."""
    return category(char) == "Co"


def mirrored(char):
    """Returns 1 if the characters is bidi mirroring, 0 otherwise."""
    load_data()
    if type(char) in [str, unicode]:
        char = ord(char)
    return int(char in _bidi_mirroring_characters)


def bidi_mirroring_glyph(char):
    """Returns the bidi mirroring glyph property of a character."""
    load_data()
    if type(char) in [str, unicode]:
        char = ord(char)
    try:
        return _bidi_mirroring_glyph_data[char]
    except KeyError:
        return None


_DEFINED_CHARACTERS_CACHE = {}

def defined_characters(version=None, scr=None):
    """Returns the set of all defined characters in the Unicode Standard."""
    load_data()
    try:
        return _DEFINED_CHARACTERS_CACHE[(version, scr)]
    except KeyError:
        pass
    characters = _defined_characters
    if version is not None:
        characters = {char for char in characters
                      if age(char) is not None and float(age(char)) <= version}
    if scr is not None:
        characters = {char for char in characters
                      if script(char) == scr or scr in script_extensions(char)}
    characters = frozenset(characters)
    _DEFINED_CHARACTERS_CACHE[(version, scr)] = characters
    return characters


def _folded_script_name(script_name):
    """Folds a script name to its bare bones for comparison."""
    return script_name.translate(None, "'_ ").lower()


def _is_same_script_name(script1, script2):
    """Returns true if the two inputs are basically the same script name."""
    return _folded_script_name(script1) == _folded_script_name(script2)


def script_code(script_name):
    """Returns the four-letter ISO 15924 code of a script from its loose name.
    """
    load_data()
    for code, code_name in _script_code_to_long_name.iteritems():
        if _is_same_script_name(code_name, script_name):
            return code
    return "Zzzz"  # Unknown


def all_script_codes():
    """Returns a frozenset of all script codes."""
    load_data()
    return frozenset(_script_code_to_long_name.keys())


def web_script_code(script_name):
    """Web version of script_code based on generate_website_data.  This
    returns an unrecognized script_name if it is 4 letters long or fails,
    unlike script_code which returns 'Zzzz'."""
    # TODO(dougfelt): see if we can drop this and just use script_code

    load_data()
    script = None
    if script_name in _script_long_name_to_code:
        script = _script_long_name_to_code[script_name]
    else:
        for lname in _script_long_name_to_code:
            if lname.replace('_', '').lower() == script_name.lower():
                script = _script_long_name_to_code[lname]
                break
    if not script:
        script = script_name
        if len(script) != 4:
            raise ValueError("script code '%s' is not the right length." % script)
        else:
            print 'default script code to name \'%s\'' % script
    return script


_HARD_CODED_HUMAN_READABLE_SCRIPT_NAMES = {
    'Nkoo': 'NKo',
    'Qaae': 'Emoji',
    'Zsym': 'Symbols',
}

def human_readable_script_name(code):
    """Returns a human-readable name for the script code."""
    try:
        return _HARD_CODED_HUMAN_READABLE_SCRIPT_NAMES[code]
    except KeyError:
        load_data()
        return _script_code_to_long_name[code].replace('_', ' ')


def all_scripts():
    """Return a frozenset of all four-letter script codes."""
    load_data()
    return frozenset(_script_code_to_long_name.keys())


_DATA_DIR_PATH = path.join(path.abspath(path.dirname(__file__)),
                           os.pardir, "third_party", "ucd")


def open_unicode_data_file(data_file_name):
    """Opens a Unicode data file.

    Args:
      data_file_name: A string containing the filename of the data file.

    Returns:
      A file handle to the data file.
    """
    return open(path.join(_DATA_DIR_PATH, data_file_name), "r")


def _parse_code_ranges(input_data):
    """Reads Unicode code ranges with properties from an input string.

    Reads a Unicode data file already imported into a string. The format is
    the typical Unicode data file format with either one character or a
    range of characters separated by a semicolon with a property value (and
    potentially comments after a number sign, that will be ignored).

    Example source data file:
      http://www.unicode.org/Public/UNIDATA/Scripts.txt

    Example data:
      0000..001F    ; Common # Cc  [32] <control-0000>..<control-001F>
      0020          ; Common # Zs       SPACE

    Args:
      input_data: An input string, containing the data.

    Returns:
      A list of tuples corresponding to the input data, with each tuple
      containing the beginning of the range, the end of the range, and the
      property value for the range. For example:
      [(0, 31, 'Common'), (32, 32, 'Common')]
    """
    ranges = []
    line_regex = re.compile(
        r"^"  # beginning of line
        r"([0-9A-F]{4,6})"  # first character code
        r"(?:\.\.([0-9A-F]{4,6}))?"  # optional second character code
        r"\s*;\s*"
        r"([^#]+)")  # the data, up until the potential comment
    for line in input_data.split("\n"):
        match = line_regex.match(line)
        if not match:  # Skip lines that don't match the pattern
            continue

        first, last, data = match.groups()
        if last is None:
            last = first

        first = int(first, 16)
        last = int(last, 16)
        data = data.rstrip()

        ranges.append((first, last, data))

    return ranges


def _parse_semicolon_separated_data(input_data):
    """Reads semicolon-separated Unicode data from an input string.

    Reads a Unicode data file already imported into a string. The format is
    the Unicode data file format with a list of values separated by
    semicolons. The number of the values on different lines may be different
    from another.

    Example source data file:
      http://www.unicode.org/Public/UNIDATA/PropertyValueAliases.txt

    Example data:
      sc;  Cher  ; Cherokee
      sc;  Copt  ; Coptic   ; Qaac

    Args:
      input_data: An input string, containing the data.

    Returns:
      A list of lists corresponding to the input data, with each individual
      list containing the values as strings. For example:
      [['sc', 'Cher', 'Cherokee'], ['sc', 'Copt', 'Coptic', 'Qaac']]
    """
    all_data = []
    for line in input_data.split('\n'):
        line = line.split('#', 1)[0].strip()  # remove the comment
        if not line:
            continue

        fields = line.split(';')
        fields = [field.strip() for field in fields]
        all_data.append(fields)

    return all_data


def _load_unicode_data_txt():
    """Load character data from UnicodeData.txt."""
    global _defined_characters
    global _bidi_mirroring_characters

    with open_unicode_data_file("UnicodeData.txt") as unicode_data_txt:
        unicode_data = _parse_semicolon_separated_data(unicode_data_txt.read())

    for line in unicode_data:
        code = int(line[0], 16)
        char_name = line[1]
        general_category = line[2]
        combining_class = int(line[3])

        decomposition = line[5]
        if decomposition.startswith('<'):
            # We only care about canonical decompositions
            decomposition = ''
        decomposition = decomposition.split()
        decomposition = [unichr(int(char, 16)) for char in decomposition]
        decomposition = ''.join(decomposition)

        bidi_mirroring = (line[9] == 'Y')
        if general_category == 'Ll':
          upcode = line[12]
          if upcode:
            upper_case = int(upcode, 16)
            _lower_to_upper_case[code] = upper_case

        if char_name.endswith("First>"):
            last_range_opener = code
        elif char_name.endswith("Last>"):
            # Ignore surrogates
            if "Surrogate" not in char_name:
                for char in xrange(last_range_opener, code+1):
                    _general_category_data[char] = general_category
                    _combining_class_data[char] = combining_class
                    if bidi_mirroring:
                        _bidi_mirroring_characters.add(char)
                    _defined_characters.add(char)
        else:
            _character_names_data[code] = char_name
            _general_category_data[code] = general_category
            _combining_class_data[code] = combining_class
            if bidi_mirroring:
                _bidi_mirroring_characters.add(code)
            _decomposition_data[code] = decomposition
            _defined_characters.add(code)

    _defined_characters = frozenset(_defined_characters)
    _bidi_mirroring_characters = frozenset(_bidi_mirroring_characters)


def _load_scripts_txt():
    """Load script property from Scripts.txt."""
    with open_unicode_data_file("Scripts.txt") as scripts_txt:
        script_ranges = _parse_code_ranges(scripts_txt.read())

    for first, last, script_name in script_ranges:
        for char_code in xrange(first, last+1):
            _script_data[char_code] = _script_long_name_to_code[script_name]


def _load_script_extensions_txt():
    """Load script property from ScriptExtensions.txt."""
    with open_unicode_data_file("ScriptExtensions.txt") as se_txt:
        script_extensions_ranges = _parse_code_ranges(se_txt.read())

    for first, last, script_names in script_extensions_ranges:
        script_set = frozenset(script_names.split(' '))
        for character_code in xrange(first, last+1):
            _script_extensions_data[character_code] = script_set


def _load_blocks_txt():
    """Load block name from Blocks.txt."""
    with open_unicode_data_file("Blocks.txt") as blocks_txt:
        block_ranges = _parse_code_ranges(blocks_txt.read())

    for first, last, block_name in block_ranges:
        for character_code in xrange(first, last+1):
            _block_data[character_code] = block_name


def _load_derived_age_txt():
    """Load age property from DerivedAge.txt."""
    with open_unicode_data_file("DerivedAge.txt") as derived_age_txt:
        age_ranges = _parse_code_ranges(derived_age_txt.read())

    for first, last, char_age in age_ranges:
        for char_code in xrange(first, last+1):
            _age_data[char_code] = char_age


def _load_derived_core_properties_txt():
    """Load derived core properties from Blocks.txt."""
    with open_unicode_data_file("DerivedCoreProperties.txt") as dcp_txt:
        dcp_ranges = _parse_code_ranges(dcp_txt.read())

    for first, last, property_name in dcp_ranges:
        for character_code in xrange(first, last+1):
            try:
                _core_properties_data[property_name].add(character_code)
            except KeyError:
                _core_properties_data[property_name] = {character_code}


def _load_property_value_aliases_txt():
    """Load property value aliases from PropertyValueAliases.txt."""
    with open_unicode_data_file("PropertyValueAliases.txt") as pva_txt:
        aliases = _parse_semicolon_separated_data(pva_txt.read())

    for data_item in aliases:
        if data_item[0] == 'sc': # Script
            code = data_item[1]
            long_name = data_item[2]
            _script_code_to_long_name[code] = long_name
            _script_long_name_to_code[long_name] = code


def _load_bidi_mirroring_txt():
    """Load bidi mirroring glyphs from BidiMirroring.txt."""
    with open_unicode_data_file("BidiMirroring.txt") as bidi_mirroring_txt:
        bmg_pairs = _parse_semicolon_separated_data(bidi_mirroring_txt.read())

    for char, bmg in bmg_pairs:
        char = int(char, 16)
        bmg = int(bmg, 16)
        _bidi_mirroring_glyph_data[char] = bmg
