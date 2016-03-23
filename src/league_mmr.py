#!/usr/bin/python3

"""
This is a script that takes all of the summoners from `summoners.csv`,
retrieves their current Matchmaking Rankings (MMR) and stores all of
the data into a MySQL database.
"""

import datetime
import csv
import logging
import time
import mysql.connector
import urllib.error

from wrapper import LeagueWrapper
from database import LeagueDatabase

__author__ = "Nelson Tran"
__email__ = "nelson@nelsontran.com"

FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(format=FORMAT)

def main():
    """
    Get the current MMR for all of the summoners listed in the
    `summoners.csv` file and store the data into a MySQL database.
    """

    # logging configuration
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # load configuration from file
    logger.info("Loading configuration from file")
    try:
        database = LeagueDatabase("config/config.json")
        wrapper = LeagueWrapper("config/config.json")
    except ValueError:
        logger.error("Invalid JSON configuration file")
        logger.error("SHUT DOWN!")
        quit()

    # attempt to connect to the MySQL database;
    # retry connection if attempt fails
    logger.info("Connecting to the SQL database")
    for _ in range(5):
        try:
            database.connect()
            break
        except mysql.connector.Error:
            logger.error("Failed to connect to the SQL database")
            time.sleep(60)
            continue

    # if we cannot connect to the MySQL database at this point,
    # terminate the script :(
    if not database.is_connected():
        logger.error("SHUT DOWN!")
        quit()

    # open list of summoners and find MMRs
    with open("config/summoners.csv") as summoner_list:

        reader = csv.reader(summoner_list)
        new_rows = 0

        for row in reader:

            # ignore invalid rows
            if len(row) != 2:
                continue

            # refresh OP.GG data
            try:
                wrapper.refresh_summoner(row[0], row[1])
                time.sleep(2)
            except LookupError:
                logger.warning("Cannot refresh summoner: summoner ID not found for " + row[0].strip())
            except urllib.error.HTTPError:
                logger.warning("Cannot refresh summoner: problem with specified API key") 

            # get MMR data
            summoner = row[0].strip()
            region = row[1].strip()
            mmr = wrapper.get_mmr(summoner, region)
            date = str(datetime.date(1, 1, 1).today())

            # record MMR data into SQL database
            if mmr != 0:
                success = database.add_row(summoner, region, mmr, date)
                if success:
                    new_rows += 1
                else:
                    logger.warning("Matchmaking Rating (MMR) already exists for " +
                                   summoner + " for " + date)
            else:
                logger.warning("Matchmaking Rating (MMR) was not found for " +
                               summoner + " for " + date)

    logger.info("%d new MMR entries have been added\n", new_rows)
    database.close()

if __name__ == "__main__":
    main()
