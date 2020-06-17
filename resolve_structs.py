from pathlib import Path
import re
from enum import IntEnum
from collections import deque


class type_enum(IntEnum):
    TYPE_REGULAR = 0
    TYPE_UNION = 1
    TYPE_STRUCT = 2


unknown_struct = """
typedef
struct
_DRIVER_OBJECT  { CSHORT             Type; // This should be ignored

  CSHORT             *Size; // so is this
  PDEVICE_OBJECT     *DeviceObject; /* and so is this */

  ULONG              Flags;

  PVOID              DriverStart;

  /* This should be ignored :)  */

  ULONG              DriverSize;
  /*
  PVOID thing
  Ignored thing1
  */
  PVOID              *DriverSection;

  union [[fallthrough]] [[noreturn]] {
    PVOID hello;
    PVOID world;
    union this_is_nice {
        PVOID helloWorld;
        INT thisIsNice;
    };
    /*
    INT thisSux;
    */
  };
  PDRIVER_EXTENSION  DriverExtension;
  UNICODE_STRING     DriverName;

  PUNICODE_STRING    HardwareDatabase;
  struct HelloWorld {
    INT64 cool;
    union {
      INT this;
    };
    PVOID helloThis;
  };
  PFAST_IO_DISPATCH  FastIoDispatch;
  PDRIVER_INITIALIZE DriverInit;

  PDRIVER_STARTIO    DriverStartIo;
  PDRIVER_UNLOAD     DriverUnload;
  PDRIVER_DISPATCH   MajorFunction[IRP_MJ_MAXIMUM_FUNCTION + 1];
} DRIVER_OBJECT, *PDRIVER_OBJECT;
"""

# Based on c++ variable naming rules
variable_capture_regex = r"[A-Za-z_]([A-Za-z0-9_]{0,254})$"
typedef_capture_regex = r"^typedef [a-zA-Z0-9_*, ]+ LPVOID[ ]{0,}[,;]"
union_capture_regex = r"union[ ]{0,}(\[\[[a-zA-Z0-9_]+\]\][ ]{1,}){0,}(\[\[[a-zA-Z0-9_]+\]\]){0,1}[a-zA-Z_]{0,1}[a-zA-Z_0-9]{0,}[ ]{0,}{"
struct_capture_regex = r"^struct[ ]{1,}[a-zA-Z_]{0,1}[a-zA-Z_0-9]{0,}[ ]{0,}{"


def get_current_file_gen(starting_address):
    """
    This function is a generator yielding a path from the start path
    each time (recursively)

    Args:
        starting_address (Path): start path
    """
    for file_name in starting_address.rglob("*.*"):
        yield file_name


def remove_comments(middle_struct):
    """
    This function removes the comments from the structure.

    Args:
        middle_struct (str struct): Struct described by a string
    """
    end_string, found_index = "", 0

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
    queue = deque()

    def __get_closing_curly_brace(string):
        for index, char in enumerate(string):
            if char == "{":
                queue.append(1)
            elif char == "}":
                queue.pop()
                if not queue:
                    return index

    string_after_bracket = string[string.find("{"):]
    return string.find("{") + __get_closing_curly_brace(string_after_bracket)


def type_extract_gen(structure_middle):
    uncommented_structure = remove_comments(structure_middle)
    # print(uncommented_structure)
    current_index = 0
    closing_index = -1
    for line in uncommented_structure.split(";"):
        current_line_length = len(line) + 1  # ";"
        if closing_index >= current_index:
            current_index += current_line_length
            continue

        line = line.strip()
        # print("Line: ", repr(line), re.match(union_capture_regex, line))
        # Found union
        if (union_match := re.match(union_capture_regex, line)) is not None\
                or re.match(struct_capture_regex, line) is not None:

            # Acquire entire struct / union
            closing_index = get_closing_curly_brace(uncommented_structure[current_index:])
            closing_index = current_index + closing_index + 1
            union_struct = ''.join(uncommented_structure[current_index:closing_index].split("  ")).strip()

            type = type_enum.TYPE_UNION if union_match is not None else type_enum.TYPE_STRUCT
            yield (union_struct, type)

        else:
            variable_match = re.search(variable_capture_regex, line)
            # print(repr(line), variable_match)
            if variable_match is None:
                continue
            return_val = ''.join(line[:variable_match.start(0)].split("  "))
            yield (return_val, type_enum.TYPE_REGULAR)

        current_index += current_line_length

# def parse_union()


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

    beginning = struct[:beginning_index].replace("\n", "")
    end = struct[ending_index:].replace("\n", "")
    middle = struct[beginning_index:ending_index]

    return beginning, middle, end


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
    path_to_headers = Path.home() / "Desktop/headers/"  # options[path]

    # Acquire all data types (string=data type, type=REGULAR TYPE/UNION/STRUCT)
    for string, type in type_extract_gen(middle):
        print(string, type)

    # Generator to loop over headers recursively
    current_file_gen = get_current_file_gen(path_to_headers)
    """
    for current_file in current_file_gen:
        with open(current_file, "r") as header_file:
            # parse_file_conditions(current_file, )
            print(get_all_typedefs())
    # Try to look for struct in winapi pdb
    """
    # print("Begin: ", beginning, "Middle: ", middle, "End: ", end)


def main():
    # Arguements here
    # TODO: check for 32/64 bit
    # TODO: Add more options
    # Temporary structure to test on
    struct = unknown_struct

    # Resolve structure offsets
    resolve_struct(struct)


if __name__ == "__main__":
    main()
