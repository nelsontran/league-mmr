#!/usr/bin/python3

"""
This module provides an easy interface for connecting to a MySQL
database and for inserting Matchmaking Rating (MMR) data into that
database.

Example Usage:
    config = "/path/to/config.json"
    database = LeagueDatabase(config)
    database.connect()
    database.add_row("Summoner", "NA", 1337, "2016/03/22")
    database.close()
"""

import json
import re
import mysql.connector

__author__ = "Nelson Tran"
__email__ = "nelson@nelsontran.com"

class LeagueDatabase(object):
    """
    Provides a set of methods for connecting to a MySQL database and
    inserting MMR data into that database.
    """

    connected = False

    sql_config_attrs = [
        "user",
        "password",
        "host",
        "port",
        "database",
        "table"]

    sql_connection = None
    sql_cursor = None
    sql_config = {}

    mmr_table = ""

    def __init__(self, config):
        """
        Construct a LeagueDatabase object and load configuration from
        a file.

        Args:
            config (str): The file path to a JSON file that contains
                all of the configuration information needed to connect
                to an SQL database.
        """

        # load configuration data from file
        with open(config) as json_config:
            self.sql_config = json.load(json_config)

            if not set(self.sql_config.keys()) >= set(self.sql_config_attrs):
                raise ValueError("Invalid SQL config file")

        # the `table` attribute is not needed for connecting to a
        # database using the MySQL connector so we will move it out
        # of the dictionary into its own variable
        self.mmr_table = self.sql_config.pop("table")

        if "apiKey" in self.sql_config:
            self.sql_config.pop("apiKey")

    def add_row(self, summoner, region, mmr, date):
        """
        Insert MMR data for a summoner into the MMR table in the
        database.

        Args:
            summoner (str): The name of the summoner.
            region (str): The server/region abbreviation.
            mmr (int): The MMR of the summoner.
            date (str): The date associated with the summoner/MMR.

        Returns:
            True if the transaction was successful; False otherwise.

        Raises:
            ValueError: If `date` does not match the format of the MySQL
                date type format (YYYY-MM-DD).
        """

        is_success = True

        date_regex_pattern = "^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]"
        if not re.match(date_regex_pattern, date):
            raise ValueError("Invalid date format, should be YYYY-MM-DD")

        try:
            add_mmr_record = (
                "INSERT INTO " + self.mmr_table + " "
                "(summoner, region, mmr, date) "
                "VALUES (%s, %s, %s, %s)")

            mmr_record = (summoner, region, mmr, date)
            self.sql_cursor.execute(add_mmr_record, mmr_record)
            self.sql_connection.commit()

        except mysql.connector.errors.IntegrityError:
            # most likely due to already existing record for the date;
            # only one MMR record per day per summoner
            is_success = False

        return is_success

    def connect(self):
        """
        Connect to a MySQL database using the configuration loaded in
        from the constructor and then check to see if a table exists
        for inserting MMR data. If not, create that table.
        """

        self.sql_connection = mysql.connector.connect(**self.sql_config)
        self.sql_cursor = self.sql_connection.cursor()

        self.connected = True

        if not self.__table_exists():
            self.__create_table()

    def close(self):
        """
        Close all database connection resources.
        """

        self.sql_cursor.close()
        self.sql_connection.close()

    def is_connected(self):
        """
        Returns True if connection to a MySQL database has been
        established; False otherwise.
        """

        return self.connected

    def __create_table(self):
        """
        Create a new table in the database with the following schema:
        (SUMMONER, REGION, MMR, DATE). The primary key is defined to be
        (SUMMONER, REGION, DATE). The name of the database will be the
        same as the one specified in the JSON configuration file.
        """

        self.sql_cursor.execute(
            "CREATE TABLE `" + self.mmr_table + "` ("
            "  `summoner` VARCHAR(16) NOT NULL,"
            "  `region` VARCHAR(4) NOT NULL,"
            "  `mmr` INT NOT NULL,"
            "  `date` DATE NOT NULL,"
            "  PRIMARY KEY (`summoner`, `region`, `date`),"
            "    KEY `summoner` (`summoner`),"
            "    KEY `region` (`region`),"
            "    KEY `date` (`date`)"
            ") ENGINE=InnoDB")

    def __table_exists(self):
        """
        Check if the table specified in the JSON configuration file
        exists in the database. Returns True if it exists; False
        otherwise.
        """

        self.sql_cursor.execute("SHOW TABLES LIKE '" + self.mmr_table + "'")
        results = self.sql_cursor.fetchall()

        return bool(len(results))
