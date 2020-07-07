# Offset resolver
This github project is meant to satisfy a need I faced in my Low-Level adventures. I have found no great place that shows offsets for structures, so I have decided to create one myself. (Intended to support winapi type structs, and currently only supports windows)

## Installation
Clone the repository:
```
git clone https://github.com/guysudai1/offset_resolver.git
```
Install rustup:
```
https://rustup.rs/
```
Build the project using the batch script:
```
install.bat
```
Install the required packages:
```
pip install -r requirements.txt
```
Launch the program (Insert struct definition at line *25*):
```
python resolve_structs.py
```
Enjoy :)

## Usage
```
usage: resolve_structs.py [-h] [--bits {64,32}] [--length LENGTH] [--if IF] [--of OF] [--unicode] [--quiet]
                          [--dlls DLLS]

This program takes in a gross structure => prettifies it and adds offsets :).

optional arguments:
  -h, --help            show this help message and exit
  --bits {64,32}, -B {64,32}
                        Bits (64/32)
  --length LENGTH, -L LENGTH
                        Begin length from specific number.
  --if IF               File to get structure from (can also insert structure into top multiline string)
  --of OF               File to write structure from (default is stdout)
  --unicode, -U         Set this value to support unicode (TCHAR, TBYTE = WCHAR).
  --quiet, -q           Set this value to get only the output, no prints.
  --dlls DLLS, -d DLLS  A list of DLL files from C:/Windows/System32 separated by a comma
```


## TODO
- [x] Support basic winapi types.
- [x] Support 64 bit / 32 bit versions of basic types.
- [x] Support unicode/ascii versions (basic types).
- [x] Add support for reading from PDB files.
- [x] Add more customization options.
- [x] Add support for pulling PDB files from microsoft's symbol servers.
- [ ] Refractor code.
