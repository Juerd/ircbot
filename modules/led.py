from ._module import _module
import urllib
import http
import logging
from datetime import datetime

class led(_module):
    def cmd_led( self, args, source, target, admin ):
        """!led <message>: put message on led matrix board"""
        if source.lower() == 'aaps' or source.lower().startswith('michielbrink'):
            pass
        return [ 'Led: {0}'.format( self.__send_led( '<' + source + '> ' + ' '.join( args ) ) ) ]

    def cmd_time( self, args, source, target, admin ):
        """!time: put current time on led matrix board"""
        self.__send_led('{:%H:%M}'.format(datetime.now()).center(16))

    def send_led(self, message):
        self.__send_led(message)
    def __send_led( self, message):
        """Send a command to the led board"""
        try:
            url = urllib.parse.urlsplit( self.get_config( 'url' ).format( urllib.parse.quote( message[:85] ) ) )
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

