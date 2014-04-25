from willie.module import commands, nickname_commands, rule, priority
from willie.tools import Nick

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from datetime import datetime
from os import path, environ

basedir = path.abspath(path.dirname(__file__))
Base = declarative_base()
database_url = environ.get('HASHY_DATABASE_URL') if environ.get('HASHY_DATABASE_URL') else 'sqlite:////home/vagrant/am.db'
db = create_engine(database_url)
Session = sessionmaker(bind=db)

class Message(Base):
	__tablename__ = 'messages'
	id = Column(Integer, primary_key=True)
	nick_to = Column(String)
	nick_from = Column(String)
	msg = Column(Text)
	time_sent = Column(DateTime)

@commands('tell')
@nickname_commands('tell')
def catch_message(bot, trigger):
	sender = trigger.nick

	if not trigger.group(3):
		return bot.reply('Tell whom?')

	receiver = trigger.group(3).rstrip('.,:;')
	msg = trigger.group(2).lstrip(receiver).lstrip()
	receiver = receiver.lower()

	if not msg:
		return bot.reply('No message detected.')
	if len(receiver) > 20:
		return bot.reply('Nickname is too long.')
	if receiver == bot.nick:
		return bot.reply('Thanks for telling me that.')

	if not receiver in (Nick(sender), bot.nick, 'me'):
		time_sent = datetime.utcnow()

		message = Message(nick_to=receiver, nick_from=sender, msg=msg, time_sent=time_sent)
		session = Session()

		try:
			session.add(message)
			session.commit()
		except OperationalError:
			session.rollback()
		finally:
			session.close()
		return bot.reply('Message stored.')
	elif Nick(sender) == receiver:
		return bot.say('You can tell yourself that!')

@rule('(.*)')
@priority('low')
def deliver_message(bot, trigger):
	receiver = trigger.nick
	session = Session()
	receiver = receiver.lower()

	if not session.query(Message).filter_by(nick_to=receiver).first():
		session.close()
		return

	messages = session.query(Message).filter_by(nick_to=receiver).all()
	for message in messages:
		bot.reply("%s (from %s)" % (message.msg, message.nick_from))
		try:
			session.delete(message)
			session.commit()
		except OperationalError:
			session.rollback()
	session.close()
	return