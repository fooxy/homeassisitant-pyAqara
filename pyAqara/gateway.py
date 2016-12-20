import socket
import json
import logging
import struct
import collections
import threading
from queue import Queue

_LOGGER = logging.getLogger(__name__)

class AqaraGateway:
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    GATEWAY_IP = None
    GATEWAY_PORT = None
    GATEWAY_SID = None

    MULTICAST_PORT = 9898
    GATEWAY_DISCOVERY_PORT = 4321

    MULTICAST_ADDRESS = '224.0.0.50'
    SOCKET_BUFSIZE = 1024

    def __init__(self):
        self._running = False
        self._queue = None
        self._timeout = 300
        self._devices = collections.defaultdict(list)
        self._deviceCallbacks = collections.defaultdict(list)
        self.socket = None
        self.sids = []
        self.sidsData = []

    def initGateway(self):
        # Send WhoIs in order to get gateway data
        cmd_whois = '{"cmd":"whois"}'
        resp = self.socketSendMsg(cmd_whois)
        self.GATEWAY_IP = resp['ip']
        self.GATEWAY_PORT = int(resp['port'])
        self.GATEWAY_SID = resp['sid']

        cmd_list = '{"cmd":"get_id_list"}'
        self.sids = self.socketSendMsg(cmd_list)

        for sid in self.sids:
            cmd = '{"cmd":"read", "sid":"' + sid + '"}'
            resp = self.socketSendMsg(cmd)
            self.sidsData.append({"sid":resp['sid'],"model":resp['model'],"data":json.loads(resp['data'])})

        self.socket = self._prepare_socket()

# # Unicast Command

    def socketSendMsg(self, cmd):

        if cmd == '{"cmd":"whois"}':
            ip = self.MULTICAST_ADDRESS
            port = self.GATEWAY_DISCOVERY_PORT
        else:
            ip = self.GATEWAY_IP
            port = self.GATEWAY_PORT

        sSocket = self.serverSocket
        try:
            sSocket.settimeout(5.0)
            sSocket.sendto(cmd.encode(), (ip, port))
            sSocket.settimeout(5.0)
            recvData, addr = sSocket.recvfrom(1024)
            if len(recvData) is not None:
                decodedJson = recvData.decode()
            else:
                _LOGGER.error("no response from gateway")
                recvData = None
        except socket.timeout:
            _LOGGER.error(
                "Timeout on socket - Failed to connect the ip %s", ip)
            return None
            sSocket.close()

        if recvData is not None:
            try:
                jsonMsg = json.loads(decodedJson)
                if jsonMsg['cmd'] == 'iam':
                    return jsonMsg
                if jsonMsg['cmd'] == "get_id_list":
                    return json.loads(jsonMsg['data'])
                elif jsonMsg['cmd'] == "get_id_list_ack":
                    devices_SID = json.loads(jsonMsg['data'])
                    return devices_SID
                elif jsonMsg['cmd'] == "read_ack":
                    return jsonMsg
                else:
                    _LOGGER.info("Got unknown response: %s", decodedJson)
            except:
                _LOGGER.error("Aqara Gateway Failed to manage the json")
        else:
            return None

    def sendCmd(self, cmd):
        IP = self.GATEWAY_IP
        PORT = self.GATEWAY_PORT
        sSocket = self.serverSocket
        # print('sendCmd - for IP: ',IP,'with PORT: ',PORT,'with CMD: ',cmd)
        try:
            sSocket.settimeout(5.0)
            sSocket.sendto(cmd.encode("utf-8"), (IP, PORT ))
        except socket.timeout:
            _LOGGER.error(
                "Timeout on socket - Failed to connect the ip %s", IP)

# # Multicast Command

    def _prepare_socket(self):
        print('Connector_prepare_socket()')
        sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP

        sock.bind(("0.0.0.0", self.MULTICAST_PORT))

        mreq = struct.pack("=4sl", socket.inet_aton(self.MULTICAST_ADDRESS),
                           socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,
                        self.SOCKET_BUFSIZE)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        return sock

    def send_command(self, cmd):
        """Send a command to the UDP subject (all related will answer)."""
        self.socket.sendto(json.dumps(cmd).encode("utf-8"),
                           (self.MULTICAST_ADDRESS, self.MULTICAST_PORT))

# # MutliThreading 

    def register(self, callbackID, callback):
        """Register a callback.
        device: device to be updated by subscription
        callback: callback for notification of changes
        """
        if not callbackID:
            _LOGGER.error("Received an invalid device")
            return

        _LOGGER.info("Subscribing to events for %s", callbackID)
        # self._devices[deviceSID].append(deviceSID)
        self._deviceCallbacks[callbackID].append((callback))

    def _log(self, msg):
        """Internal log errors."""
        try:
            self._logger.error(msg)
        except Exception:  # pylint: disable=broad-except
            print('ERROR: ' + msg)

    def _callback_thread(self):
        """Process callbacks from the queue populated by &listen."""
        while self._running:
            packet = self._queue.get(True)
            if isinstance(packet, dict):
                cmd = packet['cmd']
                sid = packet['sid']
                model = packet['model']
                data = packet['data']
                try:
                    if cmd == 'iam':
                        print('iam')
                    elif cmd == 'get_id_list_ack':
                        self.sids = json.loads(data)
                    elif cmd in ["heartbeat", "report", "read_ack"]:
                        if model == 'sensor_ht':
                            for sensor in ('temperature', 'humidity'):
                                callback_id = '{} {}'.format(sensor, sid)
                                for deviceCallback in self._deviceCallbacks.get(callback_id, ()):
                                    deviceCallback(model,
                                                sid,
                                                cmd,
                                                json.loads(data))
                        else:
                            for deviceCallback in self._deviceCallbacks.get(sid, ()):
                                deviceCallback(model,
                                            sid,
                                            cmd,
                                            json.loads(data))
                    elif cmd == 'read_ack':
                        for deviceCallback in self._deviceCallbacks.get(sid, ()):
                            deviceCallback(model,
                                        sid,
                                        cmd,
                                        json.loads(data))

                except Exception as err:  # pylint: disable=broad-except
                    self._log("Exception in aqara gateway callback\nType: " +
                              str(type(err)) + "\nMessage: " + str(err))
            self._queue.task_done()

    def _listen_thread(self):
        """The main &listen loop."""
        # print('gateway _listen_thread()')
        while self._running:
            if self.socket is not None:
                data, addr = self.socket.recvfrom(self.SOCKET_BUFSIZE)
                try:
                    payload = json.loads(data.decode("utf-8"))
                    # print('gateway listen_thread() - payload: ',payload)
                    self._queue.put(payload)
                except Exception as e:
                    raise
                    _LOGGER.error("Can't handle message %r (%r)" % (data, e))

        self._queue.put({})  # empty item to ensure callback thread shuts down

    def stop(self):
        """Stop listening."""
        self._running = False
        self.socket.close()
        self.socket = None

    def listen(self, timeout=(5, 300)):
        """Start the &listen long poll and return immediately."""
        # print('gateway listen()')
        if self._running:
            return False
        self._queue = Queue()
        self._running = True
        self._timeout = timeout
        threading.Thread(target=self._listen_thread, args=()).start()
        threading.Thread(target=self._callback_thread, args=()).start()
        return True
