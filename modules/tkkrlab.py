from _module import _module
import httplib
import datetime
from dateutil.tz import tzlocal
import dateutil.parser
import random

class tkkrlab( _module ):
	def __init__( self, config ):
		_module.__init__( self, config )
		self.space_open = None

	def can_handle( self, cmd, admin ):
		return cmd in ( 'status', 'led', 'quote', 'help' )
	def handle( self, bot, cmd, args, source, target, admin ):
		( local_status, status_date ) = self.__get_local_status()
		if cmd == 'help':
			for line in [
				'!quote: to get a random quote',
				'!status: to get open/close status of the space',
				'!led message: put message on led matrix board',
				#'!time: put current time on led matrix board',
				'!help: this message',
				'See also my friends Lock-O-Matic and arcade 1943 (if he is around)',
			]:
				bot.privmsg( target, line )
		elif cmd == 'quote':
			bot.privmsg( target, 'Quote: ' + self.__random_quote() )
		elif cmd == 'status':
			bot.privmsg( target, 'We are {0}'.format( 'Open' if local_status == True else 'Closed' ) )
		elif cmd == 'led':
			if local_status == True:
				bot.privmsg( target, 'Led ' + self.__send_led( ' '.join( args ) ) )
			elif local_status == False:
				bot.privmsg( target, 'Sorry ' + source + ', can only do this when space is open.' )
			else:
				bot.privmsg( target, 'Error: ' + local_status )
		elif cmd == 'time':
			pass

	def __get_local_status( self ):
		try:
			with open( self.statusfile ) as fd:
				space_opened = fd.readline().strip()
				if self.space_open == None:
					self.space_open = space_opened == '1'

				if self.space_open != ( space_opened == '1' ):
					self.space_open = space_opened == '1'
					self.__set_topic( bot, '#tkkrlab', 'We zijn Open' if self.space_open else 'We zijn Dicht' )
			return ( self.space_open, None )
		except AttributeError:
			self.space_open = 'No status file configured'
		except IOError:
			self.space_open = 'No status file found'
		return ( self.space_open, None )

	def __set_topic( self, bot, channel, new_topic ):
		bot.connection.topic( channel, new_topic )
		bot.privmsg( channel, new_topic )

	def __send_led( self, message ):
		pass

	def __random_quote( self ):
		"""Read a quote from a text file"""
		try:
			with open( "quotes.txt" ) as fd:
				return random.choice( fd.readlines() )
		except IOError:
			return 'No quote file found'

