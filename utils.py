import re
import os
import json
from openpyxl.utils import get_column_letter

class ReSearcher():
    
    """
    Helper  to enable evaluation
    and regex formatting in a single line
    """
    
    match = None

    def __call__(self, pattern, string):
        self.match = re.search(pattern, string)
        return self.match

    def __getattr__(self, name):
        return getattr(self.match, name)


class Tree(dict):
    """ Autovivificious dictionary """
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value

    def __str__(self):
        """ Serialize dictionary to JSON formatted string with indents """
        return json.dumps(self, indent=4)


def get_value(key, item):

    """
    key + value = interface item
    function returns value for given key and item
    """

    if key.strip() == item.strip():
        return key
    else:
        item = item.lstrip()
        result = re.search('^('+key+')(.*)', item)
        value = format(result.group(2)).lstrip()
        return value
    

def get_key(item, key_length):

    """
    key + value = item
    number of words of key = key_length
    function returns key
    """

    word = item.strip().split()
    if key_length == 0: # fix
        return item
    elif len(word) == key_length:
        return item
    else:
        return ' '.join(word[0:key_length])


def splitrange(raw_range):

    """
    '1,2,4-6' returns ['1','2','4','5','6']
    'none'    returns ['None']
    """

    m = re.search(r'^(\d+)\-(\d+)$', raw_range)
    if m:
        first = int(format(m.group(1)))
        last = int(format(m.group(2)))
        return [str(i) for i in range(first, last+1)]

    m = re.search(r'[\d+,-]+', raw_range)
    if m:
        result = []
        for raw_element in format(m.group(0)).split(','):
            if '-' in raw_element:
                for element in splitrange(raw_element):
                    result.append(element)
            else:
                result.append(raw_element)
        return result

    m = re.search(r'^none$', raw_range)
    if m:        
        return ['None']


def xlref(row, column, zero_indexed=True):

    """
    openpyxl helper
    """
    if zero_indexed:
        row += 1
        column += 1
    return get_column_letter(column) + str(row)
