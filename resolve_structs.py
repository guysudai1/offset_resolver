from pathlib import Path
import re, os, pefile, struct, argparse, pyastyle, httplib2
from enum import IntEnum
from collections import deque, namedtuple
from os.path import exists
from ctypes import *
import pymspdb as pdb
from time import sleep

class type_enum(IntEnum):
	"""
	This enum describes variables in the struct, 
	whether they are structs / unions / regular variables
	"""
	TYPE_REGULAR = 0
	TYPE_UNION = 1
	TYPE_STRUCT = 2


# Insert struct definition here
# Insert struct definition here
# Insert struct definition here
# Insert struct definition here
# Insert struct definition here
default_struct = """
"""

# Based on c++ variable naming rules. (not all are used,
# i'm keeping these in here incase I want to use them later.
# They obviously don't work super well, but they work well enough)
variable_capture_regex = r"[A-Za-z_]([A-Za-z0-9_]{0,254})$" 
union_capture_regex = r"union[ ]{0,}(\[\[[a-zA-Z0-9_]+\]\][ ]{1,}){0,}(\[\[[a-zA-Z0-9_]+\]\]){0,1}[a-zA-Z_]{0,1}[a-zA-Z_0-9]{0,}[ ]{0,}{"
struct_capture_regex = r"^struct[ ]{1,}[a-zA-Z_]{0,1}[a-zA-Z_0-9]{0,}[ ]{0,}{"

# Dictionary for 64 bit compiler options
basic_types_64_bit = {
	"LARGE_INTEGER": 8,
	"ULARGE_INTEGER": 8,
	"CSHORT": 2,
	"ATOM": 2,
	"BOOL": 1,
	"BOOLEAN": 1,
	"BYTE": 1,
	"CCHAR": 1,
	"CHAR": 1,
	"COLORREF": 4,
	"DWORD": 4,
	"DWORDLONG": 8,
	"DWORD_PTR": 8,
	"DWORD32": 4,
	"DWORD64": 8,
	"FLOAT": 4,
	"HACCEL": 8,
	"HALF_PTR": 8,
	"HANDLE": 8,
	"HBITMAP": 8,
	"HBRUSH": 8,
	"HCOLORSPACE": 8,
	"HCONV": 8,
	"HCONVLIST": 8,
	"HCURSOR": 8,
	"HDC": 8,
	"HDDEDATA": 8,
	"HDESK": 8,
	"HDROP": 8,
	"HDWP": 8,
	"HENHMETAFILE": 8,
	"HFILE": 8,
	"HFONT": 8,
	"HGDIOBJ": 8,
	"HGLOBAL": 8,
	"HHOOK": 8,
	"HICON": 8,
	"HINSTANCE": 8,
	"HKEY": 8,
	"HKL": 8,
	"HLOCAL": 8,
	"HMENU": 8,
	"HMETAFILE": 8,
	"HMODULE": 8,
	"HMONITOR": 8,
	"HPALETTE": 8,
	"HPEN": 8,
	"HRESULT": 8,
	"HRGN": 8,
	"HRSRC": 8,
	"HSZ": 8,
	"HWINSTA": 8,
	"HWND": 8,
	"INT": 4,
	"INT_PTR": 8,
	"INT8": 1,
	"INT16": 2,
	"INT32": 4,
	"INT64": 8,
	"LANGID": 2,
	"LCID": 4,
	"LCTYPE": 4,
	"LGRPID": 4,
	"LONG": 4,
	"LONGLONG": 8,
	"LONG_PTR": 8,
	"LONG32": 4,
	"LONG64": 8,
	"LPARAM": 8,
	"LPBOOL": 8,
	"LPBYTE": 8,
	"LPCOLORREF": 8,
	"LPCSTR": 8,
	"LPCTSTR": 8,
	"LPCVOID": 8,
	"LPCWSTR": 8,
	"LPDWORD": 8,
	"LPHANDLE": 8,
	"LPINT": 8,
	"LPLONG": 8,
	"LPSTR": 8,
	"LPTSTR": 8,
	"LPVOID": 8,
	"LPWORD": 8,
	"LPWSTR": 8,
	"LRESULT": 8,
	"PBOOL": 8,
	"PBOOLEAN": 8,
	"PBYTE": 8,
	"PCHAR": 8,
	"PCSTR": 8,
	"PCTSTR": 8,
	"PCWSTR": 8,
	"PDWORD": 8,
	"PDWORDLONG": 8,
	"PDWORD_PTR": 8,
	"PDWORD32": 8,
	"PDWORD64": 8,
	"PFLOAT": 8,
	"PHALF_PTR": 8,
	"PHANDLE": 8,
	"PHKEY": 8,
	"PINT": 8,
	"PINT_PTR": 8,
	"PINT8": 8,
	"PINT16": 8,
	"PINT32": 8,
	"PINT64": 8,
	"PLCID": 8,
	"PLONG": 8,
	"PLONGLONG": 8,
	"PLONG_PTR": 8,
	"PLONG32": 8,
	"PLONG64": 8,
	"POINTER_32": 4,
	"POINTER_64": 8,
	"POINTER_SIGNED": 8,
	"POINTER_UNSIGNED": 8,
	"PSHORT": 8,
	"PSIZE_T": 8,
	"PSSIZE_T": 8,
	"PSTR": 8,
	"PTBYTE": 8,
	"PTCHAR": 8,
	"PTSTR": 8,
	"PUCHAR": 8,
	"PUHALF_PTR": 8,
	"PUINT": 8,
	"PUINT_PTR": 8,
	"PUINT8": 8,
	"PUINT16": 8,
	"PUINT32": 8,
	"PUINT64": 8,
	"PULONG": 8,
	"PULONGLONG": 8,
	"PULONG_PTR": 8,
	"PULONG32": 8,
	"PULONG64": 8,
	"PUSHORT": 8,
	"PVOID": 8,
	"PWCHAR": 8,
	"PWORD": 8,
	"PWSTR": 8,
	"QWORD": 8,
	"SC_HANDLE": 8,
	"SC_LOCK": 8,
	"SERVICE_STATUS_HANDLE": 8,
	"SHORT": 2,
	"SIZE_T": 8,
	"SSIZE_T": 8,
	"TBYTE": 2, # TODO: Support unicode / not unicode
	"TCHAR": 2, # TODO: Support unicode / not unicode
	"UCHAR": 1,
	"UHALF_PTR": 4,
	"UINT": 4,
	"UINT_PTR": 8,
	"UINT8": 1,
	"UINT16": 2,
	"UINT32": 4,
	"UINT64": 8,
	"ULONG": 4,
	"ULONGLONG": 8,
	"ULONG_PTR": 8,
	"ULONG32": 4,
	"ULONG64": 8,
	"UNICODE_STRING": 12, # Dependant on struct elements
	"USHORT": 2,
	"USN": 8,
	"WCHAR": 2,
	"WORD": 2,
	"WPARAM": 8
}

basic_types_32_bit = {
	"LARGE_INTEGER": 8,
	"ULARGE_INTEGER": 8,
	"CSHORT": 2,
	"ATOM": 2,
	"BOOL": 4,
	"BOOLEAN": 1,
	"BYTE": 1,
	"CCHAR": 1,
	"CHAR": 1,
	"COLORREF": 4,
	"DWORD": 4,
	"DWORDLONG": 8,
	"DWORD_PTR": 4,
	"DWORD32": 4,
	"DWORD64": 8,
	"FLOAT": 4,
	"HACCEL": 4,
	"HALF_PTR": 2,
	"HANDLE": 4,
	"HBITMAP": 4,
	"HBRUSH": 4,
	"HCOLORSPACE": 4,
	"HCONV": 4,
	"HCONVLIST": 4,
	"HCURSOR": 4,
	"HDC": 4,
	"HDDEDATA": 4,
	"HDESK": 4,
	"HDROP": 4,
	"HDWP": 4,
	"HENHMETAFILE": 4,
	"HFILE": 4,
	"HFONT": 4,
	"HGDIOBJ": 4,
	"HGLOBAL": 4,
	"HHOOK": 4,
	"HICON": 4,
	"HINSTANCE": 4,
	"HKEY": 4,
	"HKL": 4,
	"HLOCAL": 4,
	"HMENU": 4,
	"HMETAFILE": 4,
	"HMODULE": 4,
	"HMONITOR": 4,
	"HPALETTE": 4,
	"HPEN": 4,
	"HRESULT": 4,
	"HRGN": 4,
	"HRSRC": 4,
	"HSZ": 4,
	"HWINSTA": 4,
	"HWND": 4,
	"INT": 4,
	"INT_PTR": 4,
	"INT8": 1,
	"INT16": 2,
	"INT32": 4,
	"INT64": 8,
	"LANGID": 2,
	"LCID": 4,
	"LCTYPE": 4,
	"LGRPID": 4,
	"LONG": 4,
	"LONGLONG": 8,
	"LONG_PTR": 4,
	"LONG32": 4,
	"LONG64": 8,
	"LPARAM": 4,
	"LPBOOL": 4,
	"LPBYTE": 4,
	"LPCOLORREF": 4,
	"LPCSTR": 4,
	"LPCTSTR": 4,
	"LPCVOID": 4,
	"LPCWSTR": 4,
	"LPDWORD": 4,
	"LPHANDLE": 4,
	"LPINT": 4,
	"LPLONG": 4,
	"LPSTR": 4,
	"LPTSTR": 4,
	"LPVOID": 4,
	"LPWORD": 4,
	"LPWSTR": 4,
	"LRESULT": 4,
	"PBOOL": 4,
	"PBOOLEAN": 4,
	"PBYTE": 4,
	"PCHAR": 4,
	"PCSTR": 4,
	"PCTSTR": 4,
	"PCWSTR": 4,
	"PDWORD": 4,
	"PDWORDLONG": 4,
	"PDWORD_PTR": 4,
	"PDWORD32": 4,
	"PDWORD64": 4,
	"PFLOAT": 4,
	"PHALF_PTR": 4,
	"PHANDLE": 4,
	"PHKEY": 4,
	"PINT": 4,
	"PINT_PTR": 4,
	"PINT8": 4,
	"PINT16": 4,
	"PINT32": 4,
	"PINT64": 4,
	"PLCID": 4,
	"PLONG": 4,
	"PLONGLONG": 4,
	"PLONG_PTR": 4,
	"PLONG32": 4,
	"PLONG64": 4,
	"POINTER_32": 4,
	"POINTER_64": 4,
	"POINTER_SIGNED": 4,
	"POINTER_UNSIGNED": 4,
	"PSHORT": 4,
	"PSIZE_T": 4,
	"PSSIZE_T": 4,
	"PSTR": 4,
	"PTBYTE": 4,
	"PTCHAR": 4,
	"PTSTR": 4,
	"PUCHAR": 4,
	"PUHALF_PTR": 4,
	"PUINT": 4,
	"PUINT_PTR": 4,
	"PUINT8": 4,
	"PUINT16": 4,
	"PUINT32": 4,
	"PUINT64": 4,
	"PULONG": 4,
	"PULONGLONG": 4,
	"PULONG_PTR": 4,
	"PULONG32": 4,
	"PULONG64": 4,
	"PUSHORT": 4,
	"PVOID": 4,
	"PWCHAR": 4,
	"PWORD": 4,
	"PWSTR": 4,
	"QWORD": 8,
	"SC_HANDLE": 4,
	"SC_LOCK": 4,
	"SERVICE_STATUS_HANDLE": 4,
	"SHORT": 2,
	"SIZE_T": 4,
	"SSIZE_T": 4,
	"TBYTE": 2,
	"TCHAR": 2,
	"UCHAR": 1,
	"UHALF_PTR": 2,
	"UINT": 4,
	"UINT_PTR": 4,
	"UINT8": 1,
	"UINT16": 2,
	"UINT32": 4,
	"UINT64": 8,
	"ULONG": 4,
	"ULONGLONG": 8,
	"ULONG_PTR": 4,
	"ULONG32": 4,
	"ULONG64": 8,
	"UNICODE_STRING": 4,
	"USHORT": 2,
	"USN": 8,
	"WCHAR": 2,
	"WORD": 2,
	"WPARAM": 4
}


def get_current_file_gen(starting_address):
	"""
	This function is a generator yielding a path from the start path
	each time (recursively)

	Args:
		starting_address (Path): start path
	"""
	for file_name in starting_address.rglob("*.pdb"):
		yield file_name


def remove_comments(middle_struct):
	"""
	This function removes the comments from the structure.

	Args:
		middle_struct (str struct): Struct described by a string
	"""
	end_string, found_index = "", 0

	# Multi-line comments
	while (new_found_index := middle_struct.find("/*", found_index)) != -1:
		end_string += middle_struct[found_index:new_found_index]
		found_index = middle_struct.find("*/", new_found_index + 2) + 2

	# Add remainder of string
	end_string += middle_struct[found_index:]
	end_string = "\n".join(
		current_line[:
						(found_index
						if ((found_index := current_line.find("//")) != -1)
						else len(current_line)
						)
					]
					for line in end_string.split("\n")
					if (current_line := line.strip()))
	return end_string


def get_closing_curly_brace(string):
	"""
	This function takes in a string with curly braces
    (e.g struct { INT helloWorld; }), and finds the index of the
	last closing bracket. 

	Args:
		string (str): String with curly brackets

	Returns:
		int: index of the closing curly bracket
	"""    
	queue = deque()

	def __get_closing_curly_brace(string):
		for index, char in enumerate(string):
			if char == "{":
				queue.append(1)
			elif char == "}":
				queue.pop()
				if not queue:
					return index

	# Detects beginning of curly braces
	string_after_bracket = string[string.find("{"):]
	return string.find("{") + __get_closing_curly_brace(string_after_bracket)


def type_extract_gen(structure_middle):
	"""
	This function is a generator, that takes in a structure and yields 
	a type each iteration (types are regular types / unions / structs)

	Args:
		structure_middle (str): Structure to parse

	Yields:
		type_str: Type of the variable as a string (in regular mode, the
				  type_str variable includes the variable name and type)
		type_enum: Type of the variable (regular / union / struct)
	"""    
 
	uncommented_structure = remove_comments(structure_middle)

	# Allows to acquire unions / structs (pretty ugly, will work to make it better)
	current_index = 0
	closing_index = -1
	for line in uncommented_structure.split(";"):
		
		# Check if already parsed struct / union
		current_line_length = len(line) + 1  # ";"
		if closing_index >= current_index:
			current_index += current_line_length
			continue

		line = line.strip()

		# Check if the variable is a union / struct
		if (union_match := re.match(union_capture_regex, line)) is not None\
				or re.match(struct_capture_regex, line) is not None:

			# Acquire entire struct / union
			closing_index = get_closing_curly_brace(uncommented_structure[current_index:])
			closing_index = current_index + closing_index + 1
			union_struct = uncommented_structure[current_index:closing_index].strip() + ";"

			type = type_enum.TYPE_UNION if union_match is not None else type_enum.TYPE_STRUCT
			yield (union_struct, type)

		else:
			variable_match = re.search(variable_capture_regex, line)
			# print(repr(line), variable_match)
			if variable_match is None:
				continue
			var_type = line[:variable_match.start(0)]
			var_name = line[variable_match.start(0):]
			yield ((var_type, var_name), type_enum.TYPE_REGULAR)

		current_index += current_line_length


def parse_struct(struct):
	"""
	Returns (begin, middle, end) substring of struct

	Args:
		struct (str): string representation of a C++ struct (winapi style)

	Example:
	typedef struct _hello_world {
		abcdef xyz;
	}; => (typedef struct _hello_world {, abcdef xyz;, };)
	"""
	beginning_index = struct.find("{") + 1
	ending_index = struct.rfind("}")

	beginning = struct[:beginning_index].replace("\n", " ")
	end = struct[ending_index:].replace("\n", " ")
	middle = struct[beginning_index:ending_index]

	return beginning, middle, end


def get_type_length(type_str: str, options={}):
	"""
	This function takes in a type and returns its size

	Args:
		type_str (str): Type to get length of
		type (type_enum): Actual type of the type str
		options (dictionary): Options that decide the custom properties. 
	"""

	# Remove CONST from type
	type_str = type_str.strip().upper()
	# print(f"Acquiring type for {type_str}...", end="")
	if type_str.startswith("CONST"):
		type_str = type_str[len("CONST"):].strip()
	
	# Check if type is pointer
	if type_str[-1] == "*" or type_str.startswith("LP"):
		length = 4 if (options.bits == 32) else 8
	elif options.bits == 64 and type_str in basic_types_64_bit:
		length = basic_types_64_bit[type_str]
	elif options.bits == 32 and type_str in basic_types_32_bit:
		length = basic_types_32_bit[type_str]
	elif (type_size := automatically_resolve_struct(type_str, length_type=True)) is not None:
		length = type_size
	else:
		if type_str.startswith("P"):
			sleep(0.9)
			print()
			print(f"[++] Detecting pointer variable? Write Y/Yes if {type_str} is indeed a pointer.")
			confirmation = input().lower().strip()
			print(f"Confirmation: {repr(confirmation)}")
			if confirmation == "y" or confirmation == "yes":
				length = 4 if (options.bits == 32) else 8	
				return length

		print(f"Could not find length for type {type_str}. Type 0 if you don't want to insert the length.\nPlease write the length here: ")
		try:
			length = int(input())
		except ValueError:
			length = 0
			
	# if length != 0:
	# 	print(f"FOUND LENGTH {length}", end="\n")

	return length


def get_largest_element_in_union(union, options={}):
	"""
	This function gets the union's size
	(Pretty similiar to the type gen function)
	Args:
		union (str): union to acquire the largest elements
	"""    
	_, middle, _ = parse_struct(union)
	
	# Variable to acquire unions / structs (Will work on prettier way, no worries :P)
	current_index = 0
	closing_index = -1

	# Max element size
	max_element = -1
	for line in middle.split(";"):
		# Check if already parsed
		current_line_length = len(line) + 1  # ";"
		if closing_index >= current_index:
			current_index += current_line_length
			continue
		
		line = line.strip()
  
		# Check if variable is a union or struct
		if (union_match := re.match(union_capture_regex, line)) is not None\
				or re.match(struct_capture_regex, line) is not None:
        
			closing_index = get_closing_curly_brace(middle[current_index:])
			closing_index = current_index + closing_index + 1
			union_struct = middle[current_index:closing_index].strip() + ";"

			type_size = get_largest_element_in_union(union_struct, options) if union_match is not None\
						else resolve_struct(union_struct, options).len
			if (type_size > max_element):
				max_element = type_size
		else:
			variable_match = re.search(variable_capture_regex, line)
			# print(repr(line), variable_match)
			if variable_match is None:
				continue
			var_type = line[:variable_match.start(0)].strip()
			type_size = get_type_length(var_type, options)
			if (type_size > max_element):
				max_element = type_size
		 
		current_index += current_line_length 
	return max_element

def add_length_to_type(prev_length: int, type_str: str, type: type_enum, options={}):
	"""
	This function takes the variable type, previous length, variable type, and options in order
	to append offset information to the type string provided.
 
	Args:
		prev_length(int): current offset inside struct
		type_str (str): Type to get length of
		type (type_enum): Actual type of the type str
		options (dictionary): Options that decide the custom properties. 

	Example: 
		struct {
		INT* abc;                      
		INT* hello;                   
		struct {
			PVOID this_is_cool;         
			char*   this_is_cool_2;       
		};
		PVOID* hey;                      
		}; 
		-----> 
		struct { (64 bit)
		INT* abc;                         // 8    : 0x8
		INT* hello;                       // 16   : 0x10
		struct {
			PVOID this_is_cool;           // 24   : 0x18
			char*   this_is_cool_2;       // 32   : 0x20 
		};
		PVOID* hey;                       // 40   : 0x28
		};             
	"""
	if type == type.TYPE_REGULAR:
		length = get_type_length(type_str[0], options) + prev_length
		error = "**Could not find length**" if length == prev_length else ""
		return (f"{''.join(type_str)};\t// {str(length).zfill(4)}: 0x{hex(length)[2:].zfill(4)} {error}"), length
	elif type == type.TYPE_STRUCT:
		# print(type_str)
		options.length = prev_length
		return resolve_struct(type_str, options) 
	elif type == type.TYPE_UNION:
		largest_in_union = get_largest_element_in_union(type_str, options) + prev_length
		return (f"{type_str}\t// {str(largest_in_union).zfill(4)}: 0x{hex(largest_in_union)[2:].zfill(4)}"), largest_in_union
	return '**Could not find length**', prev_length


def get_guid(path):
	try:
		dll = pefile.PE(path)
		sigs = []
		for i in range(len(dll.DIRECTORY_ENTRY_DEBUG)):
			if (dll.DIRECTORY_ENTRY_DEBUG[i].struct.Type == 2):
				rva = dll.DIRECTORY_ENTRY_DEBUG[i].struct.AddressOfRawData
				tmp = ''
				tmp += '%0.*X' % (8, dll.get_dword_at_rva(rva+4))
				tmp += '%0.*X' % (4, dll.get_word_at_rva(rva+4+4))
				tmp += '%0.*X' % (4, dll.get_word_at_rva(rva+4+4+2))
				x = dll.get_word_at_rva(rva+4+4+2+2)
				tmp += '%0.*X' % (4, struct.unpack('<H',struct.pack('>H',x))[0])
				x = dll.get_word_at_rva(rva+4+4+2+2+2)
				tmp += '%0.*X' % (4, struct.unpack('<H',struct.pack('>H',x))[0])
				x = dll.get_word_at_rva(rva+4+4+2+2+2+2)
				tmp += '%0.*X' % (4, struct.unpack('<H',struct.pack('>H',x))[0])
				x = dll.get_word_at_rva(rva+4+4+2+2+2+2+2)
				tmp += '%0.*X' % (4, struct.unpack('<H',struct.pack('>H',x))[0])
				tmp += '%0.*X' % (1, dll.get_word_at_rva(rva+4+4+2+2+2+2+2+2))

				sigs.append(tmp)
		return sigs
	except AttributeError as e:
		print('Error appends during %s parsing' % dll_path)
	
def download_pdb(guid, dll_name_no_ext):
	url = "http://msdl.microsoft.com/download/symbols/%s.pdb/%s/%s.pdb" % (dll_name_no_ext, guid, dll_name_no_ext)
	conn = httplib2.Http()
	headers = {"User-Agent": "Microsoft-Symbol-Server/6.12.0002.633"}
	response, content = conn.request(url, "GET", headers=headers)

	if response.status == 200:
		with open(f"resources/{dll_name_no_ext + '_' + guid}.pdb", 'wb') as pdb_file:
			pdb_file.write(content)
		return True
	else:
		print(f"Couldn't download {dll_name_no_ext}.pdb!")
		return False

def pull_pdb_files(dll_file_name: str, bitness: int):
	print("")
	for dll in dll_file_name:
		if bitness == 64:
			download_from_path = f"c:\\Windows\\System32\\{dll}"
		else:
			download_from_path = f"c:\\Windows\\SysWOW64\\{dll}"

		dll_no_ext = dll[:dll.find(".")]
		# download_cmd = f"symchk.exe /r {download_from_path} /s SRV*{download_to_path}*https://msdl.microsoft.com/download/symbols"
		guids = get_guid(download_from_path)
		for guid in guids:
			download_to_path = Path.cwd() / Path("resources") / Path(dll_no_ext + "_" + guid + ".pdb")
			print(f"{dll} GUID: {guid}")
			print("Downloading PDB file, this could take some time. Please hold on...")
			if exists(download_to_path):
				print(f"PDB File {download_to_path} already exists, not download again and contiuing...\n")
				continue
			if download_pdb(guid, dll_no_ext):
				print(f"\"{download_from_path}\" => \"{download_to_path}\"")
			print("")

	print("Finished pulling pdb files.")

def resolve_struct(struct, options={}):
	"""
	This function takes a structure and a set of predefined options and returns the structure
	with proper offsets in the structure.
	It first parses the structure in order to remove all comments (for easier parsing later on),
	then parses the data types, and tries to hunt the data types in winapi's header files if
	it doesn't succeed it tries to guess and asks the user if the guess is correct.

	Args:
		struct (str): Desired structure to resolve
		options (dict, optional): Includes multiple options (64/32 bit, header files location, ... more to come). Defaults to {}.
	"""
	beginning, middle, end = parse_struct(struct)
	# Test path to headers
	# path_to_headers = Path.home() / "Desktop/headers/"  # options[path]

	offsets = []
	# Acquire all data types (string=data type, type=REGULAR TYPE/UNION/STRUCT)
	prev_length = options.length
	for string, type in type_extract_gen(middle):
		current_string, prev_length = add_length_to_type(prev_length, string, type, options)
		offsets.append(current_string)
	
	StructResolveTuple = namedtuple("Struct", ["struct", "len"])
	# print(beginning + "\n" + "\n".join(offsets) + end)
	return StructResolveTuple(beginning + "\n" + "\n".join(offsets) + "\n" + end, prev_length)
	
	# Generator to loop over headers recursively
	# current_file_genc = get_current_file_gen(path_to_headers)
	"""
	for current_file in current_file_gen:
		with open(current_file, "r") as header_file:
			# parse_file_conditions(current_file, )
			print(get_all_typedefs())
	# Try to look for struct in winapi pdb
	"""
	# print("Begin: ", beginning, "Middle: ", middle, "End: ", end)


def stringify_dict(struct_name, pdb_dict):
	count = 0
	nl = "\n"
	tab_format = "\t"
	put_only_one_semicolon = lambda x: x.strip(";") + ";"
	return f"struct {struct_name} {{ {nl}{'{}'.format(nl).join(['{} {}// {}: 0x{}'.format(put_only_one_semicolon(y), tab_format, str(x).zfill(4), hex(x)[2:].zfill(4)) for x,y in pdb_dict.items()])} {nl}}}"

		
def automatically_resolve_struct(struct_name: str, length_type: bool):
	dll_list = get_current_file_gen(Path("resources"))
	struct_dict = {}
	for dll in dll_list:
		if length_type:
			struct_dict = pdb.get_structure_length(struct_name, str(dll), struct_dict)
		else:
			struct_dict = pdb.get_structure(struct_name, str(dll), struct_dict)

	if not struct_dict:
		if struct_name.startswith("LP"):
			new_name = struct_name[2:]
		elif struct_name.startswith("P"):
			new_name = struct_name[1:]
		elif struct_name.startswith("_"):
			print(f" [--] Can't find struct with name {struct_name}... Trying {struct_name.strip('_')}...", end="")
			new_name = struct_name.strip("_")
		else:
			print(f" [--] Can't find struct with name {struct_name} automatically.")
			return

		print(f" [--] Can't find struct with name {struct_name}... Trying {new_name}...", end="")
		dll_list = get_current_file_gen(Path("resources"))
		struct_dict = {}
		for dll in dll_list:
			if length_type:
				struct_dict = pdb.get_structure_length(struct_name, str(dll), struct_dict)
			else:
				struct_dict = pdb.get_structure(struct_name, str(dll), struct_dict)

		if not struct_dict:
			print()
			print(" [--] Couldn't find any structs in the PDB files...")
			return None
		print("SUCCESS")

	if len((keys := list(struct_dict.keys()))) == 1:
		if length_type:
			return struct_dict[keys[0]]	
		return stringify_dict(keys[0], struct_dict[keys[0]]["struct"])	

	
	print(" [++] Found more than 1 object matching the struct name...")
	print(" [++] I will be printing them and allows you to select the one you want (or none)")
	sleep(1.4)
	for key, val in struct_dict.items():
		if length_type:
			print(f" * Struct: {key}, Size: {val}")
		else:
			print(f" * Struct: {key}")

	print(" [++] Choose struct (if you don't want any of these, don't write anything): ")
	choice = input()

	if choice in struct_dict:
		if length_type:
			return struct_dict[choice]
		else:
			return stringify_dict(choice, struct_dict[choice]["struct"])
	else:
		print("[==] You did not choose a type value, continuing to manual type resolving...")
		print("")
		sleep(1)
		return None


def main():
	"""
	WARNING: This code is a bit gross, sorry ^-^
	
 	WARNING: Any diseases, body damage, puking, mental issues this source code 
 	WARNING: causes are on your own responsibility. 
	"""

	# Arguements here
	# TODO: Add more options
	# TODO: Add support to read from header files
	
	parser = argparse.ArgumentParser(description='This program takes in a gross structure => prettifies it and adds offsets :).')
	parser.add_argument('--bits', '-B', type=int,
						help='Bits (64/32)', choices=[64,32], default=64)
	parser.add_argument('--length', '-L', type=int,
						help="Begin length from specific number.", default=0)
	parser.add_argument("--if", type=str, 
						help="File to get structure from (can also insert structure into top multiline string)")
	parser.add_argument("--of", type=str, 
						help="File to write structure from (default is stdout)")
	parser.add_argument("--unicode", "-U", help="Set this value to support unicode (TCHAR, TBYTE = WCHAR). Default is true.", action='store_true', default=True)
	parser.add_argument("--quiet", "-q", help="Set this value to get only the output, no prints.", action='store_true')
	parser.add_argument('--dlls', '-d', help='A list of DLL files from C:/Windows/System32 separated by a comma', type=str)
	

	options = parser.parse_args()

	dll_list = "" if options.dlls is None else options.dlls
	while (dll_list := [item.strip() for item in dll_list.split(',')]) == [""]:
		print("DLL List is empty, please insert a list of dlls separated by a comma (,):")
		dll_list = input().strip()

	print(f"Dll list: {dll_list}")
	pull_pdb_files(dll_list, options.bits)

	options_dict = vars(options)
	
	if not options_dict["unicode"]:
		basic_types_32_bit["TCHAR"] = 1; basic_types_32_bit["TBYTE"] = 1
		basic_types_64_bit["TCHAR"] = 1; basic_types_64_bit["TBYTE"] = 1

	quiet_mode_set = options.quiet
	conditional_print = lambda string, print_cond: print(string) if (not print_cond) else 0
	
	conditional_print("[++] Acquiring desired struct...", quiet_mode_set)
	

	struct_file = options_dict["if"]
	struct = default_struct
	if struct_file is not None:
		if not exists(struct_file):
			raise FileNotFoundError(f"Could not find file: {struct_file}")
		struct = open(struct_file, "r").read()
		
	conditional_print("[==] Acquired struct!\n", quiet_mode_set)
	sleep(0.5)

	# Resolve structure offsets
	conditional_print("[++] Resolving struct offsets and formatting...", quiet_mode_set)

	print("Enter the struct's name: ")
	struct_name = input()
	conditional_print(" [++] Attempting to automatically get structure...", quiet_mode_set)

	sleep(0.5)
	if (returned_struct := automatically_resolve_struct(struct_name, length_type=False)) is None:
		returned_struct = resolve_struct(struct, options).struct

	conditional_print("[==] Finished calculating offsets and formatting.\n(if there were any errors please submit an issue to my github)\n", quiet_mode_set)
	
	formatted = pyastyle.format(returned_struct, '--style=allman')
	line_max_length = lambda lines: max(len(line[:line.find("//")]) for line in lines.split("\n"))
	formatted = formatted.expandtabs(line_max_length(formatted) + 4)
	
	conditional_print("[++] Writing formatted string to output / file...\n", quiet_mode_set)
	struct_out_file = options_dict["of"]
	if struct_out_file is not None:
		with open(struct_out_file, "w") as f:
			f.write(formatted)
	else:
		print(formatted)
	conditional_print("\n[==] Finished writing output, thank you for using this program :)", quiet_mode_set)

if __name__ == "__main__":
	main()
