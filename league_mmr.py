#!/usr/bin/python3

import datetime
import csv
import json
import html.parser
import string
import sys
import mysql.connector
import urllib.request

def main():

	# connect to SQL database
	with open("config.json") as json_config:
		sql_config = json.load(json_config)

	sql_connection = mysql.connector.connect(**sql_config)
	sql_cursor = sql_connection.cursor()

	# create `league_mmr' table if doesn't already exist
	check_table_exists = ("SHOW TABLES LIKE 'league_mmr'")
	sql_cursor.execute(check_table_exists)
	results = sql_cursor.fetchall()

	if (len(results) == 0):
		sql_cursor.execute(
			"CREATE TABLE `league_mmr` ("
			"  `summoner` VARCHAR(16) NOT NULL,"
			"  `region` VARCHAR(4) NOT NULL,"
			"  `mmr` INT NOT NULL,"
			"  `date` DATE NOT NULL,"
			"  PRIMARY KEY (`summoner`, `region`, `date`),"
			"    KEY `summoner` (`summoner`),"
			"    KEY `region` (`region`),"
			"    KEY `date` (`date`)"
			") ENGINE=InnoDB")
	
	# fetch ranked MMRs from op.gg for the list of summoners in 
	# `league_mmr.csv' and insert the results into the SQL table
	add_mmr_record = (
		"INSERT INTO league_mmr "
		"(summoner, region, mmr, date) "
		"VALUES (%s, %s, %s, %s)")

	with open("summoners.csv") as summoner_list:
		csv_reader = csv.reader(summoner_list)
		for row in csv_reader:

			# skip empty lines
			if (len(row) != 2):
				continue

			# strip leading and trailing whitespace
			summoner = row[0].strip()
			region = row[1].strip()

			# make GET request from op.gg and fetch MMR for summoner
			mmr = get_mmr(summoner, region)
			date = str(datetime.date(1, 1, 1).today())

			# record MMR data in SQL database
			try:
				mmr_data = (summoner, region, mmr, date)
				print(str(mmr_data) + " ", end="")
				sql_cursor.execute(add_mmr_record, mmr_data)
			except mysql.connector.errors.IntegrityError:
				print("(row already exists in database)");

	sql_cursor.close()
	sql_connection.commit()
	sql_connection.close()

def get_mmr(summoner, region):

	# normalize arguments
	summoner = summoner.strip().lower().replace(' ', '%20')
	region = region.strip().lower()
	
	# construct op.gg GET request URL from arguments
	opgg = "http://"
	if (region.lower() != "kr"):
		opgg += region + '.'
	opgg += "op.gg/summoner/ajax/mmr/summonerName=" + summoner

	# parse <text/html> response
	request = urllib.request.urlopen(opgg)
	parser = MMRParser()
	parser.feed(request.read().decode("utf-8"))
	request.close()

	return parser.get_mmr()

class MMRParser(html.parser.HTMLParser):

	found_tag = False
	mmr = 0

	def handle_starttag(self, tag, attrs):
		if (tag == "div" and attrs[0][0] == "class" and attrs[0][1] == "MMR"):
			self.found_tag = True

	def handle_endtag(self, tag):
		self.found_tag = False

	def handle_data(self, data):
		if (self.found_tag):
			self.mmr = int(data.strip().replace(',', ''))

	def get_mmr(self):
		return self.mmr

if __name__ == "__main__":
	main()

