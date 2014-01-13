import os
import sys
import json
import zlib
import base64
import httplib
import StringIO
import signal

from pyth.plugins.rtf15.reader import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter

import file_events

def parse_sticky_database(s):
    cur = 0
    while True:
        start = s.find('{\\rtf', cur+1)
        if start == -1:
            break

        cur = start
        depth = 1
        while depth > 0:
            nextleft = s.find('{', cur+1)
            nextright = s.find('}', cur+1)
            #print 'at %d: nextleft=%d nextright=%d' % (cur, nextleft, nextright)
            if nextleft == -1 and nextright == -1:
                raise Exception('Parse error in StickiesDatabase')
            elif nextleft != -1 and nextleft < nextright:
                depth += 1
                cur = nextleft
            else:
                depth -= 1
                cur = nextright

        yield s[start:cur+1]

def load_stickies(path):
    stickies = []
    with open(path) as fd:
        for i,rtf in enumerate(parse_sticky_database(fd.read())):
            doc = Rtf15Reader.read(StringIO.StringIO(rtf))
            plaintext = PlaintextWriter.write(doc).getvalue()
            stickies.append(plaintext)
    return stickies

class StickiesClient(object):
    URL_TEMPLATE = 'http://%s:%d/update/%d'
    def __init__(self, server_hostname, server_port, user_id):
        self._user_id = user_id
        self._server_hostname = server_hostname
        self._server_port = server_port
        self._server_url = self.URL_TEMPLATE % (server_hostname, server_port, user_id)

    def upload(self, stickies):
        # Generate json
        message = {
            'stickies': stickies
            };

        # Compress
        json_str = json.dumps(message)
        compressed_data = base64.b64encode(zlib.compress(json_str, 9))
        size_mb = float(len(compressed_data)) / 1e+6

        # Transmit data
        print 'Uploading stickies to %s' % self._server_url
        conn = httplib.HTTPConnection(host=self._server_hostname, port=self._server_port)
        conn.request(method='POST', url=self._server_url, body=compressed_data)

        # Get response
        response = conn.getresponse()
        print 'Server said:'
        print '  %d %s' % (response.status, response.reason)
        for line in response.read().strip().split('\n'):
            print '  '+line


class StickiesListener(object):
    def __init__(self, path, client):
        self._path = path
        self._client = client

    def on_file_event(self, path, flags):
        if path == self._path:
            print 'Detected modification to stickies. Flags=%s' % hex(flags)

            # Parse the stickies
            stickies = load_stickies(self._path)
            print 'Loaded %d stickies' % len(stickies)

            # Upload to server
            client.upload(stickies)

    def loop(self):
        file_events.register(os.path.dirname(stickies_path), self.on_file_event)
        file_events.loop()

def signal_handler(signal, frame):
    print 'You pressed Ctrl+C!'
    file_events.stop()

if __name__ == '__main__':
    stickies_path = os.path.join(os.getenv('HOME'), 'Library/StickiesDatabase')
    if not os.path.exists(stickies_path):
        print 'Could not find stickies database at %s' % stickies_path

    # Install ctrl-c handler
    signal.signal(signal.SIGINT, signal_handler)

    USER_ID = 1
    client = StickiesClient('localhost', 5000, USER_ID)

    client.upload(load_stickies(stickies_path))
    listener = StickiesListener(stickies_path, client)
    listener.loop()
