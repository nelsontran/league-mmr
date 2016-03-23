#!/usr/bin/python3

"""
This module is a small wrapper for accessing the official League of
Legends API and for accessing OP.GG's JSON endpoints.
"""

import json
import urllib.request

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

class LeagueWrapper(object):
    """
    A collection of wrapper methods to refresh a summoner's data on OP.GG
    and to retrieve a summoner's current Matchmaking Rating (MMR).
    """

    api_key = ""

    def __init__(self, config):
        """
        Load the League of Legends API key from the JSON configuration
        file.
        """

        with open(config) as json_config:
            config = json.load(json_config)
            if "apiKey" in config:
                self.api_key = config["apiKey"]

    def refresh_summoner(self, summoner, region):
        """
        Refresh the specified summoner's data on OP.GG.

        Args:
            summoner (str): The name of the summoner.
            region (str): The abbreviation of the server/region that the
                summoner belongs to.
        """

        # normalize arguments
        summoner, region = self.__normalize(summoner, region)

        if region not in LEAGUE_REGIONS:
            raise ValueError("Region does not exist")

        # get summoner ID from summoner name and region
        summoner_id = str(self.__get_summoner_id(summoner, region))

        if summoner_id is None:
            raise LookupError("Summoner ID not found for " + summoner)

        # construct GET request URL
        request = "http://"
        if region != "kr":
            request += region + '.'
        request += "op.gg/summoner/ajax/update.json/summonerId=" + summoner_id

        # send GET request
        urllib.request.urlopen(request)

    def get_mmr(self, summoner, region):
        """
        Get the MMR of a summoner in a region.

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
        summoner, region = self.__normalize(summoner, region)

        if region not in LEAGUE_REGIONS:
            raise ValueError("Region does not exist")

        # construct GET request URL
        request = "http://"
        if region != "kr":
            request += region + '.'
        request += "op.gg/summoner/ajax/mmr.json/summonerName=" + summoner

        # parse response
        response = urllib.request.urlopen(request).read().decode("utf-8")
        response_dict = json.loads(response)

        if "mmr" in response_dict.keys():
            return int(response_dict["mmr"].strip().replace(',', ''))
        else:
            return 0

    def __get_summoner_id(self, summoner, region):
        """
        Get the summoner ID given the summoner name.

        Args:
            summoner (str): The name of the summoner.
            region (str): The abbreviation of the server/region that the
                summoner belongs to.

        Returns:
            int: The summoner ID of the summoner.
            None: If the summmoner ID was not found.
        """

        # construct GET request URL
        request = "https://" + region + ".api.pvp.net/api/lol/" + \
            region + "/v1.4/summoner/by-name/" + summoner + \
            "?api_key=" + self.api_key

        # parse response
        response = urllib.request.urlopen(request).read().decode("utf-8")
        response_dict = json.loads(response)

        if summoner in response_dict.keys():
            return response_dict[summoner]["id"]
        else:
            return None

    def __normalize(self, summoner, region):
        """
        Strip leading and trailing whitespace from the arguments and
        remove spaces.
        """

        summoner = summoner.strip().lower().replace(' ', '')
        region = region.strip().lower()

        return summoner, region
