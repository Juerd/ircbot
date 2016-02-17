from modules import Module

from datetime import datetime
from dateutil.tz import tzlocal
import dateutil.parser
import re
import threading, socket, select
import logging
#website updating
import urllib.request
import twitter

class StatusMonitor(threading.Thread):
    def __init__(self, module):
        super().__init__()
        self._stop_event = threading.Event()
        self.module = module
        
    def stop(self):
        logging.debug( 'Stopping StatusMonitor thread' )
        self._stop_event.set()
        
    def run(self):
        try:
            port = int(self.module.get_config('status_listen_port'))
        except:
            port = 8889
        logging.debug('Begin of run() in StatusMonitor, port: {}'.format(port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # bind even if the socket is not cleanly closed
        self.socket.bind(('', port))
        while not self._stop_event.is_set():
            r, _, _ = select.select([self.socket],[],[], 0.5)
            if len(r) > 0:
                data = r[0].recv(1)
                try:
                    data = data.decode('ascii')
                except:
                    continue
                if data in ('0', '1'):
                    try:
                        self.module.set_space_status(data, datetime.now().replace(tzinfo=tzlocal()), 'Lock-O-Matic')
                    except Exception as e:
                        logging.warning('Failed to update status: {0}'.format(e))
                else:
                    logging.warning('Unknown data: {}'.format(data))
        self.socket.close()
        logging.debug('End of run() in StatusMonitor')

class tkkrlab(Module):
    CFG_KEY_STATE = 'space_state'
    CFG_KEY_STATE_TIME = 'space_state_time'
    CFG_KEY_STATE_NICK = 'space.state.nick'
    CFG_KEY_TEXT_OPEN = 'text.space_open'
    CFG_KEY_TEXT_CLOSED = 'text.space_closed'
    CFG_KEY_TOPIC = 'topic'

    DEFAULT_TEXT_OPEN = 'We zijn open'
    DEFAULT_TEXT_CLOSED = 'We zijn dicht'
    DEFAULT_TOPIC = 'See our activities on http://bit.ly/AsJMNc'

    """Bot module to do tkkrlab things"""
    def start(self):
        status_history = self.get_config('space_state_history', False)
        if status_history:
            self.space_status_history = [f.split(':') for f in status_history.split(',')]
        
        cfg_state = None
        cfg_time = None
        cfg_who = None
        try:
            cfg_state = self.get_config(self.CFG_KEY_STATE) == '1'
        except:
            pass
        try:
            cfg_time = dateutil.parser.parse(self.get_config(self.CFG_KEY_STATE_TIME), tzinfos={'CET': 3600, 'CEST': 7200})
        except:
            pass
        try:
            cfg_who = self.get_config(self.CFG_KEY_STATE_NICK)
        except:
            pass
        
        self.space_status = (cfg_state, cfg_time, cfg_who)

        try:
            self.thread = StatusMonitor(self)
            self.thread.start()
        except Exception as e:
            logging.warning('Thread exception: {0}'.format(e))
    
    def stop(self):
        self.thread.stop()
        self.thread.join()

    def on_notice(self, source, target, message):
        if source.nick.lower() in ('jawsper', 'lock-o-matic'):
            result = re.search('^(.+) entered the space', message)
            if result:
                nick = result.group(1)
                self.__led_welcome(nick)
            elif 'TkkrLab' in message:
                result = re.search(':\s+(?P<status>[a-z]+)\s*@\s*(?P<datetime>.*)$', message)
                if result:
                    status_bool = result.group('status') == 'open'
                    status_time = dateutil.parser.parse(result.group('datetime'), dayfirst=True).replace(tzinfo=tzlocal())
                    space_open = self.__get_space_open()
                    space_time = self.__get_space_open_time()
                    if space_open != status_bool or not space_time or abs((space_time - status_time).total_seconds()) > 100:
                        logging.info( 'Space status too different from Lock-O-Matic status, updating own status' )
                        self.set_space_status('1' if status_bool else '0', status_time, 'Lock-O-Matic')

    def admin_cmd_led_welcome(self, raw_args, admin, **kwargs):
        if not admin: return
        if len(raw_args) == 0: return
        self.__led_welcome(raw_args)

    def __led_welcome( self, user ):
        try:
            self.get_module('led').send_welcome(user)
        except:
            pass

    def admin_cmd_force_status(self, raw_args, admin, **kwargs):
        """!force_status <0|1>: force space status to closed/open"""
        if not admin: return
        if len(raw_args) == 0: return
        logging.debug('force_status: {}'.format(raw_args))
        if raw_args[0] in ('0', '1'):
            self.set_space_status(raw_args[0], datetime.now().replace(tzinfo=tzlocal()), source)
    
    def admin_cmd_force_topic_update(self, admin, **kwargs):
        """!force_topic_update: force topic update"""
        if not admin: return
        self.__set_default_topic()
        
    def cmd_status(self, **kwargs):
        """!status: to get open/close status of the space"""
        space_open = self.__get_space_open()
        space_time = self.__get_space_open_time()
        space_nick = self.__get_space_open_nick()
        if space_open not in (True, False):
            return ['Error: status is not True/False but {0}'.format(space_open)]
        else:
            open_text = 'Open' if space_open == True else 'Closed'
            time = space_time.strftime('%a, %d %b %Y %H:%M:%S %Z') if space_time else '<unknown>'
            if space_nick:
                return ['We are {0} since {1} by {2}'.format(open_text, time, space_nick)]
            else:
                return ['We are {0} since {1}'.format(open_text, time)]

    def set_space_status(self, status, aTime, who=None):
        space_open = self.__get_space_open()
        if space_open == None:
            space_open = status == '1'
        logging.debug('set_space_status [space_open: {}, status: {}]'.format(space_open, status))
        change = False
        if space_open != (status == '1'):
            space_open = status == '1'
            change = True
        self.space_status = (space_open, aTime, who)
        self.set_config(self.CFG_KEY_STATE, space_open)
        self.set_config(self.CFG_KEY_STATE_TIME, aTime.strftime('%Y-%m-%dT%H:%M:%S %Z'))
        self.set_config(self.CFG_KEY_STATE_NICK, who)

        if change:
            self.__on_state_change(space_open)

        return self.space_status

    def __get_space_open(self):
        return self.space_status[0] if self.space_status and len(self.space_status) > 0 else None

    def __get_space_open_time(self):
        return self.space_status[1] if self.space_status and len(self.space_status) > 1 else None

    def __get_space_open_nick(self):
        return self.space_status[2] if self.space_status and len(self.space_status) > 2 else None

    def __on_state_change(self, state):
        self.__set_default_topic()
        self.__update_website_state(state)
        self.__update_twitter(state)

    def __set_default_topic(self):
        space_open = self.__get_space_open()
        key = self.CFG_KEY_TEXT_OPEN if space_open else self.CFG_KEY_TEXT_CLOSED
        default = self.DEFAULT_TEXT_OPEN if space_open else self.DEFAULT_TEXT_CLOSED
        topic = self.get_config(key, default)
        self.__set_topic('#tkkrlab', topic)

    def __set_topic(self, channel, new_topic):
        channel_topic = new_topic
        cfg_topic = self.get_config(self.CFG_KEY_TOPIC, self.DEFAULT_TOPIC)
        if cfg_topic:
            channel_topic += ' | ' + cfg_topic
        self.mgr.bot.connection.topic(channel, channel_topic)
        self.privmsg(channel, new_topic)

    def __update_website_state(self, state):
        url = self.get_config('website_url').format('open' if state else 'closed')
        with urllib.request.urlopen(url) as req:
            logging.debug('Website space update: ' + req.read().decode('ascii'))

    def __update_twitter(self, state):
        now = datetime.now()
        timestamp = now.strftime("%d-%m-%Y %H:%M")
        message = 'We are {} {} Quote: {}'.format('open' if state else 'closed', timestamp, self.get_module('quote').random_quote())
        self.__send_tweet(message)

    def __send_tweet(self, text):
        params = {}
        for name in ('consumer_key', 'consumer_secret', 'token', 'token_secret'):
            params[name] = self.get_config('twitter.' + name)
        twit = twitter.Twitter(auth=twitter.OAuth(**params))
        twit.statuses.update(status=text[:140])
