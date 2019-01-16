""" SwitchInterfaceParser script

This script reads interface and vlan configuration parts of Cisco IOS
multilayer switches and prints all items in a single excel sheet. Using excel features
like autofilter you can analyse the (vlan)interface and vlan specific
configuration items.

Multiple switch configurations can be read using the glob module, see main function.
Set the directory where the configurations reside at your needs in the main function
of the script.

Input en output of script uploaded as well.
"""


import re
from collections import defaultdict
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
import glob
import os


def xlref(row, column, zero_indexed=True):
    if zero_indexed:
        row += 1
        column += 1
    return get_column_letter(column) + str(row)


def splitrange(raw_range):
    
    """
    ex. splitrange('105-107') will return ['105','106','107']
    """

    result = []
    
    if  re.search('^(\d+)\-(\d+)$', raw_range):
        match = re.search('^(\d+)\-(\d+)$', raw_range)
        first = int(format(match.group(1)))
        last = int(format(match.group(2)))
        for i in range(first, last+1):
            result.append(str(i))
        return result

    
def get_value(key, item):
    
    """
    key + value = item
    function return value for given key and item
    """
    
    if key.strip() == item.strip():
        return key
    else:
        item = item.lstrip()
        result = re.search('^('+key+')(.*)', item)
        return format(result.group(2)).lstrip()


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


def get_Switch_info(ciscofiles):

    """
    Loads interface and Vlan specific parts of switch configuration
    into python object.

    The following logic is used to determine which part of
    interface item is considered a key and which part a value. A
    set of all found keys will be printed in the first row of each
    tab in the excel sheet. 

    1. First portkey_exceptions list is read. If an interface item
       contains the words found in the list then key = item in the list
       and value = remaining words of the interface item.

    2. Portkeys dict is read. If interface item contains an item found in
       a list of the dict then corresponding key (i.e. 1 or 2) is used to
       split the item. The key of the item is equal to the number of words
       of the dict key, the rest of the item = value.
       Example: If line = channel-group 2 mode active, then key = channel-group
       and value = 2 mode active.

    3. Default. Last word of line = value and all preceding words = key.

    For the following keys, lists are used to store values:
    - switchport trunk allowed vlan (add)
    - standby (HSRP)
    - ip helper-address

    Known Caveats:
    - No support for secundairy ip addresses
    - Only Vlan name is read under VLAN configuration
    
    """


    portkey_exceptions = ['ip vrf forwarding']
    portkeys = { 1: ['hold-queue', 'standby', 'channel-group', 'description'],
                 2: ['switchport port-security', 'ip', 'spanning-tree', 'speed auto', 'srr-queue bandwidth'] }

    switchinfo = defaultdict(dict)
    for ciscoconfig in ciscofiles:
        
       with open(ciscoconfig, 'r') as lines:

            portinfo = defaultdict(dict)
            vlaninfo = defaultdict(dict)
            scanfile = False
            for line in lines:
                
                line = line.rstrip()
                word = line.split()

                if re.search('^interface Vlan(\d+)', line):
                    match = re.search('^interface Vlan(\d+)', line)
                    intf = format(match.group(0))
                    vlan = format(match.group(1))
                    vlaninfo[vlan]['vlan_id'] = vlan
                    scanfile = True
                    standby = []
                    ip_helper = []
                    
                elif re.search('^vlan (\d+)\-(\d+)$', line):
                    match = re.search('^vlan (\d+)\-(\d+)$', line)
                    for vlan in range(int(match.group(1)), (int(match.group(2))+1)):
                        vlaninfo[str(vlan)]['vlan_id'] = str(vlan)

                elif re.search('^vlan (\d+)$', line):
                    match = re.search('^vlan (\d+)$', line)
                    vlan = format(match.group(1))
                    vlaninfo[vlan]['vlan_id'] = vlan

                elif re.search('^interface (.*)' , line):
                    match = re.search('^interface (.*)' , line)
                    intf = format(match.group(1))
                    scanfile = True
                    vlan_allow_list = []
                    standby = []
                    ip_helper = []

                elif re.search('^ name (.*)', line):
                    match = re.search('^ name (.*)', line)
                    vlaninfo[vlan]['name'] = format(match.group(1))

                elif re.search('^ no (.*)', line):
                    match = re.search('^ no (.*)', line)
                    if scanfile:
                        if 'Vlan' in intf:
                            vlaninfo[vlan][format(match.group(1))] = format(match.group(0))
                        else:
                            portinfo[intf][format(match.group(1))] = format(match.group(0))

                elif re.search('^hostname (.*)', line):
                    match = re.search('^hostname (.*)', line)
                    hostname = format(match.group(1))

                elif re.search('^(ip forward-protocol nd|ip classless|ip default-gateway.*)', line):
                    scanfile = False
        
                elif re.search('^ .*', line) and scanfile:
                    line = line.lstrip()
                    found_item = False
                    
                    for key in portkey_exceptions:
                        if key in line:
                            if 'Vlan' in intf:
                                vlaninfo[vlan][key] = get_value(key, line)
                                found_item = True
                            else:
                                portinfo[intf][key] = get_value(key, line)
                                found_item = True

                    for key_length in sorted(portkeys):
                        if not found_item:
                            for item in portkeys[key_length]:
                                if item in line:
                                    if 'standby' in line:
                                        if 'Vlan' in intf:
                                            standby.append(get_value(get_key(line, key_length), line))
                                            vlaninfo[vlan]['standby'] = ','.join(standby)
                                            found_item = True
                                        else:
                                            standby.append(get_value(get_key(line, key_length), line))
                                            portinfo[intf]['standby'] = ','.join(standby)
                                            found_item = True
                                    elif 'ip helper-address' in line:
                                        if 'Vlan' in intf:
                                            ip_helper.append(get_value(get_key(line, key_length), line))
                                            vlaninfo[vlan]['ip helper-address'] = ','.join(ip_helper)
                                            found_item = True
                                        else:
                                            ip_helper.append(get_value(get_key(line, key_length), line))
                                            portinfo[intf]['ip helper-address'] = ','.join(ip_helper)
                                            found_item = True
                                    elif 'Vlan' in intf:
                                        vlaninfo[vlan][get_key(line, key_length)] = get_value(get_key(line, key_length), line)
                                        found_item = True
                                    else:
                                        portinfo[intf][get_key(line, key_length)] = get_value(get_key(line, key_length), line)
                                        found_item = True

                    if not found_item:
                        if 'switchport trunk allowed vlan' in line:
                            for raw_vlans in get_value(get_key(line, len(word)-1), line).split(','):
                                if '-' in raw_vlans:
                                    for vlan in splitrange(raw_vlans):
                                        vlan_allow_list.append(vlan)
                                else:
                                    vlan_allow_list.append(raw_vlans)
                            portinfo[intf]['vlan_allow_list'] = ','.join(vlan_allow_list)
                        elif 'Vlan' in intf:
                            vlaninfo[vlan][get_key(line, len(word)-1)] = get_value(get_key(line, len(word)-1), line)
                        else:
                            portinfo[intf][get_key(line, len(word)-1)] = get_value(get_key(line, len(word)-1), line)
        
            switchinfo[hostname]['portinfo'] = portinfo
            switchinfo[hostname]['vlaninfo'] = vlaninfo

    return switchinfo


def info_to_xls(switchinfo):

    """
    Function print Switchinfo dictionaty to excel file. Vlan
    are port info are printed in seperated tabs.
    """

    # Calculate list of keys to be present in Excel sheets
    vlankeys = []
    portkeys = []

    for hostname in switchinfo:
        for vlanid in switchinfo[hostname]['vlaninfo']:
            for key in switchinfo[hostname]['vlaninfo'][vlanid]:
                vlankeys.append(key)

    for hostname in switchinfo:
        for intf in switchinfo[hostname]['portinfo']:
            for key in switchinfo[hostname]['portinfo'][intf]:
                portkeys.append(key)

    vlankeys = sorted(set(vlankeys))
    portkeys = sorted(set(portkeys))
    vlankeys.remove('vlan_id')
    vlankeys.remove('name')
    portkeys.remove('description')
    vlankeys.insert(0, 'name')
    portkeys.insert(0, 'description')
   
    wb = Workbook()
    ws = wb.create_sheet("Vlaninfo", 0)
    ws = wb.create_sheet("Portinfo", 0)
    
    ws = wb['Vlaninfo']

    count_vlan_row = 0
    ws[xlref(0, 0)] = 'hostname'
    ws[xlref(0, 1)] = 'vlan_id'
    for count, vlanitem in enumerate(vlankeys):
            ws[xlref(0, count+2)] = vlanitem
             
    for hostname in switchinfo:
        for vlan in switchinfo[hostname]['vlaninfo']:
            ws[xlref(count_vlan_row+1, 0)] = hostname
            ws[xlref(count_vlan_row+1, 1)] = vlan

            for count_col, vlanitem in enumerate(vlankeys):
                ws[xlref(count_vlan_row+1, count_col+2)] = switchinfo[hostname]['vlaninfo'][vlan].get(vlankeys[count_col], '')
            count_vlan_row +=1

    ws = wb['Portinfo']

    count_port_row = 0
    ws[xlref(0, 0)] = 'hostname'
    ws[xlref(0, 1)] = 'interface'
    for count, portitem in enumerate(portkeys):
            ws[xlref(0, count+2)] = portitem

    for hostname in switchinfo.keys():
        for intf in switchinfo[hostname]['portinfo']:
            ws[xlref(count_port_row+1, 0)] = hostname
            ws[xlref(count_port_row+1, 1)] = intf

            for count_col, portitem in enumerate(portkeys):
                ws[xlref(count_port_row+1, count_col+2)] = switchinfo[hostname]['portinfo'][intf].get(portkeys[count_col], '')
            count_port_row +=1
        
    wb.save('result.xlsx')


def main():
    
    #os.chdir('C:/Users/Hans/Desktop/GIT/SwitchInterfaceParser')
    
    ciscofiles = []
    for file in glob.glob('*.txt'):
        ciscofiles.append(file)
        
    # Retrieve interface and vlan info from configuration file and store in switchinfo object.
    switchinfo = get_Switch_info(ciscofiles)
        
    # Print Switchinfo object in excel file.
    info_to_xls(switchinfo)


if __name__ == "__main__":
    main()

    

    

