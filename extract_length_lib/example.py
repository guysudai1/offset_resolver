import pymspdb as pdb
from pprint import pprint 

def main():
    dict_hey = pdb.extract_symbols("PEB")
    pprint(dict_hey, sort_dicts=True)
    
if __name__ == "__main__":
    main()