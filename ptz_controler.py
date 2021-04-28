import requests
from requests.auth import HTTPDigestAuth
import datetime
import time


class PTZ_Camera_Controller:
    def __init__(self, ip, account, password):
        self.ip = ip
        self.account = account
        self.password = password
        data = self.get_param(['minpan', 'maxpan', 'mintilt', 'maxtilt'])
        self.log(data)
        self.minpan = data['minpan']
        self.maxpan = data['maxpan']
        self.mintilt = data['mintilt']
        self.maxtilt = data['maxtilt']
        self.current_x = None
        self.current_y = None
        self.current_position()
        # Need to check whether the ip/ount/password are correct.

    # To move the zoom module by vector, the bigger/smaller vx, vy is the faster it moves.
    def vector_move(self, vx, vy, zooming=None, zs=None):
        if int(vx) > 150:
            vx = 150
        if vy > 150:
            vy = 150
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?stream=3&channel=0&vx={}&vy={}&vs=10'.format(self.ip, vx, vy)
        if zooming is not None:
            zooming = zooming.lower().strip()
        if zooming not in ('tele', 'wide'):
            zooming = None
        if zooming is not None or zs is not None:
            url += '&zooming={}&zs={}'.format(zooming, zs)
        self.log(url)
        # Need to handle network exceptions.
        r = self.http_get(url)
        self.current_position()
        return r

    # Simply move the module to that position.
    def position_move(self, px, py, pen_speed=100, tilt_speed=100):
        if px not in range(self.minpan - 1, self.maxpan + 1):
            self.log('The target tilt position({}) is out of range {}~{}.'.format(px, self.minpan, self.maxpan))
            return
        if py not in range(self.mintilt - 1, self.maxtilt + 1):
            self.log('The target tilt position({}) is out of range {}~{}.'.format(py, self.mintilt, self.maxtilt))
            return
        # This URL might need to be reviewed to fit your demand.
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?setpan={}&settilt={}&speedx={}&speedy={}'\
            .format(self.ip, px, py, pen_speed, tilt_speed)
        url = url + '&setptmode=nonblock'
        self.log(url)
        r = self.http_get(url)
        time.sleep(0.1)
        self.current_position()
        # Wait until the camera turn to destination.
        # while px != self.current_x or py != self.current_y:
        #     self.current_position()
        #     time.sleep(0.1)
        return r

    # Get the current parameter from camera.
    # Input: para: the parameter need to get from camera, no need the "get" in the front. The function will add.
    # Output: The dictionary with the paramater as the index and value we got from camera.
    def get_param(self, para):
        para = ['get' + x for x in para]
        para = "&".join(para)
        # Digest Authentication
        url = 'http://{}/cgi-bin/camctrl/camctrl.cgi?'.format(self.ip) + para
        r = self.http_get(url)
        text = r.text.rstrip().split('&')
        self.log(url + ' ' + ';'.join(text))
        result = {}
        for item in text:
            [name, value] = item.split('=')
            result[name] = int(value)
        return result

    # Get to know current zoom module position so that we know when to stop the turn.
    def current_position(self):
        para = ['pan', 'tilt']
        data = self.get_param(para)
        self.current_x = data['pan']
        self.current_y = data['tilt']
        return data

    def log(self, info):
        print(datetime.datetime.now(), info)

    def http_get(self, url):
        return requests.get(url, auth=HTTPDigestAuth(self.account, self.password))
        # Simple Authentication
        # url = 'http://{}:{}@{}/cgi-bin/camctrl/camctrl.cgi?'.format(self.account, self.password, self.ip) + para
        # r = requests.get(url)

    def http_other(self, method, url, data=None):
        if method == 'delete':
            return requests.delete(url, auth=HTTPDigestAuth(self.account, self.password))
        elif method == 'put':
            return requests.put(url, auth=HTTPDigestAuth(self.account, self.password))
        elif method == 'post':
            return requests.post(url, auth=HTTPDigestAuth(self.account, self.password), data=data)
        else:
            info = 'In http request unknown method {} was given.'.format(method)
            self.log(info)


if __name__ == '__main__':
    ip = '192.168.40.138'
    account = 'root'
    password = 'tssc1234'
    sd = PTZ_Camera_Controller(ip, account, password)
