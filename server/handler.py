#-*- coding:utf-8 -*-
import re
import json
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
        self.__client = None
        self.__server = None
        self.__handshaken = False
        self.__header = ""
        self.__data = ""

    def on_connect(self):
        pass
    
    def on_message(self, data):
        pass

    def on_disconnect(self, reason):
        pass


    def connectionMade(self):
        self.__server = self.transport.getHost()
        self.__client = self.transport.getPeer()
        self.on_connect()
    
    def connectionLost(self, reason):
        self.on_disconnect(reason)

    def dataReceived(self, data):
        if not self.__handshaken:
            self.__header += data
            if self.__header.find('\r\n\r\n') != -1:
                parts = self.__header.split('\r\n\r\n', 1)
                self.__header = parts[0]
                if self._dohandshake(self.__header, parts[1]):
                    self.__handshaken = True
        else:
            self.__data += data
            msgs = self.__data.split('\xff')
            self.__data = msgs.pop()
            for msg in msgs:
                if msg[0] == '\x00':
                    self.on_message(msg[1:])


    def send(self, data):
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        self.transport.write("\x00%s\xff" % data)

    def send_command(self, command, **kwargs):
        kwargs['command'] = command
        msg = json.dumps(kwargs)
        print 'Sending command:', msg
        self.send(msg)

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
                'port': self.__server.port,
                'bind': self.__server.host
            }
            handshake += response
        else:
            handshake = HANDSHAKE % {
                'origin': origin,
                'port': self.__server.port,
                'bind': self.__server.host
            }
        self.transport.write(handshake)

        return True
