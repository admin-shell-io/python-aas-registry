'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

import logging
import os
import sys
import threading
import time
from datetime import datetime
from importlib import import_module

from dotenv import load_dotenv
from dotenv.main import find_dotenv

try:
    from datastore.datamanager import DataManager
except ImportError:
    from src.main.datastore.datamanager import DataManager

try:
    from handlers.messagehandler import MessageHandler
except ImportError:
    from src.main.handlers.messagehandler import MessageHandler

try:
    from config.aasxconfig import ConfigParser
except ImportError:
    from src.main.config.aasxconfig import ConfigParser

try:
    from datastore.dbadaptor_custom import DB_ADAPTOR
except ImportError:
    from src.main.datastore.dbadaptor_custom import DB_ADAPTOR

try:
    from utils.aaslog import serviceLogHandler, LogList
except ImportError:
    from src.main.utils.aaslog import serviceLogHandler, LogList


class RIC:

    def __init__(self):
        """

        """
        self.reset()
        self.endPointmodules = {}
        self.AASendPointHandles = {}
        self.aas_end_point_handler_objects = {}
        self.aasSkillHandles = {}
        self.AASID = ''
        self.BroadCastMQTTTopic = ''
        self.msgHandler = MessageHandler(self)
        self.skillDetailsDict = {}
        self.skillInstanceDict = {}
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.lia_env_variable = {}
        self.idDict = {}
        self.mCount = 0
        self.service_log_List = LogList()
        self.service_logger = logging.getLogger(
            str(self.__class__.__name__) + ' Service Instance')
        self.file_logger_handler = logging.FileHandler(
            self.base_dir + "/logs/vws_ric.LOG")
        self.command_logger_handler = logging.StreamHandler()
        self.list_handler = serviceLogHandler(self.service_log_List)
        self.handler_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')

    def reset(self) -> None:
        """

        """
        self.AASendPointHandles = {}

    def reconfigure(self) -> None:
        """

        """
        self.stop()
        self.reset()
        self.configure()
        self.start()

    # Configure Service Entities

    def configure_logger(self) -> None:
        """

        """
        self.service_log_List.setMaxSize(maxSize=200)
        self.service_logger.setLevel(logging.DEBUG)

        self.command_logger_handler.setLevel(logging.DEBUG)
        self.file_logger_handler.setLevel(logging.DEBUG)
        self.list_handler.setLevel(logging.DEBUG)

        self.command_logger_handler.setFormatter(self.handler_format)
        self.list_handler.setFormatter(self.handler_format)
        self.file_logger_handler.setFormatter(self.handler_format)

        self.service_logger.addHandler(self.command_logger_handler)
        self.service_logger.addHandler(self.list_handler)
        self.service_logger.addHandler(self.file_logger_handler)

        self.service_logger.info('The service Logger is Configured.')

    def configure_aas_configurer_parser(self) -> None:
        """

        """
        self.aas_configurer = ConfigParser(self)

    def configure_external_variables(self) -> None:
        """

        """
        load_dotenv(find_dotenv())
        self.aas_configurer.setExternalVariables(os.environ)
        self.service_logger.info('External Variables are configured.')

    def configure_aas_id(self) -> None:
        """

        """
        self.AASID = self.aas_configurer.setAASID()
        self.service_logger.info('The AAS ID is configured.')

    def configure_internal_variables(self):
        self.registryAPI = ""
        self.productionSequenceList = []
        self.productionStepList = []
        self.conversationIdList = []
        self.httpEndPointsDict = {}
        self.coapEndPointsDict = {}
        self.connectBotsDict = {}
        self.aasBotsDict = {}
        self.aasBotsDict[self.AASID] = (
            datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        self.mqttGateWayEntries = set()

    def configure_data_adaptor(self) -> None:
        """

        """
        self.dba = DB_ADAPTOR(self)

    def configure_aas_data(self) -> None:
        if self.aas_configurer.configureAASJsonData():
            self.service_logger.info('The External DB is configured')
        else:
            self.shut_down()

    def configure_data_manager(self) -> None:
        """

        """
        self.data_manager = DataManager(self)

    def configure_end_points(self) -> None:
        """

        """
        for endPoint in self.aas_configurer.getAASEndPoints():
            name = endPoint["Name"]
            module = endPoint["Module"]
            if module not in sys.modules:
                self.endPointmodules[module] = import_module(
                    "aasendpointhandlers" + module)

            endpoint = self.endPointmodules[module].AASEndPointHandler(
                self, self.msgHandler)
            self.AASendPointHandles[name] = endpoint

            endpoint.configure()

        self.service_logger.info('The AAS I40 End Points are configured')

    def configure_skills(self) -> None:
        # configure skills
        self.skillDetailsDict = self.aas_configurer.GetAAsxSkills()
        for skill in self.skillDetailsDict.keys():
            skill_module = import_module("." + skill, package="skills")
            skill_baseclass_ = getattr(skill_module, skill)
            skill_instance = skill_baseclass_(self)
            self.skillInstanceDict[skill] = skill_instance
        self.service_logger.info('The skills are configured')

    def configure_skill_webList(self) -> None:
        """

        """
        self.skillListDict = self.skillDetailsDict
        self.skillListWeb = list(self.skillListDict.keys())
        i = 0
        for skillWeb in self.skillListWeb:
            if skillWeb == "ProductionManager":
                del self.skillListWeb[i]
                break
            i = i + 1

    # Start Service Entities

    def start_end_points(self) -> None:
        """

        """

        for module_name, endPointHandler in self.AASendPointHandles.items():
            try:
                endPointHandler.start(self, self.AASID)
                self.aas_end_point_handler_objects[module_name] = endPointHandler
            except Exception as E:
                self.service_logger.info(
                    'The AAS end Points are Started' + str(E))

        self.service_logger.info('The AAS end Points are Started')

    def start_msg_handler(self) -> None:
        """

        """
        msg_handler_thread = threading.Thread(
            target=self.msgHandler.start, args=(
                self.skillInstanceDict, self.aas_end_point_handler_objects,))
        msg_handler_thread.start()

        self.service_logger.info('The message handler started')

    def startSkills(self) -> None:
        """

        """
        # Start remaining skills that are part of the skill instance list
        for skill in self.skillInstanceDict.keys():
            skill_instance_thread = threading.Thread(
                target=self.skillInstanceDict[skill].Start, args=(
                    self.msgHandler, self.skillDetailsDict[skill],))
            skill_instance_thread.start()

        self.service_logger.info('The Skills are Started')

    def start_data_manager(self) -> None:
        """
            This method starts data manager instance as a separate thread
        """
        data_manager_thread = threading.Thread(
            target=self.data_manager.start, args=())
        data_manager_thread.start()

        self.service_logger.info('The message handler started')

    def configure(self):
        """

        """

        # configure Service Logger
        self.configure_logger()
        self.service_logger.info('Configuring the Service Entities.')
        # configure AASXConfigParser
        self.configure_aas_configurer_parser()
        # configure AASID
        self.configure_aas_id()
        # configure External Variables
        self.configure_external_variables()
        # configure registryAPI
        self.configure_internal_variables()
        self.service_logger.info("Configuration Parameters are Set.")

        # configure Data Adaptor
        self.configure_data_adaptor()
        # configure the Data Manager
        self.configure_data_manager()
        self.configure_aas_data()
        # configure EndPoints
        self.configure_end_points()
        # configure Skill
        self.configure_skills()
        self.configure_skill_webList()

    def start(self):
        """

        """
        self.service_logger.info('Starting the Service Entities')
        # start the Data Manager
        self.start_data_manager()
        # start the communication drivers
        self.start_end_points()
        # start the message handler thread
        self.start_msg_handler()
        # start the skills
        self.startSkills()

    def stop(self):
        """

        """
        for module_name, endPointHandler in self.AASendPointHandles.items():
            endPointHandler.stop()

    def shut_down(self):
        self.service_logger.info("The Service Logger is shutting down.")
        os._exit()


if __name__ == "__main__":
    pyAAS = RIC()
    pyAAS.configure()
    pyAAS.start()
    print('Press Ctrl+{0} to exit'.format('C'))
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        pyAAS.stop()
