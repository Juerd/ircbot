from modules import Module
import logging
import random

class bofh(Module):
	def cmd_bofh( self, args, source, target, admin ):
		"""!bofh: to get a random BOFH excuse"""
		return [ self.__random_quote() ]

	def __random_quote( self ):
		"""Read a quote from a text file"""
		try:
			with open( self.get_config( 'quote_file' ), 'rt', encoding = 'utf-8' ) as fd:
				return 'The cause of the problem is: ' + random.choice( fd.readlines() )
		except IOError as e:
			logging.exception( 'Quote IOError' )
			return 'Error: quote file not found: {}'.format( e )
		except:
			logging.exception( 'Quote Exception' )
			return 'Error: no quote file defined'
