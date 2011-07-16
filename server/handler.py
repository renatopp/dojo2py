#-*- coding:utf-8 -*-
import re
import struct
import hashlib
from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

HANDSHAKE = (
    "HTTP/1.1 101 Web Socket Protocol Handshake\r\n"
    "Upgrade: WebSocket\r\n"
    "Connection: Upgrade\r\n"
    "WebSocket-Origin: %(origin)s\r\n"
    "WebSocket-Location: ws://%(bind)s:%(port)s/\r\n"
    "Sec-Websocket-Origin: %(origin)s\r\n"
    "Sec-Websocket-Location: ws://%(bind)s:%(port)s/\r\n"
    "\r\n"
)

class WebSocketsHandler(Protocol):
    def __init__(self):        
        self.handshaken = False
        self.client = None
        self.server = None
        self.handshaken = False
        self.header = ""
        self.data = ""

    def on_connect(self):
        pass
    
    def on_message(self, data):
        pass

    def on_disconnect(self, reason):
        pass


    def connectionMade(self):
        self.server = self.transport.getHost()
        self.client = self.transport.getPeer()
        self.on_connect()
    
    def connectionLost(self, reason):
        self.on_disconnect(reason)

    def dataReceived(self, data):
        if not self.handshaken:
            self.header += data
            if self.header.find('\r\n\r\n') != -1:
                parts = self.header.split('\r\n\r\n', 1)
                self.header = parts[0]
                if self._dohandshake(self.header, parts[1]):
                    self.handshaken = True
        else:
            self.data += data
            msgs = self.data.split('\xff')
            self.data = msgs.pop()
            for msg in msgs:
                if msg[0] == '\x00':
                    self.on_message(msg[1:])


    def send(self, data):
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        self.transport.write("\x00%s\xff" % data)

    def _dohandshake(self, header, key=None):
        digitRe = re.compile(r'[^0-9]')
        spacesRe = re.compile(r'\s')
        part_1 = part_2 = origin = None
        for line in header.split('\r\n')[1:]:
            name, value = line.split(': ', 1)
            if name.lower() == "sec-websocket-key1":
                key_number_1 = int(digitRe.sub('', value))
                spaces_1 = len(spacesRe.findall(value))
                if spaces_1 == 0:
                    return False
                if key_number_1 % spaces_1 != 0:
                    return False
                part_1 = key_number_1 / spaces_1
            elif name.lower() == "sec-websocket-key2":
                key_number_2 = int(digitRe.sub('', value))
                spaces_2 = len(spacesRe.findall(value))
                if spaces_2 == 0:
                    return False
                if key_number_2 % spaces_2 != 0:
                    return False
                part_2 = key_number_2 / spaces_2
            elif name.lower() == "origin":
                origin = value
        if part_1 and part_2:
            challenge = struct.pack('!I', part_1)+struct.pack('!I', part_2)+key
            response = hashlib.md5(challenge).digest()
            handshake = HANDSHAKE % {
                'origin': origin,
                'port': self.server.port,
                'bind': self.server.host
            }
            handshake += response
        else:
            handshake = HANDSHAKE % {
                'origin': origin,
                'port': self.server.port,
                'bind': self.server.host
            }
        self.transport.write(handshake)

        return True
