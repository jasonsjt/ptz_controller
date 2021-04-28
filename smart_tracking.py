import ptz_controler as ptz
import time


class SmartPTZ(ptz.PTZ_Camera_Controller):
    def __init__(self, ip, account, password):
        super().__init__(ip, account, password)
        self.preset_names = []

    # Move the camera to home position.
    def move_to_home(self):
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?move=home'.format(self.ip)
        r = self.http_get(url)

    # Move the camera to preset point.
    # input:
    # preset_name   string, name of the preset point.
    # Output:
    # None
    def move_to_preset(self, preset_name):
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?recall={}'.format(self.ip, preset_name)
        r = self.http_get(url)

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
        self.log(url)
        r = self.http_get(url)
        pre_set_count = int(r.text.split('=')[1])
        # Clear the old variable so we don't duplicate the info.
        self.preset_names = []
        for i in range(pre_set_count):
            url = 'http://{}/cgi-bin/admin/getparam.cgi?camctrl_c0_preset_i{}_name'.format(self.ip, i)
            self.log(url)
            r = self.http_get(url)
            r.encoding = r.apparent_encoding
            name = r.text.split('=')[1].split('\r')[0].replace("'", "")
            self.preset_names.append(name)
        self.log(self.preset_names)

    def track_from_here(self, preset_index):
        # Move to pre-set point.
        self.move_to_preset_index(preset_index)
        # Delete current smart tracking rule.
        url = 'http://{}/VCA/Config/RE/SmartTrackingDetection'.format(self.ip)
        info = 'Delete current smart tracking rule. delete, {}'.format(url)
        self.log(info)
        r = self.http_other('delete', url)
        # Set current position as home in VCA.
        url = 'http://{}/VCA/PTZ/HomeView'.format(self.ip)
        info = 'Set current position as home in VCA. put, {}'.format(url)
        self.log(info)
        r = self.http_other('put', url)
        # Set detection rule.
        url = 'http://{}/VCA/Config/RE/SmartTrackingDetection'.format(self.ip)
        data = '{"Full Screen":{"EventName":"Full Screen","Field":[],"RuleName":"Full Screen","Type":"full"}}'
        info = 'Set detection rule. post, {}, {}'.format(url, data)
        self.log(info)
        r = self.http_other('post', url, data=data)
        # Start smart tracking.
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?auto=objtrack'.format(self.ip)
        info = 'Start smart tracking. get, {}'.format(url)
        self.log(info)
        r = self.http_get(url)
        # Reload VCA configure
        url = 'http://{}/VCA/Config/Reload'.format(self.ip)
        info = 'Reload VCA configure. get, {}'.format(url)
        self.log(info)
        r = self.http_get(url)


if __name__ == '__main__':
    ip = '172.19.14.10'
    account = 'root'
    password = 'tracking1234'
    sd = SmartPTZ(ip, account, password)
    sd.move_to_home()
    for i in range(4):
        sd.track_from_here(i)
        time.sleep(30)


