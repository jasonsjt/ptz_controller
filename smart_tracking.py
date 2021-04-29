# VIVOTEK Jason Tsung jason.tsung@vivotek.com V2
# 2021/4/29 Add new function of stop the tracking and move the camera back to home position.
# 2021/4/29 Add new function the camera will keep tracking people until the people is gone.

import ptz_controler as ptz
import time
import json


class SmartPTZ(ptz.PTZ_Camera_Controller):
    def __init__(self, ip, account, password):
        super().__init__(ip, account, password)
        self.preset_names = []

    # Move the camera to home position.
    def move_to_home(self):
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?move=home'.format(self.ip)
        r = self.http_get(url)
        info = 'Move to home position,http_get, {}'.format(url)
        self.log(info)

    # Move the camera to preset point.
    # input:
    # preset_name   string, name of the preset point.
    # Output:
    # None
    def move_to_preset(self, preset_name):
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?recall={}'.format(self.ip, preset_name)
        r = self.http_get(url)
        info = 'Move to preset points by name,http_get, {}, {}'.format(preset_name, url)
        self.log(info)

    # Move the camera to the preset index.
    # Input:
    # preset_index   integer, the preset point index, a camera might have more then 1000 preset points.
    # Output:
    # None
    def move_to_preset_index(self, preset_index):
        # Check if illegal index was given, if there is no preset point recorded in program then search it.
        if len(self.preset_names) == 0 or len(self.preset_names) < preset_index:
            self.get_preset_names()
        # If we checked again but still can't find the index user want, then issue error message.
        if len(self.preset_names) < preset_index:
            info = 'Requesting to move to {}th preset point, ' \
                   'but currently only {} preset points found'.format(preset_index, len(self.preset_names))
            self.log(info)
        # If there is the preset point then turn the camera to the preset point using it's name.
        # Please be noticed the camera only recognize the preset point by it's name, not the index.
        pre_set_name = self.preset_names[preset_index]
        self.move_to_preset(pre_set_name)

    # Find all names of preset points in the camera.
    # Input: None
    # Output: Name list stored in object variable.
    def get_preset_names(self):
        # Get how many preset points has been set.
        # Actually this function to feedback the next possible preset slot.
        # We can use it as an indication of how many preset points so far.
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?cam=getsetpreset'.format(self.ip)
        info = 'Get how many preset points set, http_get, {}'.format(url)
        self.log(info)
        r = self.http_get(url)
        pre_set_count = int(r.text.split('=')[1])
        # Clear the old variable so we don't duplicate the info.
        self.preset_names = []
        for i in range(pre_set_count):
            r = self.http_get(url)
            r.encoding = r.apparent_encoding
            name = r.text.split('=')[1].split('\r')[0].replace("'", "")
            self.preset_names.append(name)
            url = 'http://{}/cgi-bin/admin/getparam.cgi?camctrl_c0_preset_i{}_name'.format(self.ip, i)
            info = 'Get the name, {}, of preset points. http_get, {}'.format(name, url)
            self.log(info)
        self.log('The list of preset names {}'.format(self.preset_names))
        return self.preset_names

    # Function track_from_here
    # Order the camera to start the smart tracking at assigned preset point or home position.
    # Input:
    # preset_index  The index in int of the preset point,
    #               the program will need to get the name of each point.
    # home          Boolean, if the camera need to turn to the home position.
    #               (in camera firmware, not the VCA defined home position.)
    #               If home=True, then the preset_index won't be effective.
    # check_per_sec Integer, default 0 means turn off this function.
    #               If user indicate a positive integer then the program will check the status of the program.
    #               If the camera is not tracking the people, then return.
    def track_from_here(self, preset_index, home=False, check_per_sec=0):
        if home:
            # Move to home position.
            self.move_to_home()
        else:
            # Move to pre-set point.
            self.move_to_preset_index(preset_index)

        # Delete current smart tracking rule.
        url = 'http://{}/VCA/Config/RE/SmartTrackingDetection'.format(self.ip)
        info = 'Delete current smart tracking rule. http_delete, {}'.format(url)
        self.log(info)
        r = self.http_other('delete', url)
        # Set current position as home in VCA.
        url = 'http://{}/VCA/PTZ/HomeView'.format(self.ip)
        info = 'Set current position as home in VCA. http_put, {}'.format(url)
        self.log(info)
        r = self.http_other('put', url)
        # Set detection rule.
        url = 'http://{}/VCA/Config/RE/SmartTrackingDetection'.format(self.ip)
        data = '{"Full Screen":{"EventName":"Full Screen","Field":[],"RuleName":"Full Screen","Type":"full"}}'
        info = 'Set detection rule. http_post, {}, {}'.format(url, data)
        self.log(info)
        r = self.http_other('post', url, data=data)
        # Start smart tracking.
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?auto=objtrack'.format(self.ip)
        info = 'Start smart tracking. http_get, {}'.format(url)
        self.log(info)
        r = self.http_get(url)
        # Reload VCA configure
        url = 'http://{}/VCA/Config/Reload'.format(self.ip)
        info = 'Reload VCA configure. http_get, {}'.format(url)
        self.log(info)
        r = self.http_get(url)
        if check_per_sec <= 0:
            return
        # First allow some time for smart tracking to initiate.
        time.sleep(3)
        while True:
            if self.is_camera_tracking():
                time.sleep(check_per_sec)
            else:
                return

    def stop_smart_tracking(self):
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?auto=stop'.format(self.ip)
        info = 'Stop tracking . http_get, {}'.format(url)
        self.log(info)
        r = self.http_get(url)

    # Turn the camera toward home position and stop the tracking.
    def move_to_home_and_stop_tracking(self):
        self.move_to_home()
        self.stop_smart_tracking()

    # Turn the camera toward home position and start the tracking.
    def move_to_home_and_tracking(self, check_per_sec=0):
        self.track_from_here(0, home=True, check_per_sec=check_per_sec)

    # Check current smart tracking status.
    # Output:
    #   Waiting     The camera VCA is on but there is no one there.
    #   Tracking    The camera is now tracking people.
    #   Missing     The people used to be tracked was gone, camera is returning to VCA home position.
    #   Sleep       The smart tracking function is off.
    def check_tracking_status(self):
        url = 'http://{}/VCA/Camera/Status'.format(self.ip)
        r = self.http_get(url)
        info = 'Checking camera tracking status. http_get, {}, result {}'.format(url, r.text)
        self.log(info)
        status = json.loads(r.text)['PTZInfo']['Status']
        self.log('Current tracking status is {}'.format(status))
        return status

    def is_camera_tracking(self):
        if self.check_tracking_status() == 'Tracking':
            self.log('The camera is now tracking someone.')
            return True
        else:
            self.log('The camera is not tracking anyone.')
            return False


if __name__ == '__main__':
    ip = '172.19.14.10'
    account = 'root'
    password = 'tracking1234'
    sd = SmartPTZ(ip, account, password)
    name_list = sd.get_preset_names()
    for u in range(100):
        sd.move_to_home_and_tracking(check_per_sec=3)
        for i in range(len(name_list)):
            sd.track_from_here(i, check_per_sec=3)
    sd.move_to_home_and_stop_tracking()
