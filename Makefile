
PYTHON_CONFIG=/usr/local/bin/python2.7-config
CFLAGS=$(shell $(PYTHON_CONFIG) --cflags)

LDFLAGS=-lboost_python-mt $(shell $(PYTHON_CONFIG) --ldflags) -framework CoreServices

file_events.so: file_events.cpp
	g++ -fPIC -shared -o $@ $+ $(CFLAGS) $(LDFLAGS)

testlib.so: testlib.cpp
	g++ -fPIC -shared -o $@ $+ $(CFLAGS) $(LDFLAGS)
