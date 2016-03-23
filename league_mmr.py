#!/usr/bin/python3

from database import LeagueDatabase

import datetime
import csv
import json
import urllib.request

league_regions = [
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

def main():
    """
    Get the current MMR for all of the summoners listed in the
    `summoners.csv` file and store the data into a MySQL database.
    """

    database = LeagueDatabase("config.json")
    database.connect()

    with open("summoners.csv") as summoner_list:
        reader = csv.reader(summoner_list)
        for row in reader:

            # ignore invalid rows
            if (len(row) != 2):
                continue

            # get MMR data: (summoner, region, mmr, date)
            summoner = row[0].strip()
            region   = row[1].strip()
            mmr      = get_mmr(summoner, region)
            date     = str(datetime.date(1, 1, 1).today())

            # record MMR data into SQL database
            database.add_row(summoner, region, mmr, date)

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

    if (region not in league_regions):
        raise ValueError("Region does not exist")

    # construct op.gg GET request URL
    opgg = "http://"
    if (region != "kr"):
        opgg += region + '.'
    opgg += "op.gg/summoner/ajax/mmr.json/summonerName=" + summoner

    # parse text/json response
    response = urllib.request.urlopen(opgg).read().decode("utf-8")
    response_dict = json.loads(response)

    if ("mmr" in response_dict.keys()):
        return int(response_dict["mmr"].strip().replace(',', ''))
    else:
        return 0

if __name__ == "__main__":
    main()
