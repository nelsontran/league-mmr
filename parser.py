#!/usr/bin/python3

import html.parser
import string
import urllib.request

class MMRParser(html.parser.HTMLParser):

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

    found_tag = False
    mmr = 0

    def get_mmr(self, summoner, region):
        """
        Get the MMR of a summoner in a region by sending a GET request
        to op.gg and parsing the <text/html> response.

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

        # reset HTML parser
        self.reset()
        self.mmr = 0

        # normalize arguments
        summoner = summoner.strip().lower().replace(' ', '%20')
        region = region.strip().lower()

        if (region not in self.league_regions):
            raise ValueError("Region does not exist")

        # construct op.gg GET request URL
        opgg = "http://"
        if (region != "kr"):
            opgg += region + '.'
        opgg += "op.gg/summoner/ajax/mmr/summonerName=" + summoner

        # parse text/html response
        request = urllib.request.urlopen(opgg)
        self.feed(request.read().decode("utf-8"))
        request.close()

        return self.mmr

    def handle_starttag(self, tag, attrs):
        """
        Ignore all HTML tags until <div class="MMR"> is found. Then,
        set a flag to let handle_data(data) know to parse the the MMR.
        """

        if (tag == "div" and attrs[0][0] == "class" and attrs[0][1] == "MMR"):
            self.found_tag = True

    def handle_endtag(self, tag):
        """
        Set `found_tag` flag to False so handle_data(data) stops parsing
        the content of subsequent HTML tags.
        """
        
        self.found_tag = False

    def handle_data(self, data):
        """
        Parse the HTML tag content the position on the parser pointer is
        inside of the <div class="MMR"> tag.
        """

        if (self.found_tag):
            self.mmr = int(data.strip().replace(',', ''))
