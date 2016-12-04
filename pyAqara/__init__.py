    ############################################################################
    #                                                                          #
    #                            SUPPORT FOR GATEWAY                           #
    #                                                                          #
    ############################################################################

import socket
import json
import logging

_LOGGER = logging.getLogger(__name__)

class AqaraGateway:

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ipaddr = None
    serverPort = None
    multicastAddress = '224.0.0.50'
    multicastPort = 4321

    def __init__(self):
        self.data = None
        self.get_gatewayConnexionData()

    def socketSendMsg(self,cmd):

        sSocket = self.serverSocket

        if cmd == '{"cmd": "whois"}':
            ip = self.multicastAddress
            port = self.multicastPort
        else:
            ip = self.ipaddr
            port = self.serverPort

        try:
            sSocket.settimeout(5.0)
            sSocket.sendto(cmd.encode(),(ip,port))
            sSocket.settimeout(5.0)
            recvData, addr = sSocket.recvfrom(1024) # buffer size is 1024 bytes / s.recv() for TCP
            if len(recvData) is not None:
                decodedData = recvData.decode()
            else:
                _LOGGER.error("no response from gateway")
                recvData = None
        except socket.timeout:
            _LOGGER.error("Timeout on socket - Failed to connect the ip %s", ip)
            return None
            sSocket.close()
        if recvData is not None:
            try:
                jsonMsg = json.loads(decodedData)
                if jsonMsg['cmd'] == "iam":
                    return jsonMsg
                elif jsonMsg['cmd'] == "get_id_list":
                    return json.loads(jsonMsg)
                elif jsonMsg['cmd'] == "get_id_list_ack":
                    devices_SID = json.loads(jsonMsg['data'])
                    return devices_SID
                elif jsonMsg['cmd'] == "read_ack":
                    return jsonMsg
                else:
                    return None
            except:
                _LOGGER.error("Aqara Gateway Failed to manage the json")
        else:
            return None
     
    def get_devicesList(self):
        cmd = '{"cmd":"get_id_list"}'
        resp = self.socketSendMsg(cmd)
        return resp
    
    def get_model(self,SID):
        cmd = '{"cmd":"read", "sid":"' + SID + '"}'
        resp = self.socketSendMsg(cmd)
        return resp['model']

    def get_temperature(self,SID):
        cmd = '{"cmd":"read", "sid":"' + SID + '"}'
        resp = self.socketSendMsg(cmd)
        respData = json.loads(resp['data'])
        return float(respData['temperature'])/100

    def get_humidity(self,SID):
        cmd = '{"cmd":"read", "sid":"' + SID + '"}'
        resp = self.socketSendMsg(cmd)
        respData = json.loads(resp['data'])
        return float(respData['humidity'])/100

    def get_gatewayConnexionData(self):
        cmd = '{"cmd": "whois"}'
        resp = self.socketSendMsg(cmd)
        self.ipaddr = resp['ip']
        self.serverPort = int(resp['port'])
