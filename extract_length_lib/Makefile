ifeq ($(OS), Windows_NT)
	OPERATING_SYS=Windows
	LIBRARY=pymspdb.dll
	DESIRED_LIBRARY=pymspdb.pyd
	LIBRARY_BEGINNING=pymspdb
else
	OPERATING_SYS=Linux
	LIBRARY=libpymspdb.so
	DESIRED_LIBRARY=pymspdb.so
	LIBRARY_BEGINNING=libpymspdb
endif

clean:
	@echo "Cleaning for $(OPERATING_SYS)..."
	rm $(DESIRED_LIBRARY)

build:
	@echo "Building for $(OPERATING_SYS)..."
	sudo cargo build --release
	cp target/release/$(LIBRARY) $(DESIRED_LIBRARY)
	rm target/release/$(LIBRARY_BEGINNING)*