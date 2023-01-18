'''
Copyright (c) 2021-2022 Otto-von-Guericke-Universitaet Magdeburg, Lehrstuhl Integrierte Automation
Author: Harish Kumar Pakala
This source code is licensed under the Apache License 2.0 (see LICENSE.txt).
This source code may use other Open Source software components (see LICENSE.txt).
'''

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from importlib import import_module
import os.path 
import sys

try:
    from config import aasxconfig as aasxconfig
except ImportError:
    from main.config import aasxconfig as aasxconfig

data_dir = os.path.join(aasxconfig.script_dir, "data")


class Scheduler(object):
    """
    The scheduler of the Administration Shell
    """

    def __init__(self, pyAAS):
        """Reads the configuration and (re-)starts.

        This function reads the XML-based configuration file and
        initializes the scheduler.

        """
        self.pyAAS = pyAAS
        self.f_modules = {}

        # set the defaults for the scheduler, which can not be changed
        # by configuration files
        # db_path = os.path.join(data_dir, 'jobs.sqlite')
        # db_url = ''.join(['sqlite:///', db_path])
        jobstores = {
            # 'default': SQLAlchemyJobStore(url=db_url)
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(20),
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }

        # initialize the scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores, executors=executors, job_defaults=job_defaults)
        self.triggers = {}

    def configure(self, aasxconfig):
        """Configures the triggers and jobs out of the given configuration

        :param lxml.etree.ElementTree configuration: XML DOM tree of
        the configuration

        """
        
        # add each trigger of the configuration to the scheduler
        triggerList = aasxconfig.GetTriggersList()
        for trigger_xe in triggerList:
            trigger_type = trigger_xe.tag
            trigger_id = trigger_xe.attrib["ID"]

            if trigger_type == "DateTrigger":
                kwargs = {}
                kwargs["run_date"] = trigger_xe.attrib["RunDateTime"]
                if "TimeZone" in trigger_xe.attrib:
                    kwargs["timezone"] = trigger_xe.attrib["TimeZone"]
                self.triggers[trigger_id] = DateTrigger(**kwargs)

            elif trigger_type == "IntervalTrigger":
                kwargs = {}
                if "Weeks" in trigger_xe.attrib:
                    kwargs["weeks"] = int(trigger_xe.attrib["Weeks"])
                if "Days" in trigger_xe.attrib:
                    kwargs["days"] = int(trigger_xe.attrib["Days"])
                if "Hours" in trigger_xe.attrib:
                    kwargs["hours"] = int(trigger_xe.attrib["Hours"])
                if "Minutes" in trigger_xe.attrib:
                    kwargs["minutes"] = int(trigger_xe.attrib["Minutes"])
                if "Seconds" in trigger_xe.attrib:
                    kwargs["seconds"] = int(trigger_xe.attrib["Seconds"])
                if "StartDateTime" in trigger_xe.attrib:
                    kwargs["start_date"] = trigger_xe.attrib["StartDateTime"]
                if "EndDateTime" in trigger_xe.attrib:
                    kwargs["end_date"] = trigger_xe.attrib["EndDateTime"]
                if "TimeZone" in trigger_xe.attrib:
                    kwargs["timezone"] = trigger_xe.attrib["TimeZone"]
                self.triggers[trigger_id] = IntervalTrigger(**kwargs)

            elif trigger_type == "CronTrigger":
                kwargs = {}
                if "Year" in trigger_xe.attrib:
                    kwargs["year"] = trigger_xe.attrib["Year"]
                if "Month" in trigger_xe.attrib:
                    kwargs["month"] = trigger_xe.attrib["Month"]
                if "Day" in trigger_xe.attrib:
                    kwargs["day"] = trigger_xe.attrib["Day"]
                if "Week" in trigger_xe.attrib:
                    kwargs["week"] = trigger_xe.attrib["Week"]
                if "WeekDay" in trigger_xe.attrib:
                    kwargs["day_of_week"] = trigger_xe.attrib["WeekDay"]
                if "Hour" in trigger_xe.attrib:
                    kwargs["hour"] = trigger_xe.attrib["Hour"]
                if "Minute" in trigger_xe.attrib:
                    kwargs["minute"] = trigger_xe.attrib["Minute"]
                if "Second" in trigger_xe.attrib:
                    kwargs["second"] = trigger_xe.attrib["Second"]
                if "StartDateTime" in trigger_xe.attrib:
                    kwargs["start_date"] = trigger_xe.attrib["StartDateTime"]
                if "EndDateTime" in trigger_xe.attrib:
                    kwargs["end_date"] = trigger_xe.attrib["EndDateTime"]
                if "TimeZone" in trigger_xe.attrib:
                    kwargs["timezone"] = trigger_xe.attrib["TimeZone"]
                self.triggers[trigger_id] = CronTrigger(**kwargs)

            else:
                raise Exception(
                    "This PYAAS implementation can not handle the trigger type '{0}'".format(trigger_type))

            job_xes = trigger_xe.xpath("./Job")
            for job_xe in job_xes:
                job_id = job_xe.attrib["ID"]
                module_name = job_xe.attrib["Function"]
                params = [self.saas]
                param_xes = job_xe.xpath("./*")
                for param_xe in param_xes:
                    if param_xe.tag == "ChannelRef":
                        params.append(param_xe.attrib["RefID"])
                    elif param_xe.tag == "Constant":
                        t = param_xe.attrib["Type"]
                        v = param_xe.attrib["Value"]
                        if t == "str":
                            params.append(str(v))
                        if t == "int":
                            params.append(int(v))
                        if t == "float":
                            params.append(float(v))
                    else:
                        raise Exception("ERROR: Disallowed Job parameter")
                if module_name not in sys.modules:
                    self.f_modules[module_name] = import_module("modules" + module_name)
                f = self.f_modules[module_name].function
                trigger = self.triggers[trigger_id]
                self.scheduler.add_job(f, trigger=trigger, args=params, id=job_id, replace_existing=True)
                # NOTE from the apscheduler documentation:
                # If you schedule jobs in a persistent job store during your
                # application's initialization, you MUST define an explicit ID
                # for the job and use replace_existing=True or you will get a
                # new copy of the job every time your application restarts!

    def start(self):
        """Runs the scheduler.

        After the scheduler has been started, we can no longer alter
        its settings.

        """
        self.scheduler.start()

    def stop(self):
        self.scheduler.shutdown()
