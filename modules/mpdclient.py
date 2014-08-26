from ._module import _module

import threading
import mpd
import logging
import time

class mpd_thread(threading.Thread):
    def __init__(self, module):
        return
        super(mpd_thread, self).__init__()
        self._stop_event = threading.Event()
        self.module = module
        
    def stop(self):
        logging.debug('Stopping mpd_thread thread')
        self._stop_event.set()
        
    def run(self):
        logging.debug('Begin of run() in mpd_thread')
        c = mpd.MPDClient()
        c.idletimeout = 5
        connected = False
        song_id = None
        while not self._stop_event.is_set():
            if not connected:
                try:
                    c.connect('barstation', 6600)
                    connected = True
                    song_id = c.currentsong()['id']
                except:
                    pass
            else:
                try:
                    result = c.idle('player')
                    if 'player' in result:
                        song = c.currentsong()
                        if song['id'] != song_id:
                            song_id = song['id']
                            now_playing = 'Now playing: {artist} - {title}'.format(**song)
                            self.notice('#tkkrlab', now_playing)
                except:
                    logging.exception()
                    connected = False
#            time.sleep(5)
        logging.debug('End of run() in mpd_thread')

class mpdclient(_module):
    def __init__(self, mgr):
        _module.__init__(self, mgr)
        #try:
        #    self.thread = mpd_thread(self)
        #    self.thread.start()
        #except Exception as e:
        #    logging.warning('Thread exception: {0}'.format(e))

    def stop(self):
        pass
        #self.thread.stop()
        #self.thread.join()
    
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
