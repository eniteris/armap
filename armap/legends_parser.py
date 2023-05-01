# TODO: Add license

import os
import re

import xml.etree.ElementTree as ElementTree

class LegendParser():
    """TODO: add description"""

    def __init__(self, config):
        self.config = config

    def parse(self, folder: str) -> dict | None:
        """Function to parse legends and generate parameters.
        
        :param folder: folder containing DF legend files.
        """
        print("Beginning parsing of " + folder)
        print("Parsing files...")
        try:
            maps, legends, pops, world_history = self.scan_folder(folder)
        except Exception as e:
            print(e)
            return None

        print("Parsing XML...")
        tree = ElementTree.parse(legends)

        regions = tree.find("regions")
        sites = tree.find("sites")
        entities = tree.find("entities")
        events = tree.find("historical_events")
        collections = tree.find("historical_event_collections")

        d_regions = self.parse_regions(regions)
        d_sites = self.parse_sites(sites)
        d_entities = self.parse_entities(entities)
        d_event = self.parse_events(events)
        d_coll = self.parse_collections(collections)

        print("Parsing history...")
        with open(world_history, "r", encoding="cp850", errors="ignore") as file:
            world_translated_name = file.readline().strip()
            world_name = file.readline().strip()

        if self.config.site_check:
            print("Parsing pops...")
            civ_id = None  # will use the civ id as a flag

            site_pattern = re.compile(r'(\d+): ([^,]+), "([^,]+)", ([^,\n]+)')
            civ_pattern = re.compile(r'(?:\t)Owner: ([^,]+), (\w+)')
            parent_pattern = re.compile(r'(?:\t)Parent Civ: ([^,]+), (\w+)')
            pop_pattern = re.compile(r'(?:\t)(\d+) (goblin.*|kobold.*|dwar(?:f|ves).*|human.*|el(?:f|ves).*)')

            with open(pops, "r", encoding="cp850", errors="ignore") as file:
                for line in file:
                    site = site_pattern.match(line)
                    civ = civ_pattern.match(line)
                    parent = parent_pattern.match(line)
                    pop = pop_pattern.match(line)
                    if site:
                        civ_id = site.group(1)
                        d_sites[civ_id]["trans"] = site.group(2)
                    elif civ and civ_id:
                        civ_name = civ.group(1).lower()
                        entity_key = next((key for key, val in d_entities.items() if val == civ_name), None)
                        d_sites[civ_id]["ruler"] = entity_key
                        d_sites[civ_id]["civ_name"] = civ.group(1)
                        d_sites[civ_id]["civ_race"] = civ.group(2)
                    elif parent and civ_id:
                        parent_name = parent.group(1).lower()
                        entity_key = next((key for key, val in d_entities.items() if val == parent_name), None)
                        d_sites[civ_id]["ruler"] = entity_key
                        d_sites[civ_id]["parent_name"] = parent.group(1)
                        d_sites[civ_id]["parent_race"] = parent.group(2)
                    elif pop and civ_id:
                        d_sites[civ_id]["pop"] += int(pop.group(1))
                    elif "Outdoor" in line:
                        break

            for c in d_sites:
                if "pop" in d_sites[c] and d_sites[c]["pop"] > self.config.min_pop:
                    self.config.required_cities.append(d_sites[c]["name"])
                    print(d_sites[c]["name"].title(), "has a population of", d_sites[c]["pop"])

            print("Calculating owners...")
            event_types = ["destroyed site", "hf destroyed site", "new site leader", "reclaim site", "site taken over"]
            fevent = {}
            for e in d_event:
                t = d_event[e]["type"]
                if t in event_types:
                    fevent[e] = d_event[e]

            # Count number of sites each civ has
            entities = {}
            occ_sites = {}
            for s in d_sites:
                x = d_sites[s]
                if "ruler" in x:
                    if int(x["ruler"]) == -1:
                        continue
                    occ_sites[s] = x
                    if x["ruler"] in entities:
                        entities[x["ruler"]] += 1
                    else:
                        entities[x["ruler"]] = 1

            # Filter civilizations with less than minimum cities
            nents = {}
            for e in entities:
                if entities[e] > self.config.min_cities:
                    nents[e] = entities[e]
            entities = nents

            active_wars = {}
            for e in d_coll:
                if d_coll[e]["type"] == "war" and d_coll[e]["end_year"] == "-1":
                    agressor = int(d_coll[e]["aggressor_ent_id"])
                    defender = int(d_coll[e]["defender_ent_id"])
                    if agressor in active_wars:
                        active_wars[agressor].append(defender)
                    elif defender in active_wars:
                        active_wars[defender].append(agressor)
                    else:
                        active_wars[agressor] = []
                        active_wars[agressor].append(defender)

            for key in active_wars:
                active_wars[key] = set(active_wars[key])

        parameters = {
            "maps": maps,
            "world_translated_name": world_translated_name,
            "world_name": world_name,
            "d_sites": d_sites,
            "d_regions": d_regions,
            "occ_sites": occ_sites,
            "entities": entities,
            "active_wars": active_wars
        }

        return parameters

    def scan_folder(self,folder_path):
        """Receives a folder path to scan and parse the files inside"""

        files = os.listdir(folder_path)

        maps = {}
        legends = None
        pops = None
        world_history = None

        for file in files:
            if ".bmp" in file:
                m = re.search(r"([^-]*)\.bmp", file)
                if m:
                    maps[m.group(1)] = os.path.join(folder_path, file)
            elif "legends.xml" in file:
                legends = os.path.join(folder_path, file)
            elif "pops.txt" in file:
                pops = os.path.join(folder_path, file)
            elif "world_history.txt" in file:
                world_history = os.path.join(folder_path, file)

        if not maps:
            print("Could not locate any maps file")
            raise Exception()
        elif not legends:
            print("Could not locate legends file")
            raise Exception()
        elif not pops:
            print("Could not locate pops file")
            raise Exception()
        elif not world_history:
            print("Could not locate world history file")
            raise Exception()

        return maps, legends, pops, world_history
    

    def parse_regions(self, regions):
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

    def parse_sites(self, sites):
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

    def parse_entities(self, entities):
        """
        Parse each entity to create a dictionary
        """
        d_entities = {}
        for child in entities:
            if len(child) > 1:
                d_entities[child[0].text] = child[1].text

        return d_entities

    def parse_events(self, events):
        """
        Parse each entity to create a dictionary
        """
        d_events = {}
        for child in events:
            d_events[child[0].text] = {}
            for c in child:
                d_events[child[0].text][c.tag] = c.text

        return d_events

    def parse_collections(self, collections):
        """
        Parse each entity to create a dictionary
        """
        d_collections = {}
        for child in collections:
            d_collections[child[0].text] = {}
            for c in child:
                d_collections[child[0].text][c.tag] = c.text

        return d_collections

