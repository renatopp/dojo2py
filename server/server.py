#-*- coding:utf-8 -*-
import re
import struct
import hashlib
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

from handler import WebSocketsHandler
from diff_match_patch import diff_match_patch

difflib = diff_match_patch()

class Environment(object):
    def __init__(self):
        self.text = '';

    def apply_patch(self, patches):
        if isinstance(patches, basestring):
            patches = difflib.patch_fromText(patches)
        
        results = difflib.patch_apply(patches, self.text)
        self.text = results[0]

        print 'updating text:'
        print self.text
        print 


class WebClient(WebSocketsHandler):
    def on_connect(self):
        print 'connection made'
        self.factory.clients.append(self)

    def on_message(self, data):
        print 'message received:', data

        if ':' in data:
            command, arg = data.split(':', 1)
        else:
            command = data

        if command == 'CMD CONTENT':
            self.cmd_content()
        if command == 'CMD PATCH':
            self.cmd_patch(arg)


    def on_disconnect(self, reason):
        print 'connection lost'
        self.factory.clients.remove(self)


    def cmd_content(self):
        self.send('CMD CONTENT:'+self.factory.environment.text)

    def cmd_patch(self, patches):
        self.factory.environment.apply_patch(patches)

        for client in self.factory.clients:
            if client != self:
                client.send('CMD PATCH:'+patches)


def main():
    environment = Environment()
    f = Factory()

    f.protocol = WebClient
    f.clients = []
    f.environment = environment

    reactor.listenTCP(8080, f)
    print 'Listening on port', 8080
    reactor.run()

if __name__ == '__main__':
    main()