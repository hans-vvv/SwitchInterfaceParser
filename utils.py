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


class LineParser():

    """
    Helper class to parse interface items. Items which are
    present in list_items are stored in lists.
    With using the _select_key method the following logic is implemented
    to determine which part of an interface item is considered to be a
    key and which part a value.

    1. First portkey_exceptions list is examined. If an interface item
       contains the words found in this list then key = item in the list
       and value = remaining words of the interface item. If an interface
       item is found then the other methods are not considered.
    2. Key_length dict is examined. If interface item contains an item
       found in a list of the dict then corresponding key (i.e. 1 or 2)
       is used to split the item. The key of the item is equal to the
       number of words of the dict key, the rest of the item = value.
       Example: If line = channel-group 2 mode active, then
       key = "channel-group"  and value = "2 mode active". If an interface
       item is found then the last method is not considered.
    3. Default method. Last word of line = value
       and all preceding words = key.
    """

    def __init__(self, list_items, key_exceptions, key_length):
        self.list_items = list_items
        self.key_exceptions = key_exceptions
        self.key_length = key_length

    def initialize_lists(self):
        self.values = [[] for item in self.list_items]

    def _get_index(self, line):
        for index, item in enumerate(self.list_items):
            if line.startswith(item):
                return index

    def _select_key(self, line):
        for key in self.key_exceptions:
            if line.startswith(key):
                return key
        for key_length, items in self.key_length.items():
            for item in items:
                if line.startswith(item):
                    return get_key(line, key_length)
        return get_key(line, len(line.split())-1)
            

    def parse_line(self, tree, portindex, vlanindex, line):

        line = line.lstrip()
        key = self._select_key(line)

        if line.startswith('switchport trunk allowed vlan'):
            index = self._get_index(line)
            for raw_vlans in get_value(key, line).split(','):
                if '-' in raw_vlans:
                    for vlan_id in splitrange(raw_vlans):
                        self.values[index].append(vlan_id)
                else:
                    self.values[index].append(raw_vlans)
            tree['port'][portindex]['vlan_allow_list'] = self.values[index]
            return tree

        for item in self.list_items:
            if line.startswith(item):
                index = self._get_index(line)
                self.values[index].append(get_value(key, line))
                if 'Vlan' in portindex:
                    tree['vlan'][vlanindex][item] = self.values[index]
                else:
                    tree['port'][portindex][item] = self.values[index]
                return tree

        if 'Vlan' in portindex:
            tree['vlan'][vlanindex][key] = get_value(key, line)
        else:
            tree['port'][portindex][key] = get_value(key, line)
        return tree


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
    ex. splitrange('105-107') will return ['105','106','107']
    """

    m = re.search(r'^(\d+)\-(\d+)$', raw_range)
    if m:
        first = int(format(m.group(1)))
        last = int(format(m.group(2)))
        return [str(i) for i in range(first, last+1)]


def xlref(row, column, zero_indexed=True):

    """
    openpyxl helper
    """
    if zero_indexed:
        row += 1
        column += 1
    return get_column_letter(column) + str(row)



