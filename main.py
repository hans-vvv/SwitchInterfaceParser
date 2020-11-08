import json
from glob import glob
from multiprocessing import Pool
from xls_writer import xls_writer
from ios_xe_parser import ios_xe_parser



def main():

    config_files = [configfile for configfile in glob('*-cfg.txt')]

    # list of Tree objects
    #configs = [ios_xe_parser(config_file) for config_file in config_files]
    pool = Pool()
    configs = pool.map(ios_xe_parser, config_files)
     
    with open('configs.json', 'w') as f:
        json.dump(configs, f, indent=4)

    xls_writer(configs)

if __name__ == '__main__':
    main()   


