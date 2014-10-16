from ._module import _module

import threading
import mpd
import logging
import time

class mpdclient(_module):
    def __init__(self, mgr):
        _module.__init__(self, mgr)
    
    def get_currentsong(self):
        try:
            host, port = self.get_config('host'), self.get_config('port')
        except:
            return ['Error: host/port not set']
        try:
            port = int(port)
        except ValueError:
            return ['Error: port not int']
        if not host or not port:
            return ['Error: host/port not set']
        c = mpd.MPDClient()
        c.timeout = 5
        c.connect(host, port)
        return c.currentsong()
    def parse_currentsong(self, song):
        if 'artist' in song and 'title' in song:
            return '{artist} - {title}'.format(**song)
        elif 'title' in song:
            return song['title']
        elif 'file' in song:
            return song['file']
        else:
            return 'nothing at all'
    
    def cmd_np(self, args, source, target, admin):
        try:
            song = self.get_currentsong()
            np = self.parse_currentsong(song)
            try:
                self.get_module('led').send_led(np)
            except Exception as e:
                return ['Error: {}'.format(e)]
            return ['Now playing: ' + np]
        except Exception as e:
            return ['Error: {}'.format(e)]
 
    def cmd_npd(self, args, source, target, admin):
        try:
            song = self.get_currentsong()
            return [str(song)]
        except Exception as e:
            return ['Error: {}'.format(e)]
