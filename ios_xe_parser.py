from utils import ReSearcher, Tree, LineParser, splitrange, get_key


def ios_xe_parser(configfile):

    """
    This function parses a Cisco IOS configuration file into a nested
    dictionary. It has the following capabilities:
    - All interfaces items are parsed into key-value pairs using an
      algorithm to determine the key and value parts of the interface items.
    - For specific items, lists are used to store data.
    """

    with open(configfile, 'r') as lines:
        
        match = ReSearcher()
        tree = Tree()

        key_exceptions = ['ip vrf forwarding']
        key_length = {1: ['hold-queue', 'standby', 'channel-group',
                          'description'],
                      2: ['switchport port-security', 'ip', 'spanning-tree',
                          'speed auto', 'srr-queue bandwidth']
        }
        list_items = ['switchport trunk allowed vlan', 'standby',
                      'ip helper-address', 'logging event']
        line_parser = LineParser(list_items, key_exceptions, key_length)

        context = ''
        vlanindex = ''
      
        for line in lines:
            
            if not line.strip(): # skip empty lines
                continue
            line = line.rstrip()
                        
            if match(r'^hostname (.*)', line):
                hostname = format(match.group(1))
                tree['hostname'] = hostname
                     
            elif match(r'^interface (Vlan(\d+))', line):
                context = 'port'
                portindex = format(match.group(1))
                vlanindex = format(match.group(2))
                tree['vlan'][vlanindex] = {}
                line_parser.initialize_lists()
  
            elif match(r'^interface (.*)', line):
                context = 'port'
                portindex = format(match.group(1))
                tree['port'][portindex] = {}
                line_parser.initialize_lists()
 
            elif match(r'^vlan (\d+)$', line):
                context = 'vlan'
                vlanindex = format(match.group(1))
                tree['vlan'][vlanindex] = {}

            elif match(r'^vlan ([0-9,-]+)', line):
                context = 'vlan'
                value = format(match.group(1))
                for raw_vlans in value.split(','):
                    if '-' in raw_vlans:
                        for vlan in splitrange(raw_vlans):
                            tree['vlan'][str(vlan)] = {}
                    else:
                        tree['vlan'][raw_vlans] = {}

            elif context == 'port':

                if match(r'^ no (.*)', line):
                    key = format(match.group(1))
                    value = format(match.group(0))
                    if 'Vlan' in portindex:
                        tree['vlan'][vlanindex][key] = value
                    else:
                        tree['port'][portindex][key] = value

                # interface items are stored with helper class
                elif match('^ .*', line):
                    args = tree, portindex, vlanindex, line
                    tree = line_parser.parse_line(*args)

                elif match(r'!$', line):
                    context = ''

            elif context == 'vlan':

                if match(r'^ name (.*)', line):
                    tree['vlan'][vlanindex]['name'] = format(match.group(1))

                elif match(r'!$', line):
                    context = ''

        return tree
