#-*- coding:utf-8 -*-
import re
import time
import struct
import hashlib
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

from handler import WebSocketsHandler
from diff_match_patch import diff_match_patch

difflib = diff_match_patch()

class Document(object):
    def __init__(self, name):
        self.name = name
        self.content = u''

    def apply_patch(self, patches):
        if isinstance(patches, basestring):
            patches = difflib.patch_fromText(patches)
        
        results = difflib.patch_apply(patches, self.content)
        self.content = results[0]

    def __repr__(self):
        return '<Doc %s>'%self.name

class Server(object):
    def __init__(self):
        self.documents = {}
    
    def open_document(self, name):
        if name in self.documents:
            return self.documents[name]
        else:
            return self.new_document(name)

    def new_document(self, name=None):
        if not name:
            name = str(time.time()).replace('.', '')
        
        self.documents[name] = Document(name)
        return self.documents[name]


class WebClient(WebSocketsHandler):
    def on_connect(self):
        print 'connection made'
        self.factory.clients.append(self)
        self.server = self.factory.server
        self.documents = {}

    def on_message(self, data):
        print 'message received:', data
        print 'documents:', self.server.documents
        print 'opened:', self.documents

        if data.count(':') > 1:
            command, doc_name, arg = data.split(':', 2)
        else:
            command, doc_name = data.split(':', 1)

        if command == 'CMD OPENDOCUMENT':
            self.cmd_open_document(doc_name)
        elif command == 'CMD CONTENT':
            self.cmd_content(doc_name)
        elif command == 'CMD PATCH':
            self.cmd_patch(doc_name, arg)

    def on_disconnect(self, reason):
        print 'connection lost'
        self.factory.clients.remove(self)


    def cmd_content(self, doc_name):
        if doc_name not in self.documents:
            self.documents[doc_name] = self.server.open_document(doc_name)

        content = self.documents[doc_name].content
        self.send_command('CMD CONTENT', doc_name, content)

    def cmd_patch(self, doc_name, patches):
        if doc_name not in self.documents:
            self.documents[doc_name] = self.server.open_document(doc_name)

        document = self.documents[doc_name]
        document.apply_patch(patches)

        for client in self.factory.clients:
            if client != self and doc_name in client.documents:
                client.send_command('CMD PATCH', doc_name, patches)

    def cmd_open_document(self, doc_name):
        self.document = self.server.open_document(doc_name)
        self.cmd_content(doc_name)



def main():
    server = Server()
    f = Factory()

    f.protocol = WebClient
    f.clients = []
    f.server = server

    reactor.listenTCP(8080, f)
    print 'Listening on port', 8080
    reactor.run()

if __name__ == '__main__':
    main()