cd extract_length_lib
cargo build --release
move target\release\pymspdb.dll ..\pymspdb.pyd 
cargo clean
cd ..