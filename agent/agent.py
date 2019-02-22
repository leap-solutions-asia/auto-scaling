#! /usr/bin/env python

import sys
import json
import threading
if sys.version_info[0] >= 3:
    from http.server import BaseHTTPRequestHandler, HTTPServer
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

#
PORT = 8585


class Collector(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.usage = 0.0
        self.event = threading.Event()

    def run(self):
        last_idle = last_total = 0
        while not self.event.wait(timeout=5):
            with open('/proc/stat') as f:
                for line in f:
                    if line.startswith("cpu "):
                        break
                data = [ float(x) for x in line.strip().split()[1:] ]
                idle = data[3]
                total = sum(data)
                self.usage = ((total - last_total) - (idle - last_idle)) \
                             / (total - last_total) * 100.0
                last_idle = idle
                last_total = total


class AutoScalingUsageHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global collector
        response = json.dumps({
            "usage": round(collector.usage, 1),
        })
        if sys.version_info[0] >= 3:
            response = response.encode('utf8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(response))
        self.end_headers()
        self.wfile.write(response)


if __name__ == "__main__":
    # Options
    try:
        from argparse import ArgumentParser
        parser = ArgumentParser()
        parser.add_argument("-p", "--port", type=int, default=PORT, help="Port Number")
        options = parser.parse_args()
    except:
        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option("-p", "--port", type="int", default=PORT, help="Port Number")
        (options, args) = parser.parse_args()

    try:
        collector = Collector()
        collector.start()
        HTTPServer(('', options.port), AutoScalingUsageHandler).serve_forever()
    except KeyboardInterrupt:
        collector.event.set()
