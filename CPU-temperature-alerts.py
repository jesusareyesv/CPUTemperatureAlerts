import os
import sys
import threading
import time
import argparse

class Core:
    def __init__(self,number,label,max_t,crit,crit_alarm,actual_temp,rute):
        self.core_number = number
        self.label = label
        self.max_temp = max_t
        self.critical_temperature = crit
        self.crit_alarm = crit_alarm
        self.actual_temp = actual_temp
        self.input_rute = rute
        self.temperatures = []

        self.flag_core_temp = False
        self.flag_core_deltatemp = False
        self.counter_fct = 0
        self.counter_fcdt = 0
        self.deltaT_max = 5
        self.dtime_bypass = 20
        self.ddtime_bypass = 10

    def __init__(self):
        self.core_number = None
        self.label = None
        self.max_temp = None
        self.critical_temperature = None
        self.crit_alarm = None
        self.actual_temp = None
        self.input_rute = None
        self.temperatures = []

        self.flag_core_temp = False
        self.flag_core_deltatemp = False
        self.counter_fct = 0
        self.counter_fcdt = 0
        self.deltaT_max = 5
        self.dtime_bypass = 20
        self.ddtime_bypass = 10

    def set_critical_temperature(self,critical):
        self.critical_temperature = critical

    def set_crit_alarm(self,c_a):
        self.crit_alarm = c_a

    def set_max_temp(self,max_t):
        self.max_temp = max_t

    def set_label(self,lb):
        self.label = lb

    def get_core_number(self):
        return self.core_number

    def set_core_number(self,n):
        self.core_number = int(n)

    def print_info(self):
        print "\t\t" + str(self.core_number) + ") Label = " + str(self.label) + " / Max = " + str(self.max_temp) + " / Critical = " + str(self.critical_temperature) + " / Critical alarm = " + str(self.crit_alarm) + "\n\tInput rute = " + self.input_rute

    def calculate_delta_T(self):
        self.temperatures.append(self.actual_temp)

        if len(self.temperatures) >= 4:
            self.temperatures.pop(0)

            deltaT = (abs(self.temperatures[0] - self.temperatures[2]))/2

            return deltaT

class ISA_adapter:
    def __init__(self, number):
        self.adapter_number = int(number)
        self.hwmon_list = []

    def get_adapter_number(self):
        return self.adapter_number

    def print_info(self):
        print "ISA adapter: " + str(self.adapter_number) + "\n\tCores list:\n\n"
        for monitor in self.hwmon_list:
            monitor.print_info()

    def generate_cores_input_rutes(self):
        rute = "/sys/devices/platform/coretemp." + str(self.adapter_number)
        for hwmon in self.hwmon_list:
            hwmon.partial_rute = rute
            hwmon.generate_cores_input_rutes()

class HardwareMonitor:
    def __init__(self,number):
        self.hwmon_number = number
        self.cores = []
        self.partial_rute = None

    def get_hwmon_number(self):
        return self.hwmon_number

    def print_info(self):
        print "\tHardware monitor: " + str(self.hwmon_number) + "\n\tCores list:\n\n"
        for core in self.cores:
            core.print_info()

    def generate_cores_input_rutes(self):
        rute =  self.partial_rute + "/hwmon/hwmon" + str(self.hwmon_number) + "/"

        for core in self.cores:
            core.input_rute = rute + "temp" + str(core.core_number) + "_input"


def search_ISA_adapter(list_k,number):
    if number.isdigit():
        if len(list_k) > 0:
            for i in list_k:
                if i.get_adapter_number() == int(number):
                    return i

        new_adapter = ISA_adapter(number)
        list_k.append(new_adapter)

        print new_adapter

        return new_adapter
    else:
        return None

def search_hwmon(list_k,number):
    if number.isdigit():
        if len(list_k) > 0:
            for i in list_k:
                if i.get_hwmon_number() == int(number):
                    return i

        new_hwmon = HardwareMonitor(int(number))
        list_k.append(new_hwmon)

        print new_hwmon
        return new_hwmon
    else:
        return None

def search_core(list_k,core_n):
    if core_n.isdigit():
        if len(list_k) > 0:
            for i in list_k:
                if i.get_core_number() == int(core_n):
                    return i

        new_core = Core()
        new_core.set_core_number(core_n)
        list_k.append(new_core)

        print new_core

        return new_core
    else:
        return None

def detect_Adapters(dtime=None,ddtime=None,high=None,crit=None,crit_a=None):

    os.system("grep \"\" /sys/devices/platform/coretemp.?/hwmon/hwmon?/temp?_label > info-chips.txt ")
    os.system("grep \"\" /sys/devices/platform/coretemp.?/hwmon/hwmon?/temp?_crit_alarm >> info-chips.txt ")
    os.system("grep \"\" /sys/devices/platform/coretemp.?/hwmon/hwmon?/temp?_max >> info-chips.txt")
    os.system("grep \"\" /sys/devices/platform/coretemp.?/hwmon/hwmon?/temp?_crit >> info-chips.txt")

    adapters_list = list()

    print '\n\n\n\n'

    info_file = open("info-chips.txt")

    for info_line in info_file:
        num_isa_adapter = (info_line.split("coretemp.")[1]).split("/")[0]

        adapter = search_ISA_adapter(adapters_list,num_isa_adapter)
        if adapter != None:
            subtokens1 = info_line.split("temp")
            subtokens2 = subtokens1[2].split(":")
            subtokens3 = subtokens2[0].split("_")

            hw_monitor = search_hwmon(adapter.hwmon_list,(info_line.split("hwmon")[2])[0])

            core = search_core(hw_monitor.cores, subtokens3[0])

            if subtokens3[1] == "label":
                core.label = (subtokens2[1].split('\n'))[0]

            elif subtokens3[1] == "crit" and len(subtokens3) < 3:
                core.critical_temperature = float(subtokens2[1]) / 1000

            elif subtokens3[1] == "crit" and not len(subtokens3) < 3:
                core.crit_alarm = float(subtokens2[1]) / 1000

            elif subtokens3[1] == "max":
                core.max_temp = float(subtokens2[1]) / 1000

            if high != None:
                core.max_temp = high
            if crit != None:
                core.critical_temperature = int(crit)
            if crit_a != None:
                core.crit_alarm = int(crit_a)
            if dtime != None:
                core.dtime_bypass = dtime
            if ddtime != None:
                core.ddtime_bypass = ddtime
        else:
            print "Input data formatting error. Invalid ISA-adapter number!"

    print "\n\n"

    info_file.close()

    return adapters_list

version = '0.1'

parser = argparse.ArgumentParser(prog='CPUTemperatureAlerts script', usage='%(prog)s [options]',description='Linux python script for display both GNOME dialogs and system alerts to notice critical temperatures of CPU cores.')
parser.add_argument('-t','--dtime',dest='dtime',type=int,help='Time (segs)(int) between a dialog and another when the core is over HIGH temperature.')
parser.add_argument('-d','--ddtime',dest='ddtime',type=int,help='Changes time between a dialog and another when temperature of a core rockets.')
parser.add_argument('-k','--hight',dest='high',type=float,help='Changes MAX_TEMP value, therefore, changes bottom limit of detection of temperatures')
parser.add_argument('-c','--critical',dest='crit',type=float,help='Changes CRITICAL_TEMPERATURE value for each core in coretemps system folder')
parser.add_argument('-a','--critical-alarm',dest='crit_a',type=float,help='Set the CRITICAL_ALARM value for each core.')
parser.add_argument('--version',action='version',version='%(prog)s ' + version)
args = parser.parse_args()

print args

adapters_list = detect_Adapters(args.dtime, args.ddtime, args.high, args.crit,args.crit_a)

for i in adapters_list:
    i.generate_cores_input_rutes()
    i.print_info()


while True:
    for adapter in adapters_list:
        for hwmon in adapter.hwmon_list:
            for core in hwmon.cores:
                os.system("grep \"\" "+core.input_rute + " > actual_temperature_core.txt")
                f = open("actual_temperature_core.txt")
                core.actual_temp = float(f.readline()) / 1000
                f.close()

                outputstring_title = None

                if core.actual_temp >= core.max_temp and core.flag_core_temp is not True:
                    os.system("notify-send 'Alerta, temperatura alta' 'Adapter = "+str(adapter.adapter_number)+"\nCore ="+core.label+"\nTemperature = "+str(core.actual_temp)+" degrees'")
                    core.flag_core_temp = True

                if core.calculate_delta_T() >= core.deltaT_max and core.flag_core_deltatemp is not True:
                    os.system("notify-send 'Warning!, temperature of porcessor increasing at high rate!' 'Adapter = "+str(adapter.adapter_number)+"\nCore ="+core.label+"\nTemperature = "+str(core.actual_temp)+" degrees'")
                    core.flag_core_deltatemp = True



                if core.flag_core_temp:
                    core.counter_fct += 1
                    if core.counter_fct >= core.dtime_bypass:
                        core.flag_core_temp = False
                        core.counter_fct = 0

                if core.flag_core_deltatemp:
                    core.counter_fcdt += 1
                    if core.counter_fcdt >= core.ddtime_bypass:
                        core.flag_core_deltatemp = False
                        core.counter_fcdt = 0

                #print core.actual_temp
    time.sleep(1)
