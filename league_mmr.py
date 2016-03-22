#!/usr/bin/python3

from database import LeagueDatabase
from parser import MMRParser

import datetime
import csv

def main():
    """
    Get the current MMR for all of the summoners listed in the
    `summoners.csv` file and store the data into a MySQL database.
    """

    database = LeagueDatabase("config.json")
    database.connect()

    with open("summoners.csv") as summoner_list:
        reader = csv.reader(summoner_list)
        parser = MMRParser()
        
        for row in reader:
            # ignore invalid rows
            if (len(row) != 2):
                continue

            # get MMR data: (summoner, region, mmr, date)
            summoner = row[0].strip()
            region   = row[1].strip()
            mmr      = parser.get_mmr(summoner, region)
            date     = str(datetime.date(1, 1, 1).today())

            # record MMR data into SQL database
            database.add_row(summoner, region, mmr, date)

    database.close()

if __name__ == "__main__":
    main()
