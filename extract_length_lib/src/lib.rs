use std::env;
use std::path::Path;
use std::fs::File;
use fallible_iterator::FallibleIterator;
use pyo3::prelude::*;
use pyo3::exceptions::*;
use pyo3::{PyResult};
use pyo3::types::{PyString, PyList, IntoPyDict, PyDict};
use pdb::RawString;
// use std::io::{Error, ErrorKind};

/*
pub fn main() -> std::io::Result<()>{
    let mut path = env::current_dir()?;
    path = path.join(Path::new("resources"))
            .join(Path::new("notepad.pdb"));

    let file = File::open(path)
    .expect("Cannot open file.");

    let mut pdb = pdb::PDB::open(file)
    .expect("Cannot parse pdb file.");

    let type_information = pdb.type_information()
    .expect("Could not get type info");
    let mut type_finder = type_information.finder();

    let mut iter = type_information.iter();
    while let Some(typ) = iter.next().expect("Could not get next iter") {
        // build the type finder as we go
        type_finder.update(&iter);

        // parse the type record
        match typ.parse() {
            Ok(pdb::TypeData::Class(pdb::ClassType {name, fields: Some(fields), ..})) => {
                // this Type describes a class-like type with fields
                
                let mut type_name = name.to_string().into_owned();
                type_name.make_ascii_lowercase();

                let desired_type = "word";
                if !type_name.contains(desired_type) {
                    continue;
                }


                // `fields` is a TypeIndex which refers to a FieldList
                // To find information about the fields, find and parse that Type
                match type_finder.find(fields)
                .expect("Could not find fields")
                .parse()
                .expect("Could not parse field") {
                    pdb::TypeData::FieldList(list) => {
                        // `fields` is a Vec<TypeData>

                        for field in list.fields {
                            if let pdb::TypeData::Member(member) = field {
                                //let found_type = type_finder.find(member.field_type)
                                //                .expect("Could not get member field type");
                                //if let Ok(type_data) = found_type.parse() {
                                 //   println!("{:?}", type_data);
                                //}
                                // follow `member.field_type` as desired
                                println!("  - field {} at offset {:x}", member.name, member.offset);
                            } else {
                                // handle member functions, nested types, etc.
                            }
                        }
                    },
                    _ => { }
                }

            },
            Ok(_) => {
                // ignore everything that's not a class-like type
            },
            Err(pdb::Error::UnimplementedTypeKind(_)) => {
                // found an unhandled type record
                // this probably isn't fatal in most use cases
            },
            Err(_e) => {

            }
        }
    }
    Ok(())
}
*/

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

fn insert_fields_into_dict(py: Python, dict: &PyDict, desired_type: String) -> Result<(), PyErr> {
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
    let mut pdb = match pdb::PDB::open(file) {
        Ok(_pdb) => _pdb,
        Err(e) => {
            return Err(Exception::py_err(e.to_string()));
        }
    };

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
            Ok(pdb::TypeData::Class(pdb::ClassType {name, fields: Some(fields), ..})) => {
                
                // Make sure we get the desired type
                if !is_desired_type(&name, &desired_type[..]) {
                    continue;
                }

                let current_dict = PyDict::new(py);

                // Parse current field
                match type_finder.find(fields)
                .expect("Could not find fields")
                .parse()
                .expect("Could not parse field") {
                    pdb::TypeData::FieldList(list) => {
                        for field in list.fields {
                            if let pdb::TypeData::Member(member) = field {
                                current_dict.set_item(member.name.to_string(), member.offset)
                                .handle_properly();
                                // println!("  - field {} at offset {:x}", member.name, member.offset);
                            }
                        }
                    },
                    _ => { }
                }

                // Add dictionary to all dicts
                dict.set_item(name.to_string(), current_dict).handle_properly();
            },
            Err(e) => {
                println!("[pymspdb] Warning: {}", e);
            },
            _ => {}
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
    #[pyfn(m, "extract_symbols")]
    fn extract_symbols_py(py: Python, desired_type: String) -> PyResult<&PyDict> {

        println!("Hello world! ");
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

    Ok(())
}