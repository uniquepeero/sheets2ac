import requests
import logging
import os
import configparser
import gspread
import pickle
import random
import re
import string
from oauth2client.service_account import ServiceAccountCredentials
from time import sleep
from ipaddress import ip_address

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
fh = logging.FileHandler("logs.log", encoding="utf-8")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)


class User:

	def __init__(self, name):
		if os.path.isfile('cfg/config.ini'):
			self.config = configparser.ConfigParser()
			self.config.read('cfg/config.ini')
			self.NAME = name
			self.API = self.config[self.NAME]['API']
			self.URL = self.config['URL']['url']

			scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
			creds = ServiceAccountCredentials.from_json_keyfile_name(f'cfg/{self.NAME}.json', scope)
			client = gspread.authorize(creds)
			self.sheet = client.open(f'{self.NAME} to AC').sheet1
			log.debug(f'{name} connected to Sheets')
			sleep(2)
		else:
			log.critical('Configuration file not found')

	def send(self, location, name, phone):
		country = countryprice(location)['country']
		price = countryprice(location)['price']
		params = {
			'api_key': self.API,
			'name': name,
			'phone': phone,
			'offer_id': self.config[self.NAME][country],
			'country_code': self.config['Countries'][country],
			'base_url': f'https://land1.abyz.xyz/{randomString()}',
			'price': price,
			'referrer': f'https://{randomString(5)}.com/{randomString()}',
			'ip': country_ip(country)
		}
		try:
			res = requests.get(self.URL, params=params)
			if res.status_code == requests.codes.ok:
				log.debug(f'Success send: {res.json()}')
				return res.json()
			else:
				log.error(f'Unsuccess send request: {res.status_code} , {params}')
				return res.json()['error']
		except Exception as e:
			log.critical(f'Send request', exc_info=True)


	def checkvalues(self):
		last = self.sheet.acell('H1').value
		if len(last) > 0:
			last = int(last)
		else:
			return
		sleep(1)
		while True:
			row = self.sheet.row_values(last + 1)
			sleep(1)
			if row:
				last += 1
				sended = self.send(row[1], row[2], row[3])
				if 'error' not in sended.keys():
					self.sheet.update_cell(last, 5, sended['order_id'])
				else:
					log.error(f'Send: {sended["error"]}')
				sleep(1)
			else:
				break
		self.sheet.update_acell('H1', last)
		sleep(1)


def country_ip(country):
	country = country.lower()
	with open(f'data/{country}.data', 'rb') as datfile:
		ranges = pickle.load(datfile)
	range = random.choice(ranges)
	range = range.replace('\n', '')
	IPs = re.findall(r'([^-]*)', range)
	start, end = IPs[0], IPs[2]
	iplist = ips(start, end)
	return random.choice(iplist)


def storeips(country):
	ranges = []
	with open(f'txt/{country}.txt') as file:
		lines = file.readlines()
		for line in lines:
			print(line)
			ranges.append(line)
	with open(f'data/{country}.data', 'wb') as datfile:
		pickle.dump(ranges, datfile)


def ips(start, end):
    start_int = int(ip_address(start).packed.hex(), 16)
    end_int = int(ip_address(end).packed.hex(), 16)
    return [ip_address(ip).exploded for ip in range(start_int, end_int)]


def randomString(strlen=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(strlen))


def countryprice(string):
	country = re.search(r'^[a-zA-Z ]*', string)
	country = country.group(0)
	country = country[:-1]
	price = re.search(r'[0-9]+', string)
	price = price.group(0)
	return {
		'country': country,
		'price': price
	}


			
if __name__ == '__main__':
	try:
		log.info('Started')
		user1 = User('Artur')
		user2 = User('Tima')
		user3 = User('Artem')
		while True:
			user1.checkvalues()
			user2.checkvalues()
			user3.checkvalues()
	except Exception as e:
		log.critical('Main proccess', exc_info=True)
	finally:
		log.info('Closed')