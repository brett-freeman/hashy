from willie.module import rule
import re

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from datetime import datetime
from os import path, environ

basedir = path.abspath(path.dirname(__file__))
Base = declarative_base()
database_url = environ.get('HASHY_DATABASE_URL') if environ.get('HASHY_DATABASE_URL') else 'sqlite:////home/vagrant/am.db'
db = create_engine(database_url)
Session = sessionmaker(bind=db)

url_finder = re.compile(r'(?u)(?:http|https|ftp)(?:://\S+)')

class Link(Base):
	__tablename__ = 'links'
	id = Column(Integer, primary_key=True)
	url = Column(String)
	nickname = Column(String)
	last_sent = Column(DateTime)


@rule('(?u).*(https?://\S+).*')
def catch_link(bot, trigger):
	if trigger.sender == '#hashy':
		return

	urls = re.findall(url_finder, trigger)
	if urls:
		session = Session()
		for url in urls:
			link = Link(url=url, nickname=trigger.nick, last_sent=datetime.utcnow())
			try:
				session.add(link)
				session.commit()
			except:
				session.rollback()
		session.close()
	return