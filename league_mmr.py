#!/usr/bin/python3

"""
This is a script that takes all of the summoners from `summoners.csv`,
retrieves their current Matchmaking Rankings (MMR) and stores all of
the data into a MySQL database.
"""

import datetime
import csv
import json
import logging
import time
import urllib.request
import mysql.connector

from database import LeagueDatabase

__author__ = "Nelson Tran"
__email__ = "nelson@nelsontran.com"

LEAGUE_REGIONS = [
    "kr",   # Korea
    "euw",  # Europe West
    "oce",  # Oceania
    "las",  # Latin America South
    "ru",   # Russia
    "na",   # North America
    "eune", # Europe Nordic & East
    "br",   # Brazil
    "lan",  # Latin America North
    "tr"]   # Turkey

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

    logger.info("Connecting to the SQL database")
    # load MySQL database configuration from file
    try:
        database = LeagueDatabase("config.json")
    except ValueError:
        logger.error("Invalid JSON configuration file")

    # attempt to connect to the MySQL database;
    # retry connection if attempt fails
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
    with open("summoners.csv") as summoner_list:

        reader = csv.reader(summoner_list)
        new_rows = 0

        for row in reader:

            # ignore invalid rows
            if len(row) != 2:
                continue

            # get MMR data: (summoner, region, mmr, date)
            summoner = row[0].strip()
            region = row[1].strip()
            mmr = get_mmr(summoner, region)
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

def get_mmr(summoner, region):
    """
    Get the MMR of a summoner in a region by sending a GET request
    to op.gg and parsing the <text/json> response.

    Args:
        summoner (str): The name of the summoner.
        region (str): The abbreviation of the server/region that the
            summoner belongs to.

    Returns:
        int: The MMR of the summoner. This value will be 0 if
             (1) the summoner is not currently ranked or
             (2) the GET request failed.

    Raises:
        ValueError: A non-existent or unsupported region is passed
            in as an argument through `region`.
    """

    # normalize arguments
    summoner = summoner.strip().lower().replace(' ', '%20')
    region = region.strip().lower()

    if region not in LEAGUE_REGIONS:
        raise ValueError("Region does not exist")

    # construct op.gg GET request URL
    opgg = "http://"
    if region != "kr":
        opgg += region + '.'
    opgg += "op.gg/summoner/ajax/mmr.json/summonerName=" + summoner

    # parse text/json response
    response = urllib.request.urlopen(opgg).read().decode("utf-8")
    response_dict = json.loads(response)

    if "mmr" in response_dict.keys():
        return int(response_dict["mmr"].strip().replace(',', ''))
    else:
        return 0

if __name__ == "__main__":
    main()
