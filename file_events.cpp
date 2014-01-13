#include <Python.h>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>

#include <string>

#include <boost/python/module.hpp>
#include <boost/python/def.hpp>

#include <CoreServices/CoreServices.h> 

class FileEventHandler {
 public:
  std::string path;
  boost::python::object callback;

  void Dispatch(int num_events,
                const char ** paths,
                const FSEventStreamEventFlags flags[],
                const FSEventStreamEventId ids[]) {
    for (int i = 0; i < num_events; i++) {
      callback(paths[i], flags[i]);
    }
  }
};

//fork a process when there's any change in watch file
void handle_events(
    ConstFSEventStreamRef stream,
    void* pcontext,
    size_t num_events,
    void* ppaths,
    const FSEventStreamEventFlags flags[],
    const FSEventStreamEventId ids[]) {
  const char ** paths = reinterpret_cast<const char**>(ppaths);
  FileEventHandler* handler = reinterpret_cast<FileEventHandler*>(pcontext);
  handler->Dispatch(num_events, paths, flags, ids);
}

void register_listener(const std::string& path,
                       boost::python::object& callback) {
  // TODO: make sure this obejct gets deleted later
  FileEventHandler* handler = new FileEventHandler;
  handler->path = path;
  handler->callback = callback;

  // Create the event stream
  FSEventStreamContext context = { NULL, handler, NULL, NULL, NULL };
  CFStringRef cfpath = CFStringCreateWithCString(NULL, path.c_str(), kCFStringEncodingUTF8);
  CFArrayRef cfpaths = CFStringCreateArrayBySeparatingStrings (NULL, cfpath, CFSTR(":"));
  CFAbsoluteTime latency = 1.0;
  FSEventStreamRef stream = FSEventStreamCreate(NULL,
                                                &handle_events,
                                                &context,
                                                cfpaths,
                                                kFSEventStreamEventIdSinceNow,
                                                latency,
                                                kFSEventStreamCreateFlagFileEvents
                                                ); 

  // Run the stream
  FSEventStreamScheduleWithRunLoop(stream, CFRunLoopGetCurrent(), kCFRunLoopDefaultMode); 
  FSEventStreamStart(stream);
}

void loop() {
  // Start the event loop
  CFRunLoopRun();
}

void stop() {
  CFRunLoopStop(CFRunLoopGetCurrent());
}

const char* greet() {
   return "hello, world";
}

BOOST_PYTHON_MODULE(file_events) {
  using namespace boost::python;
  def("register", &register_listener);
  def("loop", &loop);
  def("stop", &stop);
}
