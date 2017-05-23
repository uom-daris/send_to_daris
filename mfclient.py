import datetime
import os
import re
import time
import xml.etree.ElementTree as ElementTree
import threading
import urllib
import os
import struct
import socket
import ssl
import base64
import time


def get_xml_header(version='1.0', encoding='UTF-8'):
    return '<?xml version="' + version + '" encoding="UTF-8"?>'


class XmlElement(object):
    def __init__(self, elem=None, name=None, attrib=None, value=None):
        if elem is not None:
            if name is not None:
                raise ValueError("Expecting 'elem' or 'name'. Found both.")
            if not isinstance(elem, ElementTree.Element):
                raise TypeError("'elem' must be an instance of xml.etree.ElementTree.Element.")
            self._elem = elem
        else:
            if name is None:
                raise ValueError("Expecting 'elem' or 'name'. Found none.")
            if attrib is None:
                attrib = {}
            else:
                if isinstance(attrib, dict):  # dictionary
                    attrib = {str(k): str(attrib[k]) for k in attrib.keys()}
                else:
                    raise ValueError("'attrib' must be an instance of dictionary.")
            idx = name.find(':')
            if idx >= 0:
                ns = name[0:idx]
                self._elem = ElementTree.Element('{' + ns + '}' + name[idx + 1:], attrib=attrib)
            else:
                self._elem = ElementTree.Element(name, attrib=attrib)
            if value is not None:
                self._elem.text = str(value)
        self._nsmap = {}
        self._register_namespace(self._elem)

    def _register_namespace(self, elem):
        tag = elem.tag
        if tag.startswith('{'):
            ns = tag[1:tag.rfind('}')]
            self._nsmap[ns] = ns
        for subelem in list(elem):
            self._register_namespace(subelem)

    @property
    def tag(self):
        if self._elem.tag.startswith('{'):
            idx = self._elem.tag.find('}')
            ns = self._elem.tag[1:idx]
            name = self._elem.tag[idx + 1:]
            return ns + ':' + name
        else:
            return self._elem.tag

    @property
    def attrib(self):
        return self._elem.attrib.copy()

    @property
    def text(self):
        return self._elem.text

    def name(self):
        return self.tag

    def attributes(self):
        return self.attrib

    def attribute(self, name):
        return self.attrib.get(name)

    def set_attribute(self, name, value):
        self.attrib.set(name, str(value))

    def value(self, xpath=None, default=None):
        if xpath is None:
            return self._elem.text
        else:
            idx = xpath.rfind('/@')
            if idx == -1:
                return self._elem.findtext(xpath, default=default, namespaces=self._nsmap)
            else:
                se = self._elem.find(xpath[:idx], namespaces=self._nsmap)
                if se is not None:
                    value = se.attrib.get(xpath[idx + 2:])
                    return value if value is not None else default

    def int_value(self, xpath=None, default=None, base=10):
        assert default is None or isinstance(default, int)
        value = self.value(xpath)
        if value is not None:
            return int(value, base)
        else:
            return default

    def float_value(self, xpath=None, default=None):
        assert default is None or isinstance(default, float)
        value = self.value(xpath)
        if value is not None:
            return float(value)
        else:
            return default

    def boolean_value(self, xpath=None, default=None):
        assert default is None or isinstance(default, bool)
        value = self.value(xpath)
        if value is not None:
            return value.lower() in ('yes', 'true', '1')
        else:
            return default

    def date_value(self, xpath=None, default=None):
        assert default is None or isinstance(default, datetime.datetime)
        value = self.value(xpath)
        if value is not None:
            return time.strptime(value, '%d-%b-%Y %H:%M:%S')
        else:
            return default

    def set_value(self, value):
        if value is not None:
            if isinstance(value, datetime.datetime):
                self._elem.text = time.strftime('%d-%b-%Y %H:%M:%S', value)
            elif isinstance(value, bool):
                self._elem.text = str(value).lower()
            else:
                self._elem.text = str(value)

    def values(self, xpath=None):
        if xpath is None:
            if self._elem.text is not None:
                return [self._elem.text]
            else:
                return None
        idx = xpath.rfind('/@')
        if idx == -1:
            ses = self._elem.findall(xpath, self._nsmap)
            if ses is not None:
                return [se.text for se in ses]
        else:
            ses = self._elem.findall(xpath[:idx], self._nsmap)
            if ses is not None:
                return [se.attrib.get(xpath[idx + 2:]) for se in ses]

    def element(self, xpath=None):
        if xpath is None:
            ses = list(self._elem)
            return XmlElement(elem=ses[0]) if ses else None
        else:
            idx = xpath.rfind('/@')
            if idx != -1:
                raise ValueError('Invalid element xpath: ' + xpath)
            se = self._elem.find(xpath, self._nsmap)
            if se is not None:
                return XmlElement(elem=se)

    def elements(self, xpath=None):
        if xpath is None:
            ses = list(self._elem)
            if ses:
                return [XmlElement(elem=se) for se in ses]
        else:
            idx = xpath.rfind('/@')
            if idx != -1:
                raise SyntaxError('invalid element xpath: ' + xpath)
            ses = self._elem.findall(xpath, self._nsmap)
            if ses:
                return [XmlElement(elem=se) for se in ses]
            else:
                return None

    def add_element(self, elem, index=None):
        assert elem is not None and isinstance(elem, (ElementTree.Element, XmlElement))
        if isinstance(elem, ElementTree.Element):
            if index is None:
                self._elem.append(elem)
            else:
                self._elem.insert(index, elem)
            self._register_namespace(elem)
        elif isinstance(elem, XmlElement):
            self.add_element(elem._elem, index)

    def tostring(self):
        for ns in self._nsmap.keys():
            ElementTree.register_namespace(ns, self._nsmap.get(ns))
        te = ElementTree.Element('temp')
        te.append(self._elem)
        ts = ElementTree.tostring(te)
        ts = ts[ts.find('>') + 1:len(ts) - 7]
        for nsk in self._nsmap.keys():
            nsv = self._nsmap.get(nsk)

            def replacement(match):
                token = match.group(0)
                if token.endswith(' '):  # ends with space
                    return token + 'xmlns:' + nsk + '="' + nsv + '" '
                else:  # ends with >
                    return token[0:-1] + ' xmlns:' + nsk + '="' + nsv + '">'

            ts = re.sub(r'<' + nsk + ':[a-zA-Z0-9_-]+[\s>]', replacement, ts)
        return ts

    def __str__(self):
        return self.tostring()

    def __getitem__(self, index):
        se = self._elem.__getitem__(index)
        return XmlElement(se) if se is not None else None

    def __len__(self):
        return self._elem.__len__()

    @classmethod
    def parse(cls, source):
        assert source is not None
        if os.path.isfile(source):  # text is a file
            tree = ElementTree.parse(source)
            if tree is not None:
                root = tree.getroot()
                if root is not None:
                    return XmlElement(elem=root)
            else:
                raise ValueError('Failed to parse XML file: ' + source)
        else:
            return XmlElement(ElementTree.fromstring(str(source)))


def _process_attributes(name, attributes):
    attrib = {}
    # add namespace attribute
    idx = name.find(':')
    if idx >= 0:
        ns = name[0:idx]
        ns_attr = 'xmlns:' + ns
        if ns_attr not in attrib:
            attrib[ns_attr] = ns
    # conver to str and remove attribute with value==None
    if attributes is not None:
        for name in attributes.keys():
            value = attributes[name]
            if value is not None:
                attrib[str(name)] = str(value)
    return attrib


class XmlStringWriter(object):
    def __init__(self, root=None):
        self.__stack = []
        self.__items = []
        if root is not None:
            self.push(str(root))

    def doc_text(self):
        self.pop_all()
        return ''.join(self.__items)

    def doc_elem(self):
        return XmlElement.parse(self.doc_text())

    def push(self, name, attributes=None):
        attributes = _process_attributes(name, attributes)
        self.__stack.append(name)
        self.__items.append('<')
        self.__items.append(name)
        for a in attributes.keys():
            self.__items.append(' ')
            self.__items.append(a)
            self.__items.append('="')
            self.__items.append(attributes[a])
            self.__items.append('"')
        self.__items.append('>')

    def pop(self):
        name = self.__stack.pop()
        self.__items.append('</')
        self.__items.append(name)
        self.__items.append('>')

    def pop_all(self):
        while len(self.__stack) > 0:
            self.pop()

    def add(self, name, value, attributes=None):
        attributes = _process_attributes(name, attributes)
        self.__items.append('<')
        self.__items.append(name)
        for a in attributes.keys():
            self.__items.append(' ')
            self.__items.append(a)
            self.__items.append('="')
            self.__items.append(attributes[a])
            self.__items.append('"')
        self.__items.append('>')
        self.__items.append(str(value))
        self.__items.append('</')
        self.__items.append(name)
        self.__items.append('>')

    def add_element(self, element, parent=True):
        if element is None:
            raise ValueError('element is not specified.')
        if isinstance(element, ElementTree.Element) or isinstance(element, XmlElement):
            if parent is True:
                if isinstance(element, ElementTree.Element):
                    self.__items.append(XmlElement(element).tostring())
                else:
                    self.__items.append(element.tostring())
            else:
                for sub_element in list(element):
                    self.add_element(sub_element, parent=True)
        else:
            elem = XmlElement.parse(str(element))
            self.add_element(elem, parent)


class XmlDocWriter(object):
    def __init__(self, root=None):
        self.__stack = []
        self.__tb = ElementTree.TreeBuilder()
        if root is not None:
            self.push(root)

    def doc_text(self):
        return str(self.doc_elem())

    def doc_elem(self):
        self.pop_all()
        return XmlElement(self.__tb.close())

    def push(self, name, attributes=None):
        attributes = _process_attributes(name, attributes)
        self.__stack.append(name)
        self.__tb.start(name, attributes)

    def pop(self):
        name = self.__stack.pop()
        if name is not None:
            self.__tb.end(name)

    def pop_all(self):
        while len(self.__stack) > 0:
            self.pop()

    def add(self, name, value, attributes=None):
        attributes = _process_attributes(name, attributes)
        self.__tb.start(name, attributes)
        self.__tb.data(str(value))
        self.__tb.end(name)

    def add_element(self, element, parent=True):
        if element is None:
            raise ValueError('element is not specified.')
        if isinstance(element, ElementTree.Element) or isinstance(element, XmlElement):
            if parent is True:
                self.__tb.start(element.tag, element.attrib)
                if element.text is not None:
                    self.__tb.data(element.text)
            for sub_element in list(element):
                self.add_element(sub_element, parent=True)
            if parent is True:
                self.__tb.end(element.tag)
        else:
            self.add_element(ElementTree.fromstring(str(element)), parent)

##############################################################################

BUFFER_SIZE = 8192
RECV_TIMEOUT = 10.0
SVC_URL = '/__mflux_svc__/'


class MFConnection(object):
    _SEQUENCE_GENERATOR = 0
    _SEQUENCE_ID = 0
    _LOCK = threading.RLock()

    @classmethod
    def sequence_generator(cls):
        with cls._LOCK:
            return cls._SEQUENCE_GENERATOR

    @classmethod
    def set_sequence_generator(cls, sequence_generator):
        with cls._LOCK:
            cls._SEQUENCE_GENERATOR = sequence_generator

    @classmethod
    def __next_sequence_id(cls):
        with cls._LOCK:
            cls._SEQUENCE_ID += 1
            return cls._SEQUENCE_ID

    def __init__(self, host, port, encrypt, proxy=None, app=None,
                 protocols=None, timeout=None, recv_timeout=RECV_TIMEOUT, compress=False, cookie=None):
        self._host = host
        self._port = port
        self._encrypt = encrypt
        self._domain = None
        self._user = None
        self._password = None
        self._token = None
        self._proxy = proxy
        self._app = app
        self._protocols = protocols
        self._session = None
        self._session_id = None
        self._token = None
        self._token_type = None
        self._lock = threading.RLock()
        self._timeout = timeout
        self._recv_timeout = recv_timeout
        self._compress = compress
        self._cookie = cookie
        self._session_timeout = -1
        self._last_send_time = -1
        self._sock = None

    @property
    def session(self):
        return self._session

    def __open_socket(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self._timeout)
        if self._proxy is not None:
            (proxy_host, proxy_port, proxy_user, proxy_password) = self._proxy
            self._sock.connect((proxy_host, proxy_port))
            f = self._sock.makefile('r+')
            try:
                f.write('CONNECT ' + self._host + ':' + self._port + ' HTTP/1.1\r\n')
                f.write('Host: ' + self._host + ':' + self._port + '\r\n')
                if proxy_user is not None and proxy_password is not None:
                    f.write(
                        'Proxy-Authorization: Basic ' + base64.b64encode(
                            proxy_user + ':' + proxy_password) + '\r\n')
                f.write('\r\n')
                f.flush()
                line = f.readline().rstrip('\r\n').strip()
                if len(line) == 0 or not line.startswith('HTTP/') or line.count(' ') < 2:
                    raise ExHttpResponse('Invalid HTTP response: ' + line)
                (version, status, message) = line.split()
                version = version[5:]
                if status != '200':
                    raise ExHttpResponse('Unexpected HTTP ' + version + ' response: ' + status + ' ' + message)
            except:
                f.close()
                self._sock.close()
                raise  # re-throw exception
            finally:
                f.close()
        else:
            self._sock.connect((self._host, self._port))
        if self._encrypt:
            self._sock = ssl.wrap_socket(self._sock)

    def __close_socket(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def set_app(self, app):
        self._app = app

    def set_protocols(self, protocols):
        self._protocols = protocols

    def set_recv_timeout(self, recv_timeout):
        self._recv_timeout = recv_timeout

    def set_timeout(self, timeout):
        self._timeout = timeout

    def connect(self, domain=None, user=None, password=None, token=None):
        if not (domain and user and password) and not token and not self._session:
            raise ValueError('Cannot open connection: No user credentials or secure identity token is specified.')
        with self._lock:
            w = XmlStringWriter('args')
            if self._app is not None:
                w.add('app', self._app)
            w.add('host', self._host)
            if domain and user and password:
                self._domain = domain
                self._user = user
                self._password = password
                w.add('domain', domain)
                w.add('user', user)
                w.add('password', password)
            elif token:
                w.add('token', token)
                self._token = token
            else:
                w.add('sid', self._session)
            rxe = self.execute('system.logon', args=w.doc_text())
            self._session = rxe.value('session')
            self._session_id = rxe.int_value('session/@id')
            self._session_timeout = rxe.int_value('session/@timeout', 600000) * 1000
            self._last_send_time = int(round(time.time() * 1000))
            return self._session

    def disconnect(self):
        if not self._session:
            return
        with self._lock:
            try:
                self.execute('system.logoff')
            finally:
                self._session = None

    def execute(self, service, args=None, inputs=None, outputs=None, route=None, emode=None):
        sgen = MFConnection.sequence_generator()
        seq = MFConnection.__next_sequence_id()
        # create request message
        request = MFRequest(sgen, seq, service, args, inputs, outputs, route, emode, self._session,
                            (self._token, self._token_type), self._app, self._protocols, self._compress)
        try:
            # open socket
            self.__open_socket()
            # send http header
            self.__send_http_header(request.length)
            # send http request
            request.send(self._sock)
            # receive http response
            response = MFResponse(outputs)
            response.recv(self._sock)
            if response.error is not None:
                raise ExHttpResponse(str(response.error))
            return response.result
        finally:
            self.__close_socket()

    def __send_http_header(self, content_length):
        header = 'POST '
        if self._encrypt:
            header += 'https://'
        else:
            header += 'http://'
        if self._host.find(':') != -1:
            header = header + '[' + self._host + ']' + ':' + self._port + SVC_URL + ' HTTP/1.1\r\n'
        else:
            header = header + self._host + ':' + str(self._port) + SVC_URL + ' HTTP/1.1\r\n'
        header += 'Host: ' + self._host + ':' + str(self._port) + '\r\n'
        header += 'User-Agent: Mediaflux/3.0\r\n'
        header += 'Connection: keep-alive\r\n'
        header += 'Keep-Alive: 300\r\n'
        if self._proxy is not None:
            header += 'Proxy-Connection: keep-alive\r\n'
            (proxy_host, proxy_port, proxy_user, proxy_password) = self._proxy
            if proxy_user:
                header += 'Proxy-Authorization: Basic ' + base64.b64encode(proxy_user + '.' + proxy_password) + '\r\n'
        if self._cookie is not None:
            header += 'Cookie: ' + self._cookie + '\r\n'
        header += 'Content-Type: application/mflux\r\n'
        if content_length == -1:
            header += 'Transfer-Encoding: chunked\r\n'
        else:
            header += 'Content-Length: ' + str(content_length) + '\r\n'
        header += '\r\n'
        self._sock.sendall(header)


class MFInput(object):
    def __init__(self, path, mime_type=None, calc_csum=False):
        self.__checksum = None
        if path.startswith('http:') or path.startswith('https:') or path.startswith('ftp:'):
            self.__url = path
            self.__type = None
            self.__length = -1
            resp = None
            try:  # probe the mime type and length
                resp = urllib.urlopen(self.__url).info()
                self.__type = resp.type
                self.__length = long(resp.getheaders('Content-Length')[0])
            except:
                pass
            finally:
                if resp is not None:
                    resp.close()
        else:
            if path.startswith('file:'):
                path = path[5:]
            self.__url = 'file:' + os.path.abspath(path)
            self.__type = mime_type
            self.__length = os.path.getsize(path)
            if calc_csum:
                self.__checksum = crc32(path)

    def type(self):
        return self.__type

    def set_type(self, mime_type):
        self.__type = mime_type

    def length(self):
        return self.__length

    def url(self):
        return self.__url

    def checksum(self):
        return self.__checksum

    def set_checksum(self, checksum):
        self.__checksum = checksum


class MFOutput(object):
    def __init__(self, path):
        self._path = os.path.abspath(path)
        self._mime_type = None

    def path(self):
        return self._path

    def url(self):
        if self._path:
            return 'file:' + self._path
        else:
            return None

    def set_mime_type(self, mime_type):
        self._mime_type = mime_type

    def mime_type(self):
        return self._mime_type


class MFRequest(object):
    class Packet(object):
        def __init__(self, string=None, url=None, length=None, mime_type=None, compress=False,
                     buffer_size=BUFFER_SIZE):
            if string:
                self._bytes = string.encode('utf-8')
                self._url = None
                self._length = len(self._bytes)
            elif url:
                self._bytes = None
                self._url = url
                self._length = length
            else:
                raise ValueError('Either str or url argument is required.')
            self._type = mime_type
            self._compress = compress
            self._buffer_size = buffer_size

        @property
        def url(self):
            return self._url

        @property
        def length(self):
            return self._length

        @property
        def type(self):
            return self._type

        @property
        def compress(self):
            return self._compress

        def send(self, sock, remaining):
            self.__send_header(sock, remaining)
            self.__send_content(sock)

        def __send_header(self, sock, remaining):
            header = '\x01'
            header += '\x01' if self._compress else '\x00'
            assert len(header) == 2
            header += struct.pack('!q', self._length)
            assert len(header) == 10
            header += struct.pack('!i', remaining)
            assert len(header) == 14
            if self._type is None:
                header += struct.pack('>h', 0)
                assert len(header) == 16
            else:
                mime_type = self._type.encode('utf-8')
                header += struct.pack('>h', len(mime_type))
                assert len(header) == 16
                header += mime_type
            sock.sendall(header)

        def __send_content(self, sock):
            if self._bytes is not None:
                sock.sendall(self._bytes)
            elif self._url is not None:
                f = open(self._url[5:]) if self._url.startswith('file:') else urllib.urlopen(self._url)
                try:
                    chunk = f.read(self._buffer_size)
                    while len(chunk) > 0:
                        sock.sendall(chunk)
                        chunk = f.read(self._buffer_size)
                finally:
                    f.close()

    def __init__(self, sgen, seq, service, args=None, inputs=None, outputs=None, route=None, emode=None, session=None,
                 token=None, app=None,
                 protocols=None, compress=False):
        self.__packets = []
        # service request/message packet
        xml = self.__create_request_xml(sgen, seq, service, args, inputs, outputs, route, emode, session,
                                        token, app, protocols)
        self.__packets.append(MFRequest.Packet(string=xml, mime_type='text/xml', compress=compress))
        if inputs is not None:
            for mi in inputs:
                self.__packets.append(
                    MFRequest.Packet(url=mi.url(), length=mi.length(), mime_type=mi.type(),
                                     compress=False))

    @classmethod
    def __create_request_xml(cls, sgen, seq, service, args=None, inputs=None, outputs=None, route=None, emode=None,
                             session=None, token=None, app=None, protocols=None):
        assert emode is None or emode == 'distributed-first' or emode == 'distributed-all'
        w = XmlStringWriter('request')
        if protocols is not None:
            for protocol in protocols:
                w.add('output-protocol', protocol)
        token_str, token_type = token if type(token) is tuple else (token, None)
        outputs = [] if outputs is None else outputs
        outputs = [outputs] if not isinstance(outputs, list) else outputs
        nb_outputs = len(outputs)
        data_out_min, data_out_max = (None, None) if nb_outputs == 0 else(nb_outputs, nb_outputs)
        w.push('service',
               {'emode': emode, 'target': route, 'name': service, 'session': session, 'token-type': token_type,
                'token': token_str, 'app': app, 'sgen': str(sgen), 'seq': str(seq), 'data-out-min': data_out_min,
                'data-out-max': data_out_max})
        if args is not None:
            w.add_element(args, True)
        if inputs is not None and len(inputs) > 0:
            for mi in inputs:
                w.push('attachment')
                if mi.url():
                    w.add('source', mi.url())
                if mi.checksum():
                    w.add('csum', str(mi.checksum()))
                w.pop()
        w.pop()
        return get_xml_header() + w.doc_text()

    @property
    def length(self):
        length = long(0)
        for packet in self.__packets:
            if packet.length == -1:
                return long(-1)
            length += 16
            if packet.type:
                length += len(packet.type.encode('utf-8'))
            length += packet.length
        return length

    def send(self, sock):
        remaining = len(self.__packets) - 1
        for packet in self.__packets:
            packet.send(sock, remaining)
            remaining -= 1

    def __getitem__(self, index):
        return self.__packets.__getitem__(index)

    def __len__(self):
        return self.__packets.__len__()


class MFResponse(object):
    def __init__(self, outputs):
        if outputs is None:
            self._outputs = []
        else:
            if not isinstance(outputs, list):
                assert isinstance(outputs, MFOutput)
                self._outputs = [outputs]
            else:
                self._outputs = outputs
        self._http_version = None
        self._http_status_code = None
        self._http_status_message = None
        self._http_header_fields = {}
        self._result = None
        self._error = None

    @property
    def result(self):
        return self._result

    @property
    def error(self):
        return self._error

    def recv(self, sock):
        bytes_received = self.__recv_header(sock)
        pkt_idx = 0  # packet index
        while True:
            bytes_length = len(bytes_received)
            if bytes_length < 16:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    raise ExHttpResponse('Incomplete packet ' + pkt_idx + '.')
                else:
                    bytes_received += data
                    continue
            pkt_length = struct.unpack('>q', bytes_received[2:10])[0]
            pkt_remaining = struct.unpack('>i', bytes_received[10:14])[0]
            pkt_mime_type_length = struct.unpack('>h', bytes_received[14:16])[0]
            if pkt_mime_type_length <= 0:
                bytes_received = self.__recv_packet(sock, pkt_idx, pkt_length, None, bytes_received, pkt_remaining)
                pkt_idx += 1
            else:
                if bytes_length < (16 + pkt_mime_type_length):
                    data = sock.recv(BUFFER_SIZE)
                    if not data:
                        raise ExHttpResponse('Incomplete packet ' + pkt_idx + '.')
                    else:
                        bytes_received += data
                        continue
                pkt_mime_type = bytes_received[16:16 + pkt_mime_type_length]
                bytes_received = bytes_received[16 + pkt_mime_type_length:]
                bytes_received = self.__recv_packet(sock, pkt_idx, pkt_length, pkt_mime_type, bytes_received,
                                                    pkt_remaining)
                pkt_idx += 1
            if pkt_remaining == 0:
                break

    def __recv_packet(self, sock, idx, length, mime_type, bytes_received, remaining):
        n = len(bytes_received)
        if idx == 0:  # first packet: result/error xml
            while len(bytes_received) < length:
                data = sock.recv(BUFFER_SIZE)
                if not data:
                    raise ExHttpResponse('Incomplete packet ' + idx + '.')
                bytes_received += data
            self.__parse_reply(bytes_received[0:length])
            bytes_received = bytes_received[length:]
            # now check outputs
            nb_outputs = len(self._outputs)
            if remaining != nb_outputs:
                raise ExHttpResponse('Mismatch number of service outputs. Expecting ' + str(nb_outputs) +
                                     ', found ' + str(remaining))
        else:
            output = self._outputs[idx - 1]
            if mime_type:
                output.set_mime_type(mime_type)
            with open(output.path(), 'wb') as f:
                if n < length:
                    if n > 0:
                        f.write(bytes_received)
                        f.flush()
                        #print('written: ' + str(n))
                    while n < length:
                        data = sock.recv(BUFFER_SIZE)
                        if not data:
                            raise IOError('Failed to receive data for packet: ' + idx)
                        if n + len(data) < length:
                            f.write(data)
                            n += len(data)
                        else:
                            f.write(data[0:length - n])
                            bytes_received = data[length - n:]
                            n = length
                        f.flush()
                        #print('written: ' + str(n))
                else:
                    f.write(bytes_received[0:length])
                    bytes_received = bytes_received[length:]
        return bytes_received

    def __parse_reply(self, text):
        rxe = XmlElement.parse(text)
        reply_type = rxe.value('reply/@type')
        if reply_type == 'result':
            self._result = rxe.element('reply/result')
        else:
            assert reply_type == 'error'
            self._error = rxe.element('reply')

    def __recv_header(self, sock):
        # receive header
        header = ''
        bytes_received = ''
        completed = False
        while not completed:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                break
            end = data.find('\r\n\r\n')  # end of header
            if end >= 0:
                header += data[0:end]
                completed = True
                bytes_received += data[end + 4:]
                break
            else:
                header += data
        if not completed:
            raise ExHttpResponse('Failed to receive http header. Incomplete header: ' + header)
        # parse header fields
        self.__parse_header(header)
        # handle status code
        if not self._http_status_code:
            raise ExHttpResponse("Invalid http response: missing status code.")
        if not self._http_status_message:
            raise ExHttpResponse("Invalid http response: missing status message.")
        if self._http_status_code == '200':
            # 200: success
            return bytes_received
        elif self._http_status_code == '407':
            # 407: proxy auth required
            raise ExProxyAuthenticationRequired('Proxy authentication required.')
        else:
            # Other failed status(errors)
            if 'Content-Type' in self._http_header_fields and 'Content-Length' in self._http_header_fields:
                # Error with content/message.
                content_type = self._http_header_fields['Content-Type']
                content_length = long(self._http_header_fields['Content-Length'])
                idx = content_type.find('charset=')
                encoding = None if idx == -1 else content_type[idx + 8:]
                content = ''
                while True:
                    data = sock.recv(BUFFER_SIZE)
                    content += data
                    if data == '' or len(content) >= content_length:
                        break
                    if encoding is not None:
                        content = content.decode(encoding)
                raise ExHttpResponse(
                    'Invalid HTTP/' + self._http_version + ' response: ' + self._http_status_code + ' ' +
                    self._http_status_message + '. Content: ' + content)
            else:
                # Error without content/message
                raise ExHttpResponse(
                    'Invalid HTTP/' + self._http_version + ' response: ' + self._http_status_code + ' ' +
                    self._http_status_message + '.')

    def __parse_header(self, header):
        lines = header.split('\r\n')
        idx1 = lines[0].find('HTTP/') + 5
        idx2 = lines[0].find(' ', idx1)
        self._http_version = lines[0][idx1:idx2]
        idx3 = idx2 + 1
        idx4 = lines[0].find(' ', idx3)
        self._http_status_code = lines[0][idx3:idx4]
        self._http_status_message = lines[0][idx4 + 1:]
        lines = lines[1:]
        self._http_header_fields = {}
        for line in lines:
            kv = line.split(':')
            self._http_header_fields[kv[0]] = kv[1].strip()


class ExNotConnected(Exception):
    pass


class ExHttpResponse(Exception):
    pass


class ExProxyAuthenticationRequired(Exception):
    pass


def crc32(path):
    from zlib import crc32
    with open(path, 'r') as f:
        crc = crc32('')
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            crc = crc32(data, crc)
    return crc
