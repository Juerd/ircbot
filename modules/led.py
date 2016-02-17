from modules import Module
import urllib
import http
import logging
from datetime import datetime

class led(Module):
    def cmd_led( self, args, source, target, admin ):
        """!led <message>: put message on led matrix board"""
        if source.lower() == 'aaps' or source.lower().startswith('michielbrink'):
            pass
        return [ 'Led: {0}'.format( self.send_led( '<' + source + '> ' + ' '.join( args ) ) ) ]

    def cmd_time( self, args, source, target, admin ):
        """!time: put current time on led matrix board"""
        self.send_led('{:%H:%M}'.format(datetime.now()).center(16))

    def send_led(self, message):
        return self.__send_led(action='text', text=message[:85])
    def send_welcome(self, name):
        return self.__send_led(action='welcome', name=name)
    def __send_led(self, **parameters):
        """Send a command to the led board"""
        try:
            url = urllib.parse.urlsplit(self.get_config('url') + '?' + urllib.parse.urlencode(parameters))
            logging.debug( 'Sending request to LED board at {0}'.format( url.geturl() ) )
            conn = http.client.HTTPConnection( url.netloc, timeout=10 )
            conn.request( 'GET', url.path + '?' + url.query )
            response = conn.getresponse()
            res = response.status
            reply = response.read()
            conn.close()
            logging.debug( 'LED board reply: {0}'.format( str( reply ) ) )
            if res != 200:
                return 'Error:' + res + ' - ' + response.reason
            else:
                return 'OK'
        except IOError as e:
            return 'Cannot connect to LED server: "{0}"'.format( e )
        except:
            logging.exception()
            return 'Error: LED URL not set'

