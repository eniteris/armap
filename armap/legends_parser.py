# TODO: Add license

import os
import re
from typing import Any

from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from .config_parser import ConfigParser

class LegendParser():
    """TODO: add description"""

    def __init__(self, config):
        self.config: ConfigParser = config
        self.world_translated_name: str = ""
        self.world_name: str = ""
        self.maps = {}
        self.d_regions = {}
        self.d_sites = {}
        self.d_entities = {}
        self.d_coll = {}
        self.occ_sites = {}
        self.entities = {}
        self.active_wars = {}

    def parse(self, folder: str) -> None:
        """Function to parse legends and generate parameters.
        
        :param folder: folder containing DF legend files.
        """
        print("Beginning parsing of " + folder)
        print("Parsing files...")
        self.maps, legends, pops, world_history = self.scan_folder(folder)

        self.parse_xml(legends)
        self.parse_history(world_history)

        if self.config.site_check:
            self.parse_pops(pops)

            print("Filtering pops...")
            # Appends sites with minimum population to required list
            for k in self.d_sites:
                if "pop" in self.d_sites[k] and self.d_sites[k]["pop"] > self.config.min_pop:
                    self.config.required_cities.append(self.d_sites[k]["name"])
                    print(self.d_sites[k]["name"].title(), "has a population of", self.d_sites[k]["pop"])

            # Count number of sites each civ has
            for k, v in self.d_sites.items():
                if "ruler" in v and int(v["ruler"]) >= 0:
                    self.occ_sites[k] = v
                    if v["ruler"] in self.entities:
                        self.entities[v["ruler"]] += 1
                    else:
                        self.entities[v["ruler"]] = 1

            # Filter civilizations with less than minimum cities
            f_entities = [
                k for k, v in
                self.entities.items()
                if v >= self.config.min_cities
            ]
            entities_before_filter = len(self.entities)
            self.entities = dict.fromkeys(f_entities, 0)
            print(f"Entities filtered from {entities_before_filter} to {len(self.entities)}")
            print("Change min_cities parameter to adjust number of entities")
            print("Calculating Wars...")
            for k in self.d_coll:
                if self.d_coll[k]["type"] == "war" and self.d_coll[k]["end_year"] == "-1":
                    agressor = int(self.d_coll[k]["aggressor_ent_id"])
                    defender = int(self.d_coll[k]["defender_ent_id"])
                    if agressor in self.active_wars:
                        self.active_wars[agressor].add(defender)
                    elif defender in self.active_wars:
                        self.active_wars[defender].add(agressor)
                    else:
                        self.active_wars[agressor] = set()
                        self.active_wars[agressor].add(defender)

    def parse_xml(self, legends_file: str) -> None:
        """TODO: add description"""
        print("Parsing XML...")
        tree = ElementTree.parse(legends_file)

        # Get specific elements on the XML tree
        regions = tree.find("regions")
        sites = tree.find("sites")
        entities = tree.find("entities")
        collections = tree.find("historical_event_collections")

        # Parse the XML tree into dictionaries
        if regions:
            self.d_regions = self.parse_regions(regions)
        else:
            # TODO: replace by specific exception
            raise Exception()
        if sites:
            self.d_sites = self.parse_sites(sites)
        else:
            # TODO: replace by specific exception
            raise Exception()
        if entities:
            self.d_entities = self.parse_entities(entities)
        else:
            # TODO: replace by specific exception
            raise Exception()
        if collections:
            self.d_coll = self.parse_collections(collections)
        else:
            # TODO: replace by specific exception
            raise Exception()

    def parse_history(self, history_file: str) -> None:
        """TODO: add description"""
        print("Parsing history...")
        with open(history_file, "r", encoding="cp850", errors="ignore") as file:
            self.world_translated_name = file.readline().strip()
            self.world_name = file.readline().strip()

    def parse_pops(self, pops_file: str) -> None:
        """TODO: add description"""
        print("Parsing pops...")
        civ_id = None  # will use the civ id as a flag

        site_pattern = re.compile(r'(\d+): ([^,]+), "([^,]+)", ([^,\n]+)')
        civ_pattern = re.compile(r'(?:\t)Owner: ([^,]+), (\w+)')
        parent_pattern = re.compile(r'(?:\t)Parent Civ: ([^,]+), (\w+)')
        pop_pattern = re.compile(r'(?:\t)(\d+) (goblin.*|kobold.*|dwar(?:f|ves).*|human.*|el(?:f|ves).*)')

        with open(pops_file, "r", encoding="cp850", errors="ignore") as file:
            for line in file:
                site = site_pattern.match(line)
                civ = civ_pattern.match(line)
                parent = parent_pattern.match(line)
                pop = pop_pattern.match(line)
                if site:
                    civ_id = site.group(1)
                    self.d_sites[civ_id]["trans"] = site.group(2)
                elif civ and civ_id:
                    entity_key = next(
                        (k for k, v in
                         self.d_entities.items()
                         if v.lower() == civ.group(1).lower()),
                        None
                    )
                    self.d_sites[civ_id]["ruler"] = entity_key
                    self.d_sites[civ_id]["civ_name"] = civ.group(1)
                    self.d_sites[civ_id]["civ_race"] = civ.group(2)
                elif parent and civ_id:
                    entity_key = next(
                        (k for k, v in
                         self.d_entities.items()
                         if v.lower() == parent.group(1).lower()),
                        None
                    )
                    self.d_sites[civ_id]["ruler"] = entity_key
                    self.d_sites[civ_id]["parent_name"] = parent.group(1)
                    self.d_sites[civ_id]["parent_race"] = parent.group(2)
                elif pop and civ_id:
                    self.d_sites[civ_id]["pop"] += int(pop.group(1))
                elif "Outdoor" in line:
                    print(self.d_sites)
                    break

    def scan_folder(self, folder: str) -> tuple[dict[str, str], str, str, str]:
        """Receives a folder path to scan and parse the files inside"""

        files = os.listdir(folder)

        maps = {}
        legends = None
        pops = None
        world_history = None

        for file in files:
            if ".bmp" in file:
                m = re.search(r"([^-]*)\.bmp", file)
                if m:
                    maps[m.group(1)] = os.path.join(folder, file)
            elif "legends.xml" in file:
                legends = os.path.join(folder, file)
            elif "pops.txt" in file:
                pops = os.path.join(folder, file)
            elif "world_history.txt" in file:
                world_history = os.path.join(folder, file)

        if not maps:
            # TODO: replace with specific exception
            print("Could not locate any maps file")
            raise Exception()
        elif not legends:
            # TODO: replace with specific exception
            print("Could not locate legends file")
            raise Exception()
        elif not pops:
            # TODO: replace with specific exception
            print("Could not locate pops file")
            raise Exception()
        elif not world_history:
            # TODO: replace with specific exception
            print("Could not locate world history file")
            raise Exception()

        return maps, legends, pops, world_history

    def parse_regions(self, regions: Element) -> dict[str, dict[str, str]]:
        """
        Parse each region to create a dictionary
        """
        d_regions = {}
        for child in regions:
            d_regions[child[0].text] = {
                "name": child[1].text,
                "type": child[2].text
            }

        return d_regions

    def parse_sites(self, sites: Element) -> dict[str, dict[str, Any]]:
        """
        Parse each site to create a dictionary
        """
        d_sites = {}
        for child in sites:
            if len(child) > 1:
                rect = child[4].text.split(":")
                d_sites[child[0].text] = {
                    "type": child[1].text,
                    "name": child[2].text,
                    "pos": child[3].text.split(","),
                    "rect": list(x.split(",") for x in rect),
                    "pop": 0,
                    "ruler": -1
                }
        return d_sites

    def parse_entities(self, entities: Element) -> dict[str, str]:
        """
        Parse each entity to create a dictionary
        """
        d_entities = {}
        for child in entities:
            if len(child) > 1:
                d_entities[child[0].text] = child[1].text

        return d_entities

    def parse_collections(self, collections: Element) -> dict[str, dict[str, str]]:
        """
        Parse each entity to create a dictionary
        """
        d_collections = {}
        for child in collections:
            d_collections[child[0].text] = {}
            for c in child:
                d_collections[child[0].text][c.tag] = c.text

        return d_collections
