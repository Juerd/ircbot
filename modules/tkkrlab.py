from _module import _module

import httplib, urllib, urlparse

import datetime
from dateutil.tz import tzlocal
import dateutil.parser
import time

import random
import os.path

import threading, socket, select

class StatusMonitor( threading.Thread ):
	def __init__( self, module ):
		super( StatusMonitor, self ).__init__()
		self._stop = threading.Event()
		self.module = module
		
	def stop( self ):
		self._stop.set()
		
	def run( self ):
		self.socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
		self.socket.bind( ( '', 8889 ) )
		while not self._stop.isSet():
			( r, w ,x ) = select.select( [self.socket],[],[], 0.5 )
			if len( r ) > 0:
				data = r[0].recv(1)
				if data in ( '0','1' ):
					try:
						self.module.set_space_status( data, time.time() )
					except Exception as e:
						print( 'Failed to update status: {0}'.format( e ) )
		self.socket.close()	

class tkkrlab( _module ):
	"""Bot module to do tkkrlab things"""
	def __init__( self, mgr ):
		_module.__init__( self, mgr )
			
		cfg_state = None
		cfg_time = None
		try:
			cfg_state = self.get_config( 'space_state' ) == '1'
		except:
			pass
		try:
			cfg_time = float( self.get_config( 'space_state_time' ) )
		except:
			pass
		
		self.space_status = ( cfg_state, cfg_time )
		try:
			self.thread = StatusMonitor( self )
			self.thread.start()
		except Exception as e:
			print( 'Thread exception: {0}'.format( e ) )
	
	def stop(self):
		self.thread.stop()
		self.thread.join()
	
	def admin_cmd_force_status( self, args, source, target, admin ):
		"""!force_status <0|1>: force space status to closed/open"""
		if not admin: return
		if len( args ) == 0: return
		if args[0] in ( '0', '1' ):
			self.set_space_status( args[0], time.time() )
	
	def admin_cmd_force_topic_update( self, args, source, target, admin ):
		"""!force_topic_update: force topic update"""
		if not admin: return
		( space_open, space_time ) = self.__get_space_status()
		self.__set_topic( '#tkkrlab', 'We zijn Open' if space_open else 'We zijn Dicht' )
		
	def cmd_quote( self, args, source, target, admin ):
		"""!quote: to get a random quote"""
		return [ 'Quote: ' + self.__random_quote() ]
		
	def cmd_status( self, args, source, target, admin ):
		"""!status: to get open/close status of the space"""
		( space_open, space_time ) = self.__get_space_status()
		if space_open not in ( True, False ):
			return [ 'Error: status is not True/False but {0}'.format( space_open ) ]
		else:
			return [ 'We are {0} since {1}'.format( 'Open' if space_open == True else 'Closed', datetime.datetime.fromtimestamp( space_time, tzlocal() ).strftime( '%a, %d %b %Y %H:%M:%S %Z' ) ) ]
	
	def cmd_led( self, args, source, target, admin ):
		"""!led <message>: put message on led matrix board"""
		( space_open, space_time ) = self.__get_space_status()
		if space_open == True:
			return [ 'Led: {0}'.format( self.__send_led( ' '.join( args ) ) ) ]
		elif space_open == False:
			return [ 'Sorry ' + source + ', can only do this when space is open.' ]
		else:
			return [ 'Error: status is not True/False but {0}'.format( space_open ) ]
		
	def cmd_time( self, args, source, target, admin ):
		"""!time: put current time on led matrix board"""
		( space_open, space_time ) = self.__get_space_status()
		if space_open == True:
			self.__send_led( time.strftime( '%H:%M' ).center( 16 ) )

	def set_space_status( self, status, aTime ):
		( space_open, space_time ) = self.space_status
		if space_open == None:
			space_open = status == '1'
		if space_open != ( status == '1' ):
			space_open = status == '1'
			self.__set_topic( '#tkkrlab', 'We zijn Open' if space_open else 'We zijn Dicht' )
		self.space_status = ( space_open, aTime )
		self.set_config( 'space_state', space_open )
		self.set_config( 'space_state_time', aTime )
		return self.space_status
		
	def __get_space_status( self ):
		return self.space_status

	def __set_topic( self, channel, new_topic ):
		self.mgr.bot.connection.topic( channel, new_topic + ' | ' + self.get_config( 'topic', 'See our activities on http://bit.ly/AsJMNc' ) )
		self.privmsg( channel, new_topic )

	def __send_led( self, message):
		"""Send a command to the led board"""
		try:
			url = urlparse.urlparse( self.get_config( 'led_url' ).format( urllib.quote( message[:85] ) ) )
			conn = httplib.HTTPConnection( url.netloc, timeout=10 )
			conn.request( 'GET', url.path )
			response = conn.getresponse()
			res = response.status
			conn.close()
			if res != 200:
				return 'Error:' + res + ' - ' + response.reason
			else:
				return 'OK'
		except IOError as e:
			return 'Cannot connect to LED server: "{0}"'.format( e )
		except:
			return 'Error: LED URL not set'

	def __random_quote( self ):
		"""Read a quote from a text file"""
		try:
			with open( self.get_config( 'quote_file' ) ) as fd:
				return random.choice( fd.readlines() )
		except IOError:
			return 'Error: quote file not found'
		except:
			return 'Error: no quote file defined'

