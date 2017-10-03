#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess
import logging
import time
import ConfigParser
import re
import IPMIConf

class IPMIManager(object):  
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('hass.conf')
        self.ip_dict = dict(self.config._sections['ipmi'])
        self.user_dict = dict(self.config._sections['ipmi_user'])
        self.TEMP_LOWER_CRITICAL = 10
        self.TEMP_UPPER_CRITICAL = 80

    def rebootNode(self, node_id):
        code = ""
        message = ""
        base = self._baseCMDGenerate(node_id)
        if base is None:
            raise Exception("node not found , node_name : %s" % node_id)
        try:
            command = base + IPMIConf.REBOOTNODE
            response = subprocess.check_output(command, shell = True)
            if IPMIConf.REBOOTNODE_SUCCESS_MSG in response:
                message = "The Computing Node %s is rebooted." % node_id
                logging.info("IpmiModule rebootNode - The Computing Node %s is rebooted." % node_id)
                code = "0"
        except Exception as e:
            message = "The Computing Node %s can not be rebooted." % node_id
            logging.error("IpmiModule rebootNode - %s" % e)
            code = "1"
        finally:
            result = {"code":code, "node":node_id, "message":message}
            return result

    def startNode(self, node_id):
        code = ""
        message = ""
        base = self._baseCMDGenerate(node_id)
        if base is None:
            raise Exception("node not found , node_name : %s" % node_id)
        try:
            command = base + IPMIConf.STARTNODE
            response = subprocess.check_output(command, shell = True)
            if IPMIConf.STARTNODE_SUCCESS_MSG in response:
                message = "The Computing Node %s is started." % node_id
                logging.info("IpmiModule startNode - The Computing Node %s is started." % node_id)
                code = "0"
        except Exception as e:
            message = "The Computing Node %s can not be started." % node_id
            logging.error("IpmiModule startNode - %s" % e)
            code = "1"
        finally:
            result = {"code":code, "node":nodeID, "message":message}
            return result
            
    def shutOffNode(self, nodeID):
        code = ""
        message = ""
        base = self._baseCMDGenerate(nodeID)
        if base is None:
            raise Exception("node not found , node_name : %s" % node_id)
        try:
            command = base + IPMIConf.SHUTOFFNODE
            response = subprocess.check_output(command, shell = True)
            if IPMIConf.SHUTOFFNODE_SUCCESS_MSG in response:
                message = "The Computing Node %s is shut down." % nodeID
                logging.info("IpmiModule shutOffNode - The Computing Node %s is shut down." % nodeID)
                code = "0"
        except Exception as e:
            message = "The Computing Node %s can not be shut down." % nodeID
            logging.error("IpmiModule shutOffNode - %s" % e)
            code = "1"
        finally:
            result = {"code":code, "node":nodeID, "message":message}
            return result

    def getTempInfoByNode(self, node_id):
        code = ""
        message = ""
        dataList = []

        base = self._baseCMDGenerate(node_id)
        if base is None:
            raise Exception("node not found , node_name : %s" % node_id)
        try:
            command = base + IPMIConf.NODE_CPU_SENSOR_INFO
            p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
            response, err = p.communicate()
            response = response.split("\n")
            dataList = self.dataClean(response , "temperature")
            return int(dataList[2]) # temperature
        except Exception as e:
            code = "1"
            message = "Error! Unable to get computing node : %s's hardware information." % node_id
            logging.error("IpmiModule getNodeInfo - " + err)

    def dataClean(self, raw_data, type=None):
        if type == "temperature":
            return self._tempDataClean(raw_data)

        sensor_id = raw_data[1].split(":")[1].strip()
        device = raw_data[2].split(":")[1].strip()
        sensor_type = raw_data[3].split(":")[1].strip()
        value = raw_data[4].split(":")[1].strip()
        status = raw_data[5].split(":")[1].strip()
        return [sensor_id, device, sensor_type, value, status]

    def _tempDataClean(self , raw_data):

        # data format:
        # Locating sensor record...
        # Sensor ID              : 02-CPU 1 (0x4)
        # Entity ID             : 65.1 (Processor)
        # Sensor Type (Threshold)  : Temperature (0x01)
        # Sensor Reading        : 40 (+/- 0) degrees C
        # Status                : ok
        # Positive Hysteresis   : Unspecified
        # Negative Hysteresis   : Unspecified
        # Minimum sensor range  : 110.000
        # Maximum sensor range  : Unspecified
        # Event Message Control : Global Disable Only
        # Readable Thresholds   : ucr 
        # Settable Thresholds   : 
        # Threshold Read Mask   : ucr 
        # Assertions Enabled    : ucr+ 

        sensor_id = raw_data[1].split(":")[1].strip()
        device = raw_data[2].split(":")[1].strip()
        value = raw_data[4].split(":")[1]
        value = re.findall("[0-9]+", value)[0].strip() # use regular expression to filt
        lower_critical = self.TEMP_LOWER_CRITICAL
        upper_critical = self.TEMP_UPPER_CRITICAL
        return [sensor_id, device, value, lower_critical, upper_critical]

    def getNodeInfoByType(self, node_id, sensor_type_list):
        code = ""
        message = ""
        result_list = []
        base = self._baseCMDGenerate(node_id)
        if base is None:
            raise Exception("node not found , node_name : %s" % node_id)
        for sensor_type in sensor_type_list:
            command = base + IPMIConf.NODEINFO_BY_TYPE % sensor_type
            print command
            try:
                p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
                response, err = p.communicate()
                response = response.split("\n")
                # data clean
                sensor_data = self.dataClean(response)
                result_list.append(sensor_data)
                code = "0"
                message = message + "Successfully get computing node : %s's %s information." % (node_id, sensor_type_list)
                logging.info("IpmiModule getNodeInfo - " + message)
            except Exception as e:
                message = message + "Error! Unable to get computing node : %s's %s information." % (node_id, sensor_type_list)
                logging.error("IpmiModule getNodeInfo - %s" % e)
                code = "1"
                break
        print result_list
        result = {"code":code, "info":result_list, "message":message}
        return result

    def getOSStatus(self, node_id):
        initial = 0
        present = 0
        status = "OK"
        base = self._baseCMDGenerate(node_id)
        if base is None:
            result = {"code" : 1}
            return result
        try:
            command = base + IPMIConf.GET_OS_STATUS
            p = subprocess.Popen(command, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell=True)
            response = p.wait()
            if response != 0:
                raise Exception("Error! The subprocess's command is invalid.")
            while True:
                info = p.stdout.readline()
                if not info:
                    break
                if 'Initial Countdown' in info:
                    initial = int(re.findall("[0-9]+", info)[0]) # find value
                if 'Present Countdown' in info:
                    present = int(re.findall("[0-9]+", info)[0]) # find value
            if (initial - present) > IPMIConf.WATCHDOG_THRESHOLD:
                #print initial - present
                status = "Error"
                return status
            else:
                return status
        except Exception as e:
            logging.error("IpmiModule detectOSstatus - %s" % e)
            status = "IPMI_disable"
            return status

    def getSensorStatus(self, node_id):
        temperature = self.getTempInfoByNode(node_id)
        return self._checkTempValue(temperature)

    def _checkTempValue(self, temperature):
        if temperature > self.TEMP_UPPER_CRITICAL:
            return False
        if temperature < self.TEMP_LOWER_CRITICAL:
            return False
        return "OK"

    def resetWatchDog(self, node_id):
        status = True
        base = self._baseCMDGenerate(node_id)
        if base is None:
            result = {"code" : 1}
            return result
        try:
            command = base + IPMIConf.RESET_WATCHDOG
            response = subprocess.check_output(command, shell = True)
            if IPMIConf.WATCHDOG_RESET_SUCEESS_MSG in responese:
                logging.info("IpmiModule resetWatchDog - The Computing Node %s's watchdog timer has been reset." % node_id)
        except Exception as e:
            logging.error("IpmiModule resetWatchDog - %s" % e)
            status = False
        return status

    def getPowerStatus(self, node_id):
        status = "OK"
        base = self._baseCMDGenerate(node_id)
        if base is None:
            result = {"code" : 1}
            return result
        try:
            command = base + IPMIConf.POWER_STATUS
            response = subprocess.check_output(command, shell = True)
            if IPMIConf.POWER_STATUS_SUCCESS_MSG not in response:
                status = "Error"
            return status
        except Exception as e:
            logging.error("IpmiModule getPowerStatus - The Compute Node %s's IPMI session can not be established." % node_id )
            status = "IPMI_disable"
        return status

    def _baseCMDGenerate(self, node_id):
        if node_id in self.user_dict:
            user = self.user_dict[node_id].split(",")[0]
            passwd = self.user_dict[node_id].split(",")[1]
            cmd = IPMIConf.BASE_CMD % (self.ip_dict[node_id] , user , passwd)
            return cmd
        else:
            return None


if __name__ == "__main__":
    i = IPMIManager()
    print i.checkPowerStatus("compute1")