#-*- coding:utf-8 -*-
import re
import time
import json
import struct
import hashlib
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

import config
from handler import WebSocketsHandler
from diff_match_patch import diff_match_patch

difflib = diff_match_patch()

def md5(string):
    return hashlib.md5(string).hexdigest()

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
        self.client_info = {}

    def on_message(self, data):
        print 'message received:', data
        data = json.loads(data)

        if data['command'] == 'REGISTRY':
            self.cmd_regitry(data)
        elif data['command'] == 'OPENDOCUMENT':
            self.cmd_open_document(data)
        elif data['command'] == 'CONTENT':
            self.cmd_content(data)
        elif data['command'] == 'PATCH':
            self.cmd_patch(data)

    def on_disconnect(self, reason):
        print 'connection lost'

        for client in self.factory.clients:
            if client != self:
                client.send_command('USERDISCONNECT', **self.client_info)

        self.factory.clients.remove(self)


    def cmd_regitry(self, data):
        if data['key'] == md5(data['email']+config.SALT):
            self.client_info = dict(name=data['name'],
                                    email=data['email'],
                                    email_hash=data['email_hash'])

            connected_users = []
            for client in self.factory.clients:
                if client != self:
                    client.send_command('USERCONNECT', **self.client_info)
                    connected_users.append(client.client_info);

            self.send_command('REGISTRY', users=connected_users);
        else:
            self.transport.loseConnection()

    def cmd_content(self, data):
        doc_name = data['doc_name']
        if doc_name not in self.documents:
            self.documents[doc_name] = self.server.open_document(doc_name)

        content = self.documents[doc_name].content
        self.send_command('CONTENT', doc_name=doc_name, content=content)

    def cmd_patch(self, data):
        doc_name = data['doc_name'] 
        patches = data['patches']

        if doc_name not in self.documents:
            self.documents[doc_name] = self.server.open_document(doc_name)

        document = self.documents[doc_name]
        document.apply_patch(patches)

        for client in self.factory.clients:
            if client != self and doc_name in client.documents:
                client.send_command('PATCH', doc_name=doc_name, patches=patches)

    def cmd_open_document(self, data):
        self.document = self.server.open_document(data['doc_name'])
        self.cmd_content(data)



def main():
    server = Server()
    f = Factory()
    # f.client_host = 
    f.protocol = WebClient
    f.clients = []
    f.server = server

    reactor.listenTCP(8080, f)
    print 'Listening on port', 8080
    reactor.run()

if __name__ == '__main__':
    main()