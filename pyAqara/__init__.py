    ############################################################################
    #                                                                          #
    #                            SUPPORT FOR GATEWAY                           #
    #                                                                          #
    ############################################################################

import socket
import json
import voluptuous as vol
import logging
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

class AqaraGateway:

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ipaddr = '192.168.1.85'
    serverPort = 9898
    multicastAddress = '224.0.0.50'
    multicastPort = 4321

    def __init__(self):
        print ('AqaraGateway Init()')
        self.data = None

    def socketSendMsg(self,cmd):
        ip = self.ipaddr
        port = self.serverPort
        sSocket = self.serverSocket
        
        print ('AqaraGateway socketSendMsg()')

        try:
            print ('AqaraGateway socketSendMsg() - try')
            # sSocket.sendto(bytes(cmd,'utf8'),(ip,port))
            sSocket.connect((ip, int(port)))
            sSocket.send(cmd.encode())
            # sSocket.sendto(cmd,(ip,port))
            recvData, addr = sSocket.recvfrom(4096) # buffer size is 1024 bytes
            # decodedJson = recvData.decode('utf-8')
            print ("response before from gateway lenth :",len(recvData))
            if len(recvData) not "":
                print ("response from gateway lenth :",len(recvData))
                decodedJson = recvData.decode()
                # print ("RHAY AqaraGateway socketSendMsg(): ",decodedJson)
            else
            print ("no response from gateway")
                recvData = None
            # sSocket.close()
        except:
            print ('issue to use socket')
            _LOGGER.error("Aqara Gateway Failed to connect the ip %s", ip)

        if recvData not None:
            try:
                jsonMsg = json.loads(decodedJson)
                # print ("jsonMsg : ",jsonMsg)
                # print ("jsonMsg cmd : ",jsonMsg['cmd'])
                if jsonMsg['cmd'] == "get_id_list":
                    # print ('Gateway json()')
                    return json.loads(jsonMsg['data'])

                elif jsonMsg['cmd'] == "get_id_list_ack":
                    device_SID = json.loads(jsonMsg['data'])
                    return device_SID
                elif jsonMsg['cmd'] == "read_ack":
                    # print ("jsonMsg cmd is Read Ack")
                    # newData = self.getInfoForSid(jsonMsg)
                    # return newData
                    deviceData = json.loads(jsonMsg['data'])
                    # print ("json deviceData: ", deviceData)
                    return float(deviceData['temperature'])/100
                    # return float(jsonMsg['data']['temperature'])/100
            except:
                # print ("issue with the json")
                _LOGGER.error("Aqara Gateway Failed to manage the json")
        else
            return None
     
    def get_devicesList(self):
        # print ('Gateway getDeviceList()')
        devices = []
        cmd = '{"cmd":"get_id_list"}'
        resp = self.socketSendMsg(cmd)
        print (resp)
        # for device in devices:
        #     self.device.append(device)
        # return self.device

        # print self.devices_Sid
        # print "number of devices : ", len(devices)

        # print json.dumps(jsonData, sort_keys=True, indent=4) # convert to formatted json str

    def get_infoForSid(self,msg):
        # print ('RHAY getInfoForSid')
        deviceData = json.loads(msg['data'])
        # print deviceData
        # print ('RHAY temperature', deviceData['temperature'])
        return float(deviceData['temperature'])/100
    
    def get_temperature(self,SID):
        # deviceSID = '158d0001081511'
        print ("get temp")
        cmd = '{"cmd":"read", "sid":"' + SID + '"}'
        # print (cmd)
        resp = self.socketSendMsg(cmd)
        print (resp)
        return resp

    # @property
    # def lastTemp(self):
    #     return self.get_temperature("158d0001143246")