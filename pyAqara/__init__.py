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


class AqaraGateway:

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ipaddr = '192.168.1.85'
    serverPort = 9898
    multicastAddress = '224.0.0.50'
    multicastPort = 4321
    command = " "
    device = []

    def __init__(self):
        print ('AqaraGateway Init()')
        self.data = None

    def socketSendMsg(self,cmd):
        ip = self.ipaddr
        port = self.serverPort
        sSocket = self.serverSocket
        
        # print ('AqaraGateway socketSendMsg()')

        try:
            # sSocket.sendto(bytes(cmd,'utf8'),(ip,port))
            sSocket.connect((ip, int(port)))
            sSocket.send(cmd.encode())
            # sSocket.sendto(cmd,(ip,port))
            recvData, addr = sSocket.recvfrom(4096) # buffer size is 1024 bytes
            # decodedJson = recvData.decode('utf-8')
            decodedJson = recvData.decode()
            # print ("RHAY AqaraGateway socketSendMsg(): ",decodedJson)
            # sSocket.close()
        except:
            # print ('issue to use socket')
            _LOGGER.error("Aqara Gateway Failed to connect the ip %s", ip)

        try:
            jsonMsg = json.loads(decodedJson)
            # print ("jsonMsg : ",jsonMsg)
            # print ("jsonMsg cmd : ",jsonMsg['cmd'])
            if jsonMsg['cmd'] == "get_id_list":
                # print ('Gateway json()')
                newData = self.getDeviceList(jsonMsg)
                return newData

            elif jsonMsg['cmd'] == "get_id_list_ack":

                devices = json.loads(jsonMsg['data'])
                for device in devices:
                    deviceCmd = '{"cmd":"read", "sid":"' + device + '"}'
                    socketSendMsg(deviceCmd)

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
     
    def getDeviceList(self,msg):
        # print ('Gateway getDeviceList()')
        devices = json.loads(msg['data'])

        for device in devices:

            self.device.append(device)
            # print ('RHAY devices : ', device)

        return self.device

        # print self.devices_Sid
        # print "number of devices : ", len(devices)

        # print json.dumps(jsonData, sort_keys=True, indent=4) # convert to formatted json str

    def getInfoForSid(self,msg):
        # print ('RHAY getInfoForSid')
        deviceData = json.loads(msg['data'])
        # print deviceData
        # print ('RHAY temperature', deviceData['temperature'])
        return float(deviceData['temperature'])/100
    
    def get_temperature(self,SID):
        # deviceSID = '158d0001081511'
        # print ("get temp")
        cmd = '{"cmd":"read", "sid":"' + SID + '"}'
        # print (cmd)
        resp = self.socketSendMsg(cmd)
        return resp

    # @property
    # def lastTemp(self):
    #     return self.get_temperature("158d0001143246")


