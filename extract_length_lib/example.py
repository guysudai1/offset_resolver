import pymspdb as pdb
from pprint import pprint 

def main():
    dict_hey = pdb.get_structure("DRIVER_OBJECT")
    pprint(dict_hey, sort_dicts=True)
    
if __name__ == "__main__":
    main()