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
	def __init__( self, config, bot ):
		_module.__init__( self, config, bot )
		self.space_open_data = None
		self.space_status = ( None, None )
		try:
			self.thread = StatusMonitor( self )
			self.thread.start()
		except Exception as e:
			print( 'Thread exception: {0}'.format( e ) )
	
	def stop(self):
		self.thread.stop()
		self.thread.join()

	def can_handle( self, cmd, admin ):
		return cmd in ( 'status', 'led', 'time', 'quote' ) or admin and cmd in ( 'admin_help', 'force_status', 'force_topic_update' )

	def handle( self, bot, cmd, args, source, target, admin ):
		( local_status, status_date ) = self.__get_space_status()
		if admin:
			if cmd == 'admin_help':
				bot.notice( source, '!force_status <status>: force a status update' )
				bot.notice( source, '!force_topic_update: force a topic update' )
			elif cmd == 'force_status':
				if len( args ) == 0: return
				if args[0] in ( '0', '1' ):
					self.set_space_status( args[0], time.time() )
			elif cmd == 'force_topic_update':
				self.__set_topic( '#tkkrlab', 'We zijn Open' if self.space_open else 'We zijn Dicht' )
				return
		if cmd == 'help':
			return [
				'!quote: to get a random quote',
				'!status: to get open/close status of the space',
				'!led message: put message on led matrix board',
				'!time: put current time on led matrix board',
			]
		elif cmd == 'quote':
			return [ 'Quote: ' + self.__random_quote() ]
		elif cmd == 'status':
			if local_status not in ( True, False ):
				return [ 'Error: status is not True/False but {0}'.format( local_status ) ]
			else:
				return [ 'We are {0} since {1}'.format( 'Open' if local_status == True else 'Closed', datetime.datetime.fromtimestamp( status_date, tzlocal() ).strftime( '%a, %d %b %Y %H:%M:%S %Z' ) ) ]
		elif cmd == 'led':
			if local_status == True:
				return [ 'Led: {0}'.format( self.__send_led( ' '.join( args ) ) ) ]
			elif local_status == False:
				return [ 'Sorry ' + source + ', can only do this when space is open.' ]
			else:
				return [ 'Error: ' + local_status ]
		elif cmd == 'time':
			self.__send_led( time.strftime( '%H:%M' ).center( 16 ) )

	def set_space_status( self, status, aTime ):
		( space_open, space_time ) = self.space_status
		if space_open == None:
			space_open = status == '1'
		if space_open != ( status == '1' ):
			space_open = status == '1'
			self.__set_topic( '#tkkrlab', 'We zijn Open' if space_open else 'We zijn Dicht' )
		self.space_status = ( space_open, aTime )
		return self.space_status
		
	def __get_space_status( self ):
		return self.space_status

	def __set_topic( self, channel, new_topic ):
		self.bot.connection.topic( channel, new_topic + ' | See our activities on http://bit.ly/AsJMNc' )
		self.bot.privmsg( channel, new_topic )

	def __send_led( self, message):
		"""Send a command to the led board"""
		try:
			url = urlparse.urlparse( self.led_url.format( urllib.quote( message[:85] ) ) )
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
		except AttributeError:
			return 'LED URL not set'

	def __random_quote( self ):
		"""Read a quote from a text file"""
		try:
			with open( self.quote_file ) as fd:
				return random.choice( fd.readlines() )
		except AttributeError:
			return 'Error: no quote file defined'
		except IOError:
			return 'Error: quote file not found'

