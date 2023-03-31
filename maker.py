from os import listdir
import re
import argparse
from configparser import ConfigParser
import math
import xml.etree.ElementTree as ElementTree

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DEBUG = False
DEFAULT_COLORS_FOLDER = "resources/color-palettes/"
DEFAULT_FONT = "resources/DF-Curses-8x12.ttf"
DEFAULT_MAPS_PATH = "maps/"
DEFAULT_OUTPUT_PATH = "output/"
DESCRIPTION = 'Automated map maker from Dwarf Fortress maps'


entity_colors = [
    (255, 179, 0),
    (128, 62, 117),
    (255, 104, 0),
    (166, 189, 215),
    (193, 0, 32),
    (206, 162, 98),
    (129, 112, 102),
    (0, 125, 52),
    (246, 118, 142),
    (0, 83, 138),
    (255, 122, 92),
    (83, 55, 122),
    (255, 142, 0),
    (179, 40, 81),
    (244, 200, 0),
    (127, 24, 13),
    (147, 170, 0),
    (89, 51, 21),
    (241, 58, 19),
    (35, 44, 22)
]

mandatory_cities = []

sea_level_color = (44, 64, 75)
topology_color = (57, 62, 71)  # The topology lines
ag_color = (64, 85, 64)
path_color = (64, 64, 64)

glac_alpha = 0.7
desert_alpha = 1
veg_green = .8
veg_alpha = 1
terr_alpha = 0.3
vill_alpha = 0.3
ag_alpha = 0.1
glow_alpha = 0.7
topology_alpha = 0.5

big_point = 3
med_point = 2
small_point = 1
label_pcolor = (0, 0, 0)
point_pcolor = (64, 64, 64)

title_size = 300
subtitle_size = 100
font_size = 20
sub_size = 14
title_font = ImageFont.truetype(DEFAULT_FONT, title_size)
subtitle_font = ImageFont.truetype(DEFAULT_FONT, subtitle_size)
font = ImageFont.truetype(DEFAULT_FONT, font_size)
subfont = ImageFont.truetype(DEFAULT_FONT, sub_size)

text_offset = (10, 5)
title_adjust = (20, 10)
title_align = "tm"

label_color = (255, 255, 255)
blur_color = (0, 0, 0, 255)

mandatory_pop = 1000
min_cities = 5
mandatory_cities = [x.lower() for x in mandatory_cities]

ice_bgr = [255, 255, 255]
desert_bgr = [175, 201, 237]

brook = False
process_road = True
grid_draw = False
site_check = True
territory_check = False
structure_check = False
other_labels_check = False
world_label_check = False
veg_type = "Green"


def test_image(img):
    """
    TODO: add a description for this function
    """
    img = Image.fromarray(img[:, :, ::-1])
    img = img.convert("RGBA")
    img.show()
    cv.waitKey(0)


def blue_conversion(img):
    """
    TODO: add a description for this function
    """
    idx = img[:, :, 2] == 0
    grey_value = img[idx, 0] * .73
    img[idx, 0] = grey_value
    img[idx, 1] = grey_value
    img[idx, 2] = grey_value
    return img


def read_colors(folder=DEFAULT_COLORS_FOLDER):
    """
    Read the colors from a folder
    """
    palette_dict = {}
    color_palettes = listdir(folder)
    for c in color_palettes:
        color_config = ConfigParser()
        color_config.read(folder + c)
        color_values = {}
        for k, v in dict(color_config["COLORS"]).items():
            value = tuple(int(v.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
            color_values.update({int(k): value})
        palette_dict[color_config["META"]["name"]] = color_values
    return palette_dict


def scan_folder(folder_path):
    """
    Receives a folder path to scan and parse the files inside
    """

    if folder_path[-1] != "/":
        folder_path += "/"

    files = listdir(folder_path)

    maps = {}
    legends = None
    pops = None
    world_history = None

    for file in files:
        if ".bmp" in file:
            m = re.search(r"([^-]*)\.bmp", file)
            if m:
                maps[m.group(1)] = folder_path + file
        elif "legends.xml" in file:
            legends = folder_path + file
        elif "pops.txt" in file:
            pops = folder_path + file
        elif "world_history.txt" in file:
            world_history = folder_path + file

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


def parse_regions(regions):
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


def parse_sites(sites):
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


def parse_entities(entities):
    """
    Parse each entity to create a dictionary
    """
    d_entities = {}
    for child in entities:
        if len(child) > 1:
            d_entities[child[0].text] = child[1].text

    return d_entities


def parse_events(events):
    """
    Parse each entity to create a dictionary
    """
    d_events = {}
    for child in events:
        d_events[child[0].text] = {}
        for c in child:
            d_events[child[0].text][c.tag] = c.text

    return d_events


def parse_collections(collections):
    """
    Parse each entity to create a dictionary
    """
    d_collections = {}
    for child in collections:
        d_collections[child[0].text] = {}
        for c in child:
            d_collections[child[0].text][c.tag] = c.text

    return d_collections


def generate_parameters(folder):
    """
    Function to parse legends and generate parameters
    """
    print("Beginning parsing of " + folder)
    folder_path = DEFAULT_MAPS_PATH + folder

    print("Parsing files...")
    try:
        maps, legends, pops, world_history = scan_folder(folder_path)
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

    d_regions = parse_regions(regions)
    d_sites = parse_sites(sites)
    d_entities = parse_entities(entities)
    d_event = parse_events(events)
    d_coll = parse_collections(collections)

    print("Parsing history...")
    with open(world_history, 'r', encoding='cp850', errors='ignore') as file:
        world_translated_name = file.readline().strip()
        world_name = file.readline().strip()

    if site_check:
        print("Parsing pops...")
        civ_id = None  # will use the civ id as a flag
        with open(pops, 'r', encoding='cp850', errors='ignore') as file:
            for line in file:
                site = civ = parent = pop = None
                site = re.match(r'(\d+): ([^,]+), "([^,]+)", ([^,\n]+)', line)
                civ = re.match(r'(?:\t)Owner: ([^,]+), (\w+)', line)
                parent = re.match(r'(?:\t)Parent Civ: ([^,]+), (\w+)', line)
                pop = re.match(
                    r'(?:\t)(\d+) (goblin.*|kobold.*|dwar(?:f|ves).*|human.*|el(?:f|ves).*)',
                    line
                )
                if site:
                    civ_id = site.group(1)
                    d_sites[civ_id]["trans"] = site.group(2)
                elif civ and civ_id:
                    d_sites[civ_id]["ruler"] = list(
                        d_entities.keys()
                    )[list(d_entities.values()).index(civ.group(1).lower())]
                    d_sites[civ_id]["civ_name"] = civ.group(1)
                    d_sites[civ_id]["civ_race"] = civ.group(2)
                elif parent and civ_id:
                    d_sites[civ_id]["ruler"] = list(
                        d_entities.keys()
                    )[list(d_entities.values()).index(parent.group(1).lower())]
                    d_sites[civ_id]["parent_name"] = parent.group(1)
                    d_sites[civ_id]["parent_race"] = parent.group(2)
                elif pop and civ_id:
                    d_sites[civ_id]["pop"] += int(pop.group(1))
                elif "Outdoor" in line:
                    break

        for c in d_sites:
            if "pop" in d_sites[c] and d_sites[c]["pop"] > mandatory_pop:
                mandatory_cities.append(d_sites[c]["name"])
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
            if entities[e] > min_cities:
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
        "occ_sites": occ_sites,
        "entities": entities,
        "active_wars": active_wars
    }

    return parameters


def draw_base(elevation_file, color):
    """
    Draw the elevation
    """
    print("Drawing elevation...")
    elevation = cv.imread(elevation_file, cv.IMREAD_COLOR)
    elevation = blue_conversion(elevation)
    grey = np.uint8(cv.cvtColor(elevation, cv.COLOR_BGR2GRAY))

    canv = np.ones(grey.shape, np.uint8)
    canv = cv.merge([canv * color[0][2], canv * color[0][1], canv * color[0][0]])

    t = []
    kernel = np.ones((3, 3), 'uint8')
    for i in range(256):
        ret, thresh = cv.threshold(grey, i, 255, cv.THRESH_BINARY)
        thresh = cv.erode(thresh, kernel, iterations=1)
        thresh = cv.dilate(thresh, kernel, iterations=1)
        t.append(thresh)

        if i in color.keys():
            col = color[i]
            canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(thresh))
            cols = cv.merge([thresh / 255 * col[2], thresh / 255 * col[1], thresh / 255 * col[0]])
            canv = cv.add(canv, np.uint8(cols))

    ground = t[73]

    print("Drawing topology...")
    bathy_color = (color[0][2] * 0.9, color[0][1] * 0.9, color[0][0] * 0.9)
    for i, x in color.items():
        if i == 0:
            continue
        contours, hierarchy = cv.findContours(t[i], cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        if i < 73:
            col = bathy_color
        elif i == 73:
            col = sea_level_color
            cv.drawContours(canv, contours, -1, col, 1)
        elif i < 123:
            col = topology_color
            cv.drawContours(canv, contours, -1, col, 1)
        elif i >= 123:
            col = topology_color
            cv.drawContours(canv, contours, -1, col, 1)

    return canv, ground, kernel


def draw_vegetation(vegetation_file, canv):
    print("Drawing vegetation...")
    veg = cv.imread(vegetation_file, cv.IMREAD_GRAYSCALE)
    ret, veg_mask = cv.threshold(veg, 1, 255, cv.THRESH_BINARY)

    if veg_type == "Green":
        veg_overlay = cv.merge(
            [
                np.uint8(
                    (-0.4549 * veg) + 116
                ),
                np.uint8(
                    (-0.3804 * veg) + 172
                ),
                np.uint8(
                    (-0.6118 * veg) + 156
                )
            ]
        )
        veg_overlay = cv.bitwise_and(veg_overlay, veg_overlay, mask=veg)
    else:
        veg_overlay = cv.merge(
            [np.uint8(veg * (1 - veg_green)), np.uint8(veg * veg_green), np.uint8(veg * (1 - veg_green))])
    # veg_overlay = cv.blur(veg_overlay,(3,3))
    veg_top = cv.bitwise_and(canv, canv, mask=veg)
    veg_top = cv.addWeighted(veg_top, 1 - veg_alpha, veg_overlay, veg_alpha, 0)

    canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(veg_mask))
    canv = cv.add(canv, veg_top)

    return canv


def draw_biomes(biomes_file, canv):
    print("Drawing deserts...")
    biome = cv.imread(biomes_file, cv.IMREAD_COLOR)
    desert = np.zeros(biome.shape, dtype="uint8")
    desert[np.where((biome == [32, 96, 255]).all(axis=2))] = [108, 107, 94]  # Badland desert
    desert[np.where((biome == [0, 255, 255]).all(axis=2))] = [82, 142, 206]  # Sand desert
    desert[np.where((biome == [64, 128, 255]).all(axis=2))] = [108, 107, 94]  # Rock desert

    dmask = np.uint8(cv.cvtColor(desert, cv.COLOR_BGR2GRAY))
    dmask[np.where(dmask != 0)] = 255
    desert_top = cv.bitwise_and(canv, canv, mask=dmask)
    desert_top = cv.addWeighted(desert_top, 1 - desert_alpha, desert, desert_alpha, 0)

    canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(dmask))
    canv = cv.add(canv, desert_top)

    print("Drawing glaciers...")
    glacier = np.zeros(biome.shape, dtype="uint8")
    glacier[np.where((biome == [255, 255, 0]).all(axis=2))] = [255, 255, 255]
    glacier[np.where((biome == [255, 255, 64]).all(axis=2))] = [255, 255, 255]
    glacier[np.where((biome == [255, 255, 128]).all(axis=2))] = [255, 255, 255]
    # glacier = cv.dilate(glacier, kernel, iterations=1)
    # [247,253,254]

    gmask = np.uint8(cv.cvtColor(glacier, cv.COLOR_BGR2GRAY))
    glac_top = cv.bitwise_and(canv, canv, mask=gmask)
    glac_top = cv.addWeighted(glac_top, 1 - glac_alpha, glacier, glac_alpha, 0)

    canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(gmask))
    canv = cv.add(canv, glac_top)

    return canv


def draw_water(water_file, vegetation_file, color, canv):
    print("Drawing water...")
    water = cv.imread(water_file, cv.IMREAD_COLOR)
    veg = cv.imread(vegetation_file, cv.IMREAD_GRAYSCALE)

    rivers = np.zeros(veg.shape, dtype="uint8")
    rivers[np.where((water == [255, 96, 0]).all(axis=2))] = [255]  # lake
    rivers[np.where((water == [255, 112, 0]).all(axis=2))] = [255]  # ocean river
    rivers[np.where((water == [255, 128, 0]).all(axis=2))] = [255]  # major river
    rivers[np.where((water == [255, 160, 0]).all(axis=2))] = [255]  # river
    rivers[np.where((water == [255, 192, 0]).all(axis=2))] = [255]  # minor river
    rivers[np.where((water == [255, 224, 0]).all(axis=2))] = [255]  # stream
    if brook:
        rivers[np.where((water == [255, 255, 0]).all(axis=2))] = [255]  # brook

    ret, riv_mask = cv.threshold(rivers, 1, 255, cv.THRESH_BINARY)
    canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(riv_mask))

    col = color[72]
    rivers = cv.merge([riv_mask / 255 * col[2], riv_mask / 255 * col[1], riv_mask / 255 * col[0]])
    canv = cv.add(np.uint8(canv), np.uint8(rivers))
    return canv


def draw_territory(parameters, canv, ground, kernel):
    maps = parameters.get("maps")
    world_translated_name = parameters.get("world_translated_name")
    world_name = parameters.get("world_name")
    d_sites = parameters.get("d_sites")
    occ_sites = parameters.get("occ_sites")
    entities = parameters.get("entities")
    active_wars = parameters.get("active_wars")

    veg = cv.imread(maps["veg"], cv.IMREAD_GRAYSCALE)
    (maxx, maxy) = veg.shape
    print("Drawing territories...")
    i = 0
    k = cv.getStructuringElement(cv.MORPH_ELLIPSE, (15, 15))

    # VORONOI TERRITORY 2 ELECTRIC BOOGALGOO
    elevation = cv.imread(maps["el"], cv.IMREAD_COLOR)
    elevation = blue_conversion(elevation)
    delauny = np.zeros(elevation.shape, dtype="uint8")
    pts = []
    rulers = []

    for s in occ_sites:  # d_sites:
        if "ruler" in occ_sites[s] and int(occ_sites[s]["ruler"]) >= 0 and occ_sites[s]["ruler"] in entities:
            ((x1, y1), (x2, y2)) = d_sites[s]["rect"]
            x = int((int(x1) + int(x2)) / 2)
            y = int((int(y1) + int(y2)) / 2)
            pts.append((x, y))
            rulers.append(int(d_sites[s]["ruler"]))
            cv.circle(delauny, (x, y), 2, (255, 255, 255), -1)

    russet = sorted(set(rulers))
    i = 0
    for s in russet:
        rulers = [i if s == x else x for x in rulers]
        i = i + 1

    rect = (0, 0, maxy, maxx)
    subdiv = cv.Subdiv2D(rect)
    for p in pts:
        subdiv.insert(p)

    def draw_voronoi(img, subdiv):
        (facets, centers) = subdiv.getVoronoiFacetList([])
        for i in range(0, len(facets)):
            ifacet_arr = []
            for f in facets[i]:
                ifacet_arr.append(f)

            ifacet = np.array(ifacet_arr, np.intc)
            color = (rulers[i], rulers[i], rulers[i])

            cv.fillConvexPoly(img, ifacet, color, cv.LINE_4, 0)

    draw_voronoi(delauny, subdiv)

    facets = []
    for i in range(0, max(rulers) + 1):
        vp = np.zeros(veg.shape, dtype="uint8")
        vp[np.where((delauny == [i, i, i]).all(axis=2))] = [255]  # entity_colors[i]
        facets.append(vp)

    i = 0
    terrs = []
    disp = []
    for e in entities:
        terr = np.zeros(veg.shape, dtype="uint8")
        occ_pts = []
        for s in occ_sites:
            if occ_sites[s]["ruler"] == e:
                #            xy = occ_sites[s]["pos"]
                #            x = int(xy[0])*16
                #            y = int(xy[1])*16
                ((x1, y1), (x2, y2)) = occ_sites[s]["rect"]
                x = int((int(x1) + int(x2)) / 2)
                y = int((int(y1) + int(y2)) / 2)
                occ_pts = (x, y)
                # cv.rectangle(terr,(int(x),int(y)),(int(x+16),int(y+16)),(255),-1)
                cv.circle(terr, (x, y), 8, 255, -1)

                rect = occ_sites[s]["rect"]
        terr = cv.dilate(terr, k, iterations=10)
        terr = cv.erode(terr, k, iterations=6)

        n = 0
        ii = -1
        #    for q in range(len(facets)):
        #        m = cv.countNonZero(cv.bitwise_and(facets[q    ],terr))
        #        if m > n:
        #            n = m
        #            ii = q
        if not occ_pts:
            continue

        for q in range(len(facets)):
            if facets[q][occ_pts[1]][occ_pts[0]]:
                ii = q
                break
        # ii is the biggest voronoi cell(s)
        #    print(ii,n)

        disp.append(terr)
        terr = cv.bitwise_and(terr, terr, mask=facets[ii])
        terrs.append(terr)

    for i, terr in enumerate(terrs):
        c1 = int(list(entities)[i])

        for j, uerr in enumerate(disp):
            c2 = int(list(entities)[j])
            if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                terr = cv.subtract(terr, uerr)

        terr = cv.bitwise_and(terr, terr, mask=ground)
        terr_top = cv.bitwise_and(canv, canv, mask=terr)
        if i >= len(entity_colors):
            print("Error: Not enough colors in entity_colors")
            i = i % len(entity_colors)
        terr_overlay = np.ones(elevation.shape, dtype="uint8") * [entity_colors[i][2], entity_colors[i][1],
                                                                  entity_colors[i][0]]
        terr_overlay = cv.bitwise_and(terr_overlay, terr_overlay, mask=terr).astype(np.uint8)

        terr_top = cv.addWeighted(terr_top, 1 - terr_alpha, terr_overlay, terr_alpha, 0)

        canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(terr))
        canv = cv.add(canv, terr_top)
    #    i = i + 1
    #################################################################################
    diag_width = 1
    diag_space = 0

    outerlay = np.zeros(elevation.shape, dtype="uint8")
    outermask = np.zeros(veg.shape, dtype="uint8")
    for i, terr in enumerate(terrs):
        c1 = int(list(entities)[i])

        diag = np.zeros(veg.shape, dtype="uint8")
        for d in range(0, 2 * maxx, len(disp) * (diag_width + diag_space)):
            cv.line(diag, (maxy, d - maxx + i * (diag_width + diag_space)), (0, d + i * (diag_width + diag_space)),
                    (255), diag_width)

        for j, uerr in enumerate(disp):
            c2 = int(list(entities)[j])
            m = 0
            if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                inter = cv.bitwise_and(disp[i], disp[j])
                m = cv.countNonZero(inter)
            if m > 0:
                if i >= len(entity_colors):
                    i = i % len(entity_colors)
                overlay = np.ones(elevation.shape, dtype="uint8") * [entity_colors[i][2], entity_colors[i][1],
                                                                     entity_colors[i][0]]
                mask = cv.bitwise_and(inter, diag)
                overlay = cv.bitwise_and(overlay, overlay, mask=mask).astype(np.uint8)

                eiag = np.zeros(veg.shape, dtype="uint8")
                for d in range(0, 2 * maxx, len(terrs) * (diag_width + diag_space)):
                    cv.line(eiag, (maxy, d - maxx + j * (diag_width + diag_space)),
                            (0, d + j * (diag_width + diag_space)), (255), diag_width)

                if j >= len(entity_colors):
                    j = j % len(entity_colors)

                everlay = np.ones(elevation.shape, dtype="uint8") * [entity_colors[j][2], entity_colors[j][1],
                                                                     entity_colors[j][0]]
                emask = cv.bitwise_and(inter, eiag)
                everlay = cv.bitwise_and(everlay, everlay, mask=emask).astype(np.uint8)

                fmask = cv.add(mask, emask)

                overlay = cv.add(overlay, everlay)

                templay = cv.bitwise_and(overlay, overlay, mask=cv.bitwise_not(outermask))
                outerlay = cv.add(outerlay, templay)
                outermask = cv.add(outermask, fmask)

    outermask = cv.bitwise_and(outermask, outermask, mask=ground)
    outerlay = cv.bitwise_and(outerlay, outerlay, mask=outermask)
    canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(outermask))
    canv = cv.add(canv, outerlay)

    # BORDERS
    for i, terr in enumerate(terrs):
        edges = cv.Canny(terr, 0, 0)
        edges = cv.dilate(edges, kernel, iterations=1)
        edges = cv.erode(edges, kernel, iterations=1)
        # cv.imshow("d",edges)
        # cv.waitKey(0)
        c1 = int(list(entities)[i])
        for j, uerr in enumerate(disp):
            c2 = int(list(entities)[j])
            if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                edges = cv.subtract(edges, uerr)

        edges = cv.bitwise_and(edges, edges, mask=ground)

        if i >= len(entity_colors):
            i = i % len(entity_colors)

        overlay = np.ones(elevation.shape, dtype="uint8") * [entity_colors[i][2], entity_colors[i][1],
                                                             entity_colors[i][0]]
        overlay = cv.bitwise_and(overlay, overlay, mask=edges).astype(np.uint8)
        canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(edges))
        canv = cv.add(canv, overlay)

    return canv


def generate_map(parameters, color_name):
    """
    Function to generate maps
    """

    maps = parameters.get("maps")
    world_translated_name = parameters.get("world_translated_name")
    world_name = parameters.get("world_name")
    d_sites = parameters.get("d_sites")
    occ_sites = parameters.get("occ_sites")
    entities = parameters.get("entities")
    active_wars = parameters.get("active_wars")

    # OpenCV
    color = palette_dict[color_name]
    veg = cv.imread(maps["veg"], cv.IMREAD_GRAYSCALE)
    (maxx, maxy) = veg.shape

    print(f"Beginning {color_name} map generation")

    canv, ground, kernel = draw_base(maps["el"], color)
    canv = draw_vegetation(maps["veg"], canv)
    canv = draw_biomes(maps["bm"], canv)
    canv = draw_water(maps["hyd"], maps["veg"], color, canv)

    if territory_check:
        canv = draw_territory(parameters, canv, ground, kernel)

    if structure_check:
        print("Drawing structures...")
        struct = cv.imread(maps["str"], cv.IMREAD_COLOR)
        castle = np.zeros(veg.shape, dtype="uint8")
        village = np.zeros(veg.shape, dtype="uint8")
        tunnel = np.zeros(veg.shape, dtype="uint8")
        sbridge = np.zeros(veg.shape, dtype="uint8")
        sroad = np.zeros(veg.shape, dtype="uint8")
        swall = np.zeros(veg.shape, dtype="uint8")
        bridge = np.zeros(veg.shape, dtype="uint8")
        road = np.zeros(veg.shape, dtype="uint8")
        wall = np.zeros(veg.shape, dtype="uint8")
        crop1 = np.zeros(veg.shape, dtype="uint8")
        crop2 = np.zeros(veg.shape, dtype="uint8")
        crop3 = np.zeros(veg.shape, dtype="uint8")
        pasture = np.zeros(veg.shape, dtype="uint8")
        meadow = np.zeros(veg.shape, dtype="uint8")
        woodland = np.zeros(veg.shape, dtype="uint8")
        orchard = np.zeros(veg.shape, dtype="uint8")

        castle[np.where((struct == [128, 128, 128]).all(axis=2))] = [255]  # castle
        village[np.where((struct == [255, 255, 255]).all(axis=2))] = [255]  # village
        tunnel[np.where((struct == [20, 20, 20]).all(axis=2))] = [255]  # tunnel
        sbridge[np.where((struct == [224, 224, 224]).all(axis=2))] = [255]  # stone bridge
        sroad[np.where((struct == [192, 192, 192]).all(axis=2))] = [255]  # stone road
        swall[np.where((struct == [96, 96, 96]).all(axis=2))] = [255]  # stone wall
        bridge[np.where((struct == [20, 167, 180]).all(axis=2))] = [255]  # other bridge
        road[np.where((struct == [20, 127, 150]).all(axis=2))] = [255]  # other road
        wall[np.where((struct == [20, 127, 160]).all(axis=2))] = [255]  # other wall

        crop1[np.where((struct == [0, 128, 255]).all(axis=2))] = [255]  # crops (all crops are humans)
        crop2[np.where((struct == [0, 160, 255]).all(axis=2))] = [255]  # crops
        crop3[np.where((struct == [0, 192, 255]).all(axis=2))] = [255]  # crops
        pasture[np.where((struct == [0, 255, 0]).all(axis=2))] = [255]  # pasture (dwarves mostly, some human)
        meadow[np.where((struct == [0, 255, 64]).all(axis=2))] = [255]  # meadow
        woodland[np.where((struct == [0, 128, 0]).all(axis=2))] = [255]  # woodland
        orchard[np.where((struct == [0, 160, 0]).all(axis=2))] = [255]  # orchard (elves)

        # print("Drawing villages...")
        # village = cv.dilate(village, kernel, iterations=2)
        # village = cv.erode(village, kernel, iterations=1)
        # vill_overlay = cv.merge([np.uint8(village/255*vill_color[2]),np.uint8(village/255*vill_color[1]),np.uint8(village/255*vill_color[0])])
        # vill_top = cv.bitwise_and(canv,canv,mask=village)
        # vill_top = cv.addWeighted(vill_top,1-vill_alpha,vill_overlay,vill_alpha,0)
        # canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(village))
        # canv = cv.add(canv,vill_top)

        print("Drawing crops...")
        crops = cv.add(crop1, crop2)
        crops = cv.add(crops, crop3)
        plain = cv.add(pasture, meadow)
        woods = cv.add(woodland, orchard)
        ag = cv.add(crops, plain)
        ag = cv.add(ag, woods)

        ag_overlay = cv.merge(
            [np.uint8(ag / 255 * ag_color[2]), np.uint8(ag / 255 * ag_color[1]), np.uint8(ag / 255 * ag_color[0])])
        ag_top = cv.bitwise_and(canv, canv, mask=ag)
        ag_top = cv.addWeighted(ag_top, 1 - ag_alpha, ag_overlay, ag_alpha, 0)
        canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(ag))
        canv = cv.add(canv, ag_top)

        # convil, hierarchy = cv.findContours(village, 1, 2)

        # for c in convil:
        #    M = cv.moments(c)
        #    if M["m00"] == 0:
        #        print(M)
        #        continue
        #    cX = int(M["m10"] / M["m00"])
        #    cY = int(M["m01"] / M["m00"])
        #    radius = math.sqrt(cv.contourArea(c))/2

        #    if radius < 5:
        #        print(radius)
        #        cv.circle(canv, (cX, cY), math.ceil(radius), (0,0,0), -1)

        # CASTLES
        # print("Drawing castles...")
        # castle = cv.dilate(castle, kernel, iterations=1)
        # castle = cv.erode(castle, kernel, iterations=1)
        # concast, hierarchy = cv.findContours(castle, 1, 2)
        # for c in concast:
        #    M = cv.moments(c)
        #    if M["m00"] == 0:
        #        continue
        #    cX = int(M["m10"] / M["m00"])
        #    cY = int(M["m01"] / M["m00"])
        #    radius = math.sqrt(cv.contourArea(c))/2
        # print(radius)
        #    cv.circle(canv, (cX, cY), math.floor(radius), (0,0,0), -1)

        print("Drawing roads...")
        roads = cv.add(road, sroad)
        bridges = cv.add(bridge, sbridge)

        path = cv.add(roads, bridges)
        path = cv.add(path, tunnel)

        pts = []
        for s in d_sites:
            ((x1, y1), (x2, y2)) = d_sites[s]["rect"]
            x = int((int(x1) + int(x2)) / 2)
            y = int((int(y1) + int(y2)) / 2)
            pts.append((x, y))
            # cv.circle(path,(x,y), 1, (255), -1)

        # corners = cv.goodFeaturesToTrack(path, 200, 0.05, 16)
        # hole = []
        # for i in range(0,len(corners)):
        #    for j in range(i+1,len(corners)):
        #        x1,y1 = corners[i].ravel()
        #        x2,y2 = corners[j].ravel()
        #        w = 16
        #        if abs(x1-x2)<=w and abs(y1-y2)<=w:
        #            hole.append((x1,y1,x2,y2))
        #            cv.circle(path,(int(x1),int(y1)), 3, (255), -1)
        # for h in hole:
        #    (x1,y1,x2,y2) = h
        #    cv.line(path,(int(x1),int(y1)),(int(x2),int(y2)),(255),1)

        # cv.imshow("p",path)

        print("Merging roads...")

        cnt, hierarchy = cv.findContours(path, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        clen = len(cnt)
        clon = -1
        if process_road == False:
            clon = clen
        for it in range(math.ceil(math.sqrt(clen))):
            holes = []
            cnt, hierarchy = cv.findContours(path, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            clen = len(cnt)
            if clon == clen:
                print("Roads done.")
                break
            clon = clen
            print(it, ":", clen, "contours")
            for i in range(len(cnt)):
                area = cv.contourArea(cnt[i])
                dist = 99
                for j in range(i + 1, len(cnt)):
                    for pi in cnt[i]:
                        for pj in cnt[j]:
                            x1, y1 = pi.ravel()
                            x2, y2 = pj.ravel()
                            d = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                            if d < dist:
                                dist = d
                                a = (x1, y1)
                                b = (x2, y2)
                if dist < 32:
                    holes.append((a, b))
            for h in holes:
                cv.line(path, h[0], h[1], (255), 1)
        #    cv.imshow("l",path)
        #    cv.waitKey(1)

        '''
        print("Drawing offramps...")
        close = []
        for p in pts:
            it = -1
            dist = 16
            for i in range(0,len(cnt)):
                d = -cv.pointPolygonTest(cnt[i],p,True)
                if d < dist:
                    dist = d
                    it = i
            if dist < 16:
                close.append([p,it])
        
        for (p,i) in close:
            dist = 16
            eist = 16
            a = -1
            b = -1
            e = -1
            d = -1
            for c in cnt[i]:
                x1,y1 = c[0]
                x2,y2 = p
                d = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                if d < dist:
                    eist = d
                    e = a
        
                    dist = d
                    a = (x1,y1)
                    b = (x2,y2)
                elif d < eist:
                    eist = d
                    e = (x1,y1)
            if -1 in [a,b,e] or eist > 8:
                continue
        
            line = np.zeros(veg.shape, dtype="uint8")
            #dx = b[0]-a[0]
            #dy = b[1]-a[1]
            #cv.line(line,a,(a[0]+2*dx,a[1]+2*dy),(127),1)
            cv.line(line,a,e,(127),1)
            sect = cv.countNonZero(cv.bitwise_and(ag,line))
            if sect > 5:
                print(p,dist,eist,sect,a,b,e)
                cv.circle(path,b, 1, (256), -1)
                cv.imshow("E",cv.add(path,line))
                cv.waitKey(0)
        
                cv.line(path,a,b,(256),1)
                cv.line(path,b,e,(256),1)
        '''

        # for p in pts:
        #    cv.circle(path,p, 1, (127), -1)

        # cv.imshow("d",path)
        # cv.waitKey(0)

        path_overlay = cv.merge([np.uint8(path / 255 * path_color[2]), np.uint8(path / 255 * path_color[1]),
                                 np.uint8(path / 255 * path_color[0])])
        canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(path))
        canv = cv.add(canv, path_overlay)

    if grid_draw:
        print("Drawing grid...")
        size = len(canv)
        grid_spacing = 43
        grid_width = 1
        grid_color = [200, 200, 200]
        grid_offset = 5
        grid_alpha = .7
        for i in range(grid_offset, grid_width + grid_offset):
            canv[i:size:grid_spacing, :] = grid_color
            canv[:, i:size:grid_spacing] = grid_color

    # grid_top = cv.addWeighted(glac_top,1-grid_alpha,glacier,grid_alpha,0)

    print("Drawing labels...")
    bigprint = ["tower", "dark fortress", "castle", ]
    medprint = ["town", "fort", "monastery", "tomb", "fortress", "labyrinth", "mountain halls"]
    smallprint = ["dark pits", "hillocks", "hamlet", "forest retreat"]
    noprint = ["camp", "cave", "lair", "vault", "shrine"]
    typeprint = ["tower", "dark fortress", "fortress", "castle"]

    marquee = []
    im = Image.fromarray(canv[:, :, ::-1])
    im = im.convert("RGBA")
    overlap = np.zeros(veg.shape, dtype="uint8")

    if other_labels_check:
        ###############################
        for s in d_sites:
            if d_sites[s]["name"] in mandatory_cities:
                marquee.append(s)

        for s in d_sites:
            if (d_sites[s]["type"] in bigprint + medprint + smallprint or d_sites[s]["name"] in mandatory_cities):
                ((x1, y1), (x2, y2)) = d_sites[s]["rect"]
                x = int((int(x1) + int(x2)) / 2)
                y = int((int(y1) + int(y2)) / 2)

                if d_sites[s]["type"] in bigprint:
                    size = big_point
                elif d_sites[s]["type"] in medprint:
                    size = med_point
                else:
                    size = small_point

                if d_sites[s]["type"] in typeprint or d_sites[s]["name"] in mandatory_cities:
                    col = label_pcolor
                else:
                    col = point_pcolor

                if d_sites[s]["type"] in typeprint and s not in marquee:
                    marquee.append(s)

                cv.circle(canv, (x, y), size, col, -1)

            #        print(x,y,d_sites[s]["rect"])
            elif d_sites[s]["type"] in noprint:
                continue
            else:
                print(d_sites[s]["type"])

        for s in marquee:
            back = Image.new("RGBA", (maxx, maxy))
            draw = ImageDraw.Draw(back)

            ((x1, y1), (x2, y2)) = d_sites[s]["rect"]
            x = int((int(x1) + int(x2)) / 2)
            y = int((int(y1) + int(y2)) / 2)

            subtext = ""
            if "trans" in d_sites[s]:
                if d_sites[s]["trans"][0].isascii():
                    text = d_sites[s]["trans"].title()
                else:
                    text = d_sites[s]["trans"]
                subtext = d_sites[s]["name"].title()
            else:
                text = d_sites[s]["name"].title()

            bbox = draw.textbbox((0, 0), text, font)
            textsize = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            bbox2 = draw.textbbox((0, 0), subtext, subfont)
            textsize2 = (bbox2[2] - bbox2[0], bbox2[3] - bbox2[1])

            testlap = np.zeros(veg.shape, dtype="uint8")
            if x < maxx - textsize[0] - text_offset[0]:
                anchor = "lm"
                cv.rectangle(testlap, (x + text_offset[0], int(y + textsize[1] / 2 + textsize2[1])),
                             (x + text_offset[0] + textsize[0], int(y - textsize[1] / 2)), (255), -1)
            else:
                print(d_sites[s]["name"], "reversed.")
                anchor = "rm"
                cv.rectangle(testlap, (x - textsize[0] - text_offset[0], int(y + textsize[1] / 2 + textsize2[1])),
                             (x - text_offset[0], int(y - textsize[1] / 2)), (255), -1)

            if cv.countNonZero(cv.bitwise_and(testlap, overlap)) > 0:
                print(d_sites[s]["name"], "label clash")
                continue

            # Shadows
            overlap = cv.add(testlap, overlap)
            if anchor == "lm":
                draw.text((x + text_offset[0], y), text, font=font, anchor=anchor, fill=(0, 0, 0, 255))
                draw.text((x + text_offset[0] + textsize[0] / 2, y + textsize[1] / 2), subtext, font=subfont,
                          anchor="ma", fill=blur_color)
            else:
                draw.text((x - text_offset[0], y), text, font=font, anchor=anchor, fill=(0, 0, 0, 255))
                draw.text((x - text_offset[0] - textsize[0] / 2, y + textsize[1] / 2), subtext, font=subfont,
                          anchor="ma", fill=blur_color)

            back = back.filter(ImageFilter.GaussianBlur(radius=3))
            back.alpha_composite(back)
            back.alpha_composite(back)

            # Text
            draw = ImageDraw.Draw(back)
            if anchor == "lm":
                draw.text((x + text_offset[0], y), text, font=font, anchor=anchor, color=label_color)
                draw.text((x + text_offset[0] + textsize[0] / 2, y + textsize[1] / 2), subtext, font=subfont,
                          color=label_color, anchor="ma")
            else:
                draw.text((x - text_offset[0], y), text, font=font, anchor=anchor)
                draw.text((x - text_offset[0] - textsize[0] / 2, y + textsize[1] / 2), subtext, font=subfont,
                          color=label_color, anchor="ma")
            im.alpha_composite(back)

    back = Image.new("RGBA", (maxx, maxy))
    draw = ImageDraw.Draw(back)

    titlebox = draw.textbbox((0, 0), world_translated_name, title_font)
    titlesize = (titlebox[2] - titlebox[0], titlebox[3] - titlebox[1])
    subbox = draw.textbbox((0, 0), world_name, subtitle_font)
    subsize = (subbox[2] - subbox[0], subbox[3] - subbox[1])

    if title_align == "tm":
        anchor = "ma"
        (x, y) = (maxx / 2, 0 + title_adjust[1])
        (x1, y1) = (x, y + titlesize[1])
    if title_align == "tl":
        anchor = "la"
        (x, y) = (0 + title_adjust[0], 0 + title_adjust[1])
        (x1, y1) = (x + titlesize[0] / 2, y + titlesize[1])
    elif title_align == "tr":
        anchor = "ra"
        (x, y) = (maxx - title_adjust[0], 0 + title_adjust[1])
        (x1, y1) = (x - titlesize[0] / 2, y + titlesize[1])
    elif title_align == "bl":
        anchor = "ld"
        (x, y) = (0 + title_adjust[0], maxy - title_adjust[1] - subsize[1])
        (x1, y1) = (x + titlesize[0] / 2, y)
    elif title_align == "br":
        anchor = "rd"
        (x, y) = (maxx - title_adjust[0], maxy - title_adjust[1] - subsize[1])
        (x1, y1) = (x - titlesize[0] / 2, y)

    draw.text((x, y), world_translated_name, font=title_font, anchor=anchor, fill=(0, 0, 0, 255))
    draw.text((x1, y1), world_name, font=subtitle_font, anchor="ma", fill=blur_color)
    back = back.filter(ImageFilter.GaussianBlur(radius=3))
    back.alpha_composite(back)
    back.alpha_composite(back)

    draw = ImageDraw.Draw(back)
    draw.text((x, y), world_translated_name, font=title_font, anchor=anchor, color=label_color)
    draw.text((x1, y1), world_name, font=subtitle_font, anchor="ma", color=label_color)
    im.alpha_composite(back)

    im.show()
    print("Saving to file...")
    output_path = "output/"
    im.save(f"{output_path}{world_translated_name} - {color_name}.png")
    print("---------------------------")
    print(f"All maps generated for {world_translated_name}")
    print("---------------------------")

    return canv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='ARMap',
        description=DESCRIPTION,
    )

    parser.add_argument('-d', '--debug', action='store_true',
                        help='enable debug mode')
    parser.add_argument('-g', '--grid', action='store_true',
                        help='Draw grid')
    parser.add_argument('-c', '--colors', nargs='*', default='all',
                        help='list of color palettes, enter "all" if you want \
                          to use all palettes, default is all available')
    args = parser.parse_args()

    DEBUG = args.debug
    grid_draw = args.grid
    color_folder = DEFAULT_COLORS_FOLDER
    colors = args.colors

    folders = listdir(DEFAULT_MAPS_PATH)

    # TODO: confirm with Myckou what is the "complete" flow
    if "Complete" in folders:
        folders.remove("Complete")

    if not folders:
        print("No map data folders present.")

    palette_dict = read_colors(color_folder)
    if colors == "all":
        colors = list(palette_dict.keys())

    canvas = None
    for f in folders:
        parameters = generate_parameters(f)
        for color_name in colors:
            if color_name in palette_dict.keys():
                canvas = generate_map(parameters, color_name)
            else:
                print(f"{color_name} not found! Skipping color!")

    if DEBUG and canvas:
        cv.imshow("wat", canvas)
        cv.waitKey(0)

    print("Done!")
