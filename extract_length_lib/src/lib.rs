use std::env;
use std::fmt::Debug;
// use std::borrow::Cow;
use std::path::Path;
use std::str;
use std::fs::File;
use fallible_iterator::FallibleIterator;
use pyo3::prelude::*;
use pyo3::exceptions::*;
use pyo3::{PyResult};
use pyo3::types::{PyString, /*PyList, IntoPyDict,*/ PyDict, PyTuple};
use pdb::{RawString, TypeIndex, TypeFinder/*, PrimitiveType*/};
// use std::io::{Error, ErrorKind};

#[derive(Debug, PartialEq)]
pub enum TypeData {
    Primitive,
    Class,
    Member,
    MemberFunction,
    OverloadedMethod,
    Method,
    StaticMember,
    Nested,
    BaseClass,
    VirtualBaseClass,
    VirtualFunctionTablePointer,
    Procedure,
    Pointer,
    Modifier,
    Enumeration,
    Enumerate,
    Array,
    Union,
    Bitfield,
    FieldList,
    ArgumentList,
    MethodList,
}
trait ErrorHandler {
    fn handle_properly(&self) -> ();
}

impl<T> ErrorHandler for PyResult<T> {
    fn handle_properly(&self) -> () {
        match self { 
            Err(_) => {
                println!("[{}] Couldn't set dict key.", line!());
            },
            _ => {}
        }
    }
}

fn is_desired_type(name: &RawString, desired_type: &str) -> bool {
    /*
    Checks if current class is of type of desired_string (case insensitive)
    */

    let mut type_name = name.to_string().clone().into_owned();
    type_name.make_ascii_lowercase();

    if !type_name.contains(desired_type) {
        return false
    }
    true
}

fn open_pdb_and_parse<'a>() -> Result<pdb::PDB<'a, File>, PyErr>{
    let mut path = match env::current_dir() {
        Ok(cur_dir) => cur_dir,
        Err(e) => {
            return Err(FileNotFoundError::py_err(e.to_string()));
        }
    };

    path = path.join(Path::new("resources"))
            .join(Path::new("ntdll.pdb"));

    // Open file handle to user specified PDB file
    let file = match File::open(path) {
        Ok(cur_file) => cur_file,
        Err(e) => {
            return Err(IOError::py_err(e.to_string()));
        }
    };

    // Open and parse PDB file from file handle
    let pdb = match pdb::PDB::open(file) {
        Ok(_pdb) => _pdb,
        Err(e) => {
            return Err(Exception::py_err(e.to_string()));
        }
    };

    Ok(pdb)
}


fn extract_type_string(type_finder: &TypeFinder, field_type: pdb::TypeIndex, member_name: Option<String>, prev_string: Option<&str>) 
-> (crate::TypeData, String) {
    let type_str: (crate::TypeData, String) = match type_finder.find(field_type)
    .expect("Could not find member")
    .parse()
    .expect("Could not parse field") {
        pdb::TypeData::Primitive(pdb::PrimitiveType{kind, ..}) => {
            match member_name {
                Some(member_name_) => (crate::TypeData::Primitive, format!("{} {};", format!("{:?}", kind).to_uppercase(), member_name_)),
                None => (crate::TypeData::Primitive, format!("{:?}", kind).to_uppercase())
            }
             
           // println!("{:#?}", kind);
           // 
            // println!("Kind: {}", format!("{:?}", kind).to_uppercase());
        },
        pdb::TypeData::Array(pdb::ArrayType {element_type, indexing_type, dimensions, ..}) => {
            match member_name {
                Some(member_name_) => (crate::TypeData::Array, 
                    format!("{} {:?} {} (Index type: {});", extract_type_string(type_finder, element_type, None, None).1, 
                                                    dimensions,
                                                    member_name_,
                                                    extract_type_string(type_finder, indexing_type, None, None).1)),
                None => (crate::TypeData::Array, 
                    format!("{} {:?} (Index type: {})", extract_type_string(type_finder, element_type, None, None).1, 
                                                    dimensions,
                                                    extract_type_string(type_finder, indexing_type, None, None).1))
            }
            
           // println!("{}", type_str);
        },
        pdb::TypeData::Bitfield(pdb::BitfieldType{underlying_type, length, position}) => {
            if position == 0 {
                match member_name {
                    Some(member_name_) => (crate::TypeData::Bitfield, 
                        format!("struct {{\n{} ({:#x}) - {}:{:#x} {};\n}}", 
                                            extract_type_string(type_finder, underlying_type, None, None).1,
                                            length, 
                                            position, position,
                                            member_name_)),
                    None => (crate::TypeData::Bitfield, 
                        format!("struct {{\n{} ({:#x}) - {}:{:#x};\n}}", 
                                            extract_type_string(type_finder, underlying_type, None, None).1,
                                            length, 
                                            position, position))
                }

            } else {
                if let Some(prev_option_string) = prev_string {
                    let prev_length = prev_option_string.len();
                    let prev_option_string = &prev_option_string[..(prev_length - 3)];
                    // println!("Prev: {}", prev_option_string.to_string());
                    match member_name {
                        Some(member_name_) => (crate::TypeData::Bitfield, format!("{}{} ({:#x}) - {}:{:#x} {};\n}}", 
                                                        prev_option_string, 
                                                        extract_type_string(type_finder, underlying_type, None, None).1, 
                                                        length, position, position, member_name_)),
                        None => (crate::TypeData::Bitfield, format!("{}{} ({:#x}) - {}:{:#x};\n}}", 
                                                        prev_option_string, 
                                                        extract_type_string(type_finder, underlying_type, None, None).1, 
                                                        length, position, position))
                    }

                } else {
                    (crate::TypeData::Bitfield, 
                        String::from(""))
                }
            }
            

           // println!("{}", type_str);
        },
        pdb::TypeData::Union(pdb::UnionType{name, ..}) => {
            let final_union = match member_name {
                Some(member_name_) => {
                    format!("union {} {};", name.to_string(), member_name_)
                },
                None => format!("union {};", name.to_string())
            };
            // println!("{:#?} - {}", , name.to_string());
            
            (crate::TypeData::Union,
                final_union)
        },
        pdb::TypeData::Class(pdb::ClassType{name, ..}) => {
            let final_struct = match member_name {
                Some(member_name_) => {
                    format!("struct {} {};", name.to_string(), member_name_)
                },
                None => format!("struct {}", name.to_string())
            };
            // println!("{:#?} - {}", , name.to_string());
            
            (crate::TypeData::Class,
                final_struct)
        },
        pdb::TypeData::Pointer(pdb::PointerType{underlying_type, attributes,..}) => {
            let mut final_pointer = String::from("");
            if attributes.is_const() {
                final_pointer.push_str("const ");
            }
            if let Some(member_name) = member_name {
                let member_name = format!("*{}", member_name);
                let pointer_type = extract_type_string(type_finder, underlying_type, Some(member_name), None).1;
                final_pointer.push_str(&pointer_type[..]);
            } else {
                let _member_name = String::from("*");
                let pointer_type = extract_type_string(type_finder, underlying_type, None, None).1;
                let pointer_type = format!("{}*", pointer_type);
                final_pointer.push_str(&pointer_type[..]);
            }
            // println!("POINTER {}", final_pointer);
            (crate::TypeData::Pointer,
                final_pointer)
        },
        pdb::TypeData::Modifier(pdb::ModifierType {underlying_type, constant, volatile, unaligned}) => {
            let mut final_modified = String::from("");
            if constant {
                final_modified.push_str("const ");
            }
            if volatile {
                final_modified.push_str("volatile ");
            }
            if unaligned {
                final_modified.push_str("unaligned ");
            }

            if let Some(member_name) = member_name {
                let modifier_type = extract_type_string(type_finder, underlying_type, Some(member_name), None).1;
                final_modified.push_str(&modifier_type[..]);
            } else {
                let _member_name = String::from("<unknown>");
                let modifier_type = extract_type_string(type_finder, underlying_type, None, None).1;
                let modifier_type = format!("{}", modifier_type);//, member_name);
                final_modified.push_str(&modifier_type[..]);
            }
            // println!("MODIFIER {}", final_modified);
            (crate::TypeData::Modifier,
                final_modified)
        },
        pdb::TypeData::Procedure(pdb::ProcedureType {return_type, argument_list, ..}) => {
            let mut final_procedure = String::from("");

            if let Some(return_type) = return_type {
                let return_type = extract_type_string(type_finder, return_type, None, None).1;
                final_procedure.push_str(&return_type[..]);
                final_procedure.push_str(" ");
            }

            if let Some(member_name) = member_name {
                let procedure_type = extract_type_string(type_finder, argument_list, Some(member_name.clone()), None).1;
                let procedure_type = format!("{} {}", member_name, procedure_type);
                final_procedure.push_str(&procedure_type[..]);
            } else {
                let _member_name = String::from("<unknown>");
                let procedure_type = extract_type_string(type_finder, argument_list, None, None).1;
                let procedure_type = format!("{}", procedure_type);//, member_name);
                final_procedure.push_str(&procedure_type[..]);
            }
            // println!("PROCEDURE {}", final_procedure);
            (crate::TypeData::Modifier,
                final_procedure)
        },
        pdb::TypeData::ArgumentList(pdb::ArgumentList {arguments}) => {
            let mut final_argument_string = String::from("(");
            let vec_len_index = arguments.len() - 1;
            let mut count = 0;
            for type_index in arguments.into_iter() {
                let mut type_var = extract_type_string(type_finder, type_index, None, None).1;
                if count == vec_len_index {
                    type_var = format!("{}", type_var);
                } else {
                    type_var = format!("{}, ", type_var);
                }
                
                final_argument_string.push_str(&type_var[..]);
                count += 1;
            }
            final_argument_string.push_str(")");
            (crate::TypeData::ArgumentList,
                final_argument_string)
        }
        _type_data =>  {
            // println!("{:#?}", type_data);
            (crate::TypeData::FieldList,
                String::from("** CANNOT FIND TYPE, PLEASE SUBMIT ISSUE ON GITHUB **"))
        },
    };
    // println!("{:#?}", type_str);
    type_str
}


fn loop_over_fields(py: &Python, type_finder: &TypeFinder, fields: TypeIndex, current_dict: &PyDict) -> () {
    match type_finder.find(fields)
    .expect("Could not find fields")
    .parse()
    .expect("Could not parse field") {
        pdb::TypeData::FieldList(list) => {
            for field in list.fields {
                if let pdb::TypeData::Member(member) = field {
                    // println!("");

                    let current_name = &member.name.to_string().into_owned()[..];
                    let (_type_data, type_str) = extract_type_string(&type_finder, member.field_type, Some(current_name.to_string()), None);
                    
                    // println!("{} ({}) - ", member.name.to_string(), member.offset);
                    // println!("Name {} Type {} Offset {:#x}", current_name, type_str, member.offset);
                    // println!("");
                    if let Some(type_cast) = current_dict.get_item(member.offset) {
                        let prev_type_string_tuple = type_cast.downcast::<PyTuple>().expect("Bad downcast");
                        // println!("{:#?} ({:#x})", prev_type_string_tuple, member.offset);
                        let prev_type_string = prev_type_string_tuple.get_item(1).downcast::<PyString>()
                                                        .expect("Cant downcast pystring").to_string()
                                                        .unwrap().into_owned();
                        let original_name = prev_type_string_tuple.get_item(0).downcast::<PyString>()
                                                        .expect("Cant downcast pystring").to_string()
                                                        .unwrap().into_owned();

                        let (type_data, type_str) = extract_type_string(&type_finder, member.field_type, Some(current_name.to_string()),
                                                        Some(&prev_type_string[..(prev_type_string.len() - 1)]));
                        
                        let prev_string_length = prev_type_string.len();

                        let result_string;
                        let mut cut_index = prev_string_length - 2;
                        if type_data == crate::TypeData::Bitfield {
                            cut_index = 0;
                        }
                        let last_character = prev_type_string.chars().last().unwrap();

                        
                        // println!("Field: {}", prev_type_string);
                        // println!("last character: {}", last_character);
                        if last_character == '}' {
                            if cut_index > 0 {
                                let prev_type_string = (&prev_type_string[..cut_index]).to_string();
                                result_string = format!("{}\n{};\n}}", prev_type_string, type_str);
                            } else {
                                result_string = format!("{};\n}}", type_str);
                            }
                            // println!("Result string: {}", result_string);
                        } else {
                            result_string = format!("union {{\n{}\n{};\n}}", 
                                                    prev_type_string, type_str);
                        }
                        let types = vec![original_name, result_string];
                        let types_tuple = PyTuple::new(*py, types);

                        current_dict.set_item(member.offset, types_tuple).handle_properly();
                        
                    } else {
                        let types = vec![current_name.to_string(), type_str];
                        let types_tuple = PyTuple::new(*py, types);
                        // println!("{:#?} {:#x}", types_tuple, member.offset);
                        current_dict.set_item(member.offset, types_tuple).handle_properly();
                    }
                    
                    
                    // println!("  - field {} at offset {:x}", member.name, member.offset);
                }
            }
        },
        _ => { }
    }
    ()
}

fn insert_length_into_dict(_py: Python, dict: &PyDict, desired_type: String) -> Result<(), PyErr> {
    
    let mut pdb = open_pdb_and_parse()?;

    // Acquire type information from the pdb file
    let type_information = match pdb.type_information() {
        Ok(_type) => _type,
        Err(e) => {
            return Err(Exception::py_err(e.to_string()));
        }
    };

    // Create type_information finder which allows to interate over all the 
    // types inside the PDB file.
    let mut type_finder = type_information.finder();

    // Get iterator object for type_information.
    let mut iter = type_information.iter();
    let desired_type = desired_type.to_lowercase();

    while let Some(typ) = match iter.next() {
            Ok(_next) => _next,
            Err(e) => {
                return Err(Exception::py_err(e.to_string()));
            }
        } 

        {
        // Update the type finder to go to the current one
        type_finder.update(&iter);

        // parse the type record
        match typ.parse() {
            Ok(pdb::TypeData::Class(pdb::ClassType {name, size,  ..})) => {
                
                // Make sure we get the desired type
                if !is_desired_type(&name, &desired_type[..]) {
                    continue;
                }

                // Add dictionary to all dicts
                dict.set_item(name.to_string(), size).handle_properly();
            },
            Err(e) => {
                println!("[pymspdb] Warning: {}", e);
            },
            _ => {
                // println!("{:?}", obj);
            }
        }
    }
    Ok(())
}


fn insert_fields_into_dict(py: Python, dict: &PyDict, desired_type: String) -> Result<(), PyErr> {
    
    let mut pdb = open_pdb_and_parse()?;

    // Acquire type information from the pdb file
    let type_information = match pdb.type_information() {
        Ok(_type) => _type,
        Err(e) => {
            return Err(Exception::py_err(e.to_string()));
        }
    };

    // Create type_information finder which allows to interate over all the 
    // types inside the PDB file.
    let mut type_finder = type_information.finder();

    // Get iterator object for type_information.
    let mut iter = type_information.iter();
    let desired_type = desired_type.to_lowercase();

    while let Some(typ) = match iter.next() {
            Ok(_next) => _next,
            Err(e) => {
                return Err(Exception::py_err(e.to_string()));
            }
        } 

        {
        // Update the type finder to go to the current one
        type_finder.update(&iter);

        // parse the type record
        match typ.parse() {
            Ok(pdb::TypeData::Class(pdb::ClassType {name, size, fields: Some(fields), ..})) => {
                
                // Make sure we get the desired type
                if !is_desired_type(&name, &desired_type[..]) {
                    continue;
                }

                let current_dict = PyDict::new(py);

                let struct_dict = PyDict::new(py);
                // Parse current field
                loop_over_fields(&py, &type_finder, fields, struct_dict);

                current_dict.set_item("size", size).handle_properly();
                current_dict.set_item("struct", struct_dict).handle_properly();
                // Add dictionary to all dicts
                dict.set_item(name.to_string(), current_dict).handle_properly();
                
            },
            Err(e) => {
                println!("[pymspdb] Warning: {}", e);
            },
            _ => {
                // println!("{:?}", obj);
            }
        }
    }
    Ok(())
}

#[pymodule]
fn pymspdb(_py: Python, m: &PyModule) -> PyResult<()> {
    // PyO3 aware function. All of our Python interfaces could be declared in a separate module.
    // Note that the `#[pyfn()]` annotation automatically converts the arguments from
    // Python objects to Rust values, and the Rust return value back into a Python object.
    // The `_py` argument represents that we're holding the GIL.
    #[pyfn(m, "get_structure")]
    fn extract_symbols_py(py: Python, desired_type: String) -> PyResult<&PyDict> {

        let dict = PyDict::new(py);
        
        match insert_fields_into_dict(py, dict, desired_type) {
            Ok(_) => (),
            Err(e) => {
                return Err(e);
            }
        }
        /* dict.set_item("hey", "world")
        .expect("Could not set item.");
        dict.set_item("what", "is going on")
        .expect("Could not set item.");;
        let lst = vec![1, 2, 3, 4].to_object(_py);
        */
        Ok(dict)
    }

    #[pyfn(m, "get_structure_length")]
    fn extract_symbols_len_py(py: Python, desired_type: String) -> PyResult<&PyDict> {

        let dict = PyDict::new(py);

        match insert_length_into_dict(py, dict, desired_type) {
            Ok(_) => (),
            Err(e) => {
                return Err(e);
            }
        }
        /* dict.set_item("hey", "world")
        .expect("Could not set item.");
        dict.set_item("what", "is going on")
        .expect("Could not set item.");;
        let lst = vec![1, 2, 3, 4].to_object(_py);
        */
        Ok(dict)
    }
    Ok(())
}