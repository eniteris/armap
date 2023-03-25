import os
import re
import argparse
from configparser import ConfigParser
import math
import xml.etree.ElementTree as ET

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter


COLORS_FOLDER = "resources/color-palettes/"
DEBUG = False
DEFAULT_FONT = "resources/DF-Curses-8x12.ttf"
ROOT_PATH = "Map Data/"
DESCRIPTION='Automated map maker from Dwarf Fortress maps'


SETTINGS = {
    "min_cities": 5 
}

palette_dict =  {}
color_palettes = os.listdir(COLORS_FOLDER)
for c in color_palettes:
    color_config = ConfigParser()
    color_config.read(COLORS_FOLDER + c)
    color_values = dict(color_config["COLORS"])
    for k, v in color_values.items():
        value = tuple(int(v.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        color_values.update({k: value})
    palette_dict[color_config["META"]["name"]] = color_values


ent_colors = [
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

sea_level_color = (44,64,75)
topology_color = (57,62,71) #The topology lines
ag_color = (64,85,64)
path_color = (64,64,64)

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
label_pcolor = (0,0,0)
point_pcolor = (64,64,64)

title_size = 300
subtitle_size = 100
font_size = 20
sub_size = 14
titlefont = ImageFont.truetype(DEFAULT_FONT, title_size)
subtitlefont = ImageFont.truetype(DEFAULT_FONT, subtitle_size)
font = ImageFont.truetype(DEFAULT_FONT, font_size)
subfont = ImageFont.truetype(DEFAULT_FONT, sub_size)

text_offset = (10,5)
titleadjust = (20,10)
title_align = "tm"

label_color = (255,255,255)
blur_color = (0,0,0,255)

brook = False
process_road = True

mand_pop = 1000
mandatory_cities = [x.lower() for x in mandatory_cities]

ice_bgr = [255,255,255]
desert_bgr = [175,201,237]

grid_draw = False
site_check = False
territory_check = False
structure_check = False
other_labels_check = False
world_label_check = False
veg_type = "Green"


def test_image(img):
    """
    TODO: add a description for this funcion
    """
    img = Image.fromarray(img[:,:,::-1])
    img = img.convert("RGBA")
    img.show()
    cv.waitKey(0)


def blue_conversion(img):
    """
    TODO: add a description for this funcion
    """
    idx = img[:, :, 2] == 0
    grey_value = img[idx, 0] * .73
    img[idx, 0] = grey_value
    img[idx, 1] = grey_value
    img[idx, 2] = grey_value
    return img


def scan_folder(folder_path):
    """
    Receives a folder path to scan and parse the files inside
    """

    if folder_path[-1] != "/":
        folder_path += "/"

    files = os.listdir(folder_path)

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

    if maps:
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
    Parse each region to create a dictonary
    """
    d_regions = {}
    for child in regions:
        d_regions[child[0].text] = {
            "name":child[1].text,
            "type":child[2].text
        }

    return d_regions


def parse_sites(sites):
    """
    Parse each site to create a dictonary
    """
    d_sites = {}
    for child in sites:
        if len(child) > 1:
            rect = child[4].text.split(":")
            d_sites[child[0].text] = {
                "type":child[1].text,
                "name":child[2].text,
                "pos": child[3].text.split(","),
                "rect": list(x.split(",") for x in rect),
                "pop": 0,
                "ruler": -1
            }

    return d_sites


def parse_entities(entities):
    """
    Parse each entity to create a dictonary
    """
    d_entities = {}
    for child in entities:
        if len(child) > 1:
            d_entities[child[0].text] = child[1].text

    return d_entities


def parse_events(events):
    """
    Parse each entity to create a dictonary
    """
    d_events = {}
    for child in events:
        d_events[child[0].text] = {}
        for c in child:
            d_events[child[0].text][c.tag] = c.text

    return d_events


def parse_collections(collections):
    """
    Parse each entity to create a dictonary
    """
    d_collections = {}
    for child in collections:
        d_collections[child[0].text] = {}
        for c in child:
            d_collections[child[0].text][c.tag] = c.text

    return d_collections


def generate(folder):
    """
    General function to generate maps
    """

    print("Beginning generation of " + folder)
    folder_path = ROOT_PATH + folder

    print("Parsing files...")
    try:
        maps, legends, pops, world_history = scan_folder(folder_path)
    except Exception as e:
        print(e)
        return None

    print("Parsing XML...")
    tree = ET.parse(legends)

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
    with open(world_history,'r',encoding='cp850',errors='ignore') as file:
        worldtransname = file.readline().strip()
        worldname = file.readline().strip()

    if site_check:
        print("Parsing pops...")
        civ_id = None # will use the civ id as a flag
        with open(pops,'r',encoding='cp850',errors='ignore') as file:
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
                        )[list(d_entities.values()).index(civ.group(1))]
                    d_sites[civ_id]["ruler_name"] = civ.group(1)
                    d_sites[civ_id]["ruler_race"] = civ.group(2)
                elif parent and civ_id:
                    d_sites[civ_id]["parent_name"] = parent.group(1)
                    d_sites[civ_id]["parent_race"] = parent.group(2)
                elif pop and civ_id:
                    d_sites[civ_id]["pop"] += pop.group(1)
                elif "Outdoor" in line:
                    break

        for c in d_sites:
            if "pop" in d_sites[c] and d_sites[c]["pop"] > mand_pop:
                mandatory_cities.append(d_sites[c]["name"])
                print(d_sites[c]["name"].title(),"has a population of",d_sites[c]["pop"])

        print("Calculating owners...")
        event_types = ["destroyed site","hf destroyed site","new site leader","reclaim site","site taken over"]
        fevent = {}
        for e in d_event:
            t = d_event[e]["type"]
            if t in event_types:
                fevent[e] = d_event[e]

        # Count number of sites each civ has
        ents = {}
        occ_sites = {}
        for s in d_sites:
            x = d_sites[s]
            if "ruler" in x:
                if int(x["ruler"]) == -1:
                    continue
                occ_sites[s] = x
                if x["ruler"] in ents:
                    ents[x["ruler"]] += 1
                else:
                    ents[x["ruler"]] = 1
        
        # Filter civs with less than minimum cities
        nents = {}
        for e in ents:
            if ents[e] > SETTINGS.get("min_cities"):
                nents[e] = ents[e]
        ents = nents

        active_wars = {}
        for e in d_coll:
            if d_coll[e]["type"] == "war" and d_coll[e]["end_year"] == "-1":
                agressor = int(d_coll[e]["aggressor_ent_id"])
                defender = int(d_coll[e]["defender_ent_id"])  
                if agressor in active_wars:
                    active_wars[agressor].append(defender)
                else:
                    active_wars[defender].append(agressor)
        
        for key in active_wars:
            active_wars[key] = set(active_wars[key])

    color = palette_dict["extra"]
    bathy_color = (color[0][2]*0.9,color[0][1]*0.9,color[0][0]*0.9)
    print("Beginning extra map generation")
    yx = (1131,1524)
    print("Drawing elevation...")
    elevation = cv.imread(maps["el"],cv.IMREAD_COLOR)
    elevation = blue_conversion(elevation)
    
    grey = np.uint8(cv.cvtColor(elevation, cv.COLOR_BGR2GRAY))

    #print("Elevation ranges from",np.amin(grey),"to",np.amax(grey))
    canv = np.ones(grey.shape,np.uint8)       
    canv = cv.merge([canv*color[0][2],canv*color[0][1],canv*color[0][0]])
    
    t = []
    kernel = np.ones((3, 3), 'uint8')
    for i in range(256):
        ret,thresh = cv.threshold(grey, i, 255, cv.THRESH_BINARY)
        thresh = cv.erode(thresh, kernel, iterations=1)
        thresh = cv.dilate(thresh, kernel, iterations=1)
        t.append(thresh)
    
        if i in color.keys():
            col = color[i]
            canv = cv.bitwise_and(canv,canv,mask = cv.bitwise_not(thresh))
            cols = cv.merge([thresh/255*col[2],thresh/255*col[1],thresh/255*col[0]])
            canv = cv.add(canv, np.uint8(cols))
    
    print("Drawing topology...")
    for i,x in color.items():
        if i == 0: continue
        contours, hierarchy = cv.findContours(t[i], cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contour_canv = canv.copy()
        if i < 73: 
            col = bathy_color
        elif i == 73:
            col = sea_level_color
            cv.drawContours(canv, contours, -1, col, 1)
            #canv = cv.addWeighted(canv,1-topology_alpha,contour_canv,topology_alpha,0)
        elif i < 123:
            col = topology_color
            cv.drawContours(canv, contours, -1, col, 1)
            #canv = cv.addWeighted(canv,1-topology_alpha,contour_canv,topology_alpha,0)
        elif i >= 123:
            col = topology_color
            cv.drawContours(canv, contours, -1, col, 1)
            #canv = cv.addWeighted(canv,1-topology_alpha,contour_canv,topology_alpha,0)
        # cv.drawContours(canv, contours, -1, col, 1)
        #img2 = grey.copy() 
    
    
    print("Drawing vegetation...")
    veg = cv.imread(maps["veg"],cv.IMREAD_GRAYSCALE)
    ret,veg_mask = cv.threshold(veg,1,255,cv.THRESH_BINARY)
    
    if veg_type == "Green":
        veg_overlay = cv.merge(
            [
                np.uint8(
                    (-0.4549*veg)+116
                ),
                np.uint8(
                    (-0.3804*veg)+172
                ),
                np.uint8(
                    (-0.6118*veg)+156
                )
            ]
        )
        veg_overlay = cv.bitwise_and(veg_overlay,veg_overlay,mask=veg)
    else:
        veg_overlay = cv.merge([np.uint8(veg*(1-veg_green)),np.uint8(veg*veg_green),np.uint8(veg*(1-veg_green))])
    #veg_overlay = cv.blur(veg_overlay,(3,3))
    veg_top = cv.bitwise_and(canv,canv,mask=veg)
    veg_top = cv.addWeighted(veg_top,1-veg_alpha,veg_overlay,veg_alpha,0)
    
    #cv.imshow("veg",veg_overlay)
    #cv.waitKey(1)
    
    canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(veg_mask))
    canv = cv.add(canv,veg_top)
    
    (maxx,maxy) = veg.shape
    
    print("Drawing deserts...")
    biome = cv.imread(maps["bm"],cv.IMREAD_COLOR)
    desert = np.zeros(biome.shape, dtype="uint8")
    desert[np.where((biome==[32,96,255]).all(axis=2))] = [108,107,94]       #Badland desert
    desert[np.where((biome==[0,255,255]).all(axis=2))] = [82,142,206]       #Sand desert
    desert[np.where((biome==[64,128,255]).all(axis=2))] = [108,107,94]      #Rock desert
    
    dmask = np.uint8(cv.cvtColor(desert, cv.COLOR_BGR2GRAY))
    dmask[np.where(dmask != 0)] = 255
    desert_top = cv.bitwise_and(canv,canv,mask=dmask)
    desert_top = cv.addWeighted(desert_top,1-desert_alpha,desert,desert_alpha,0)

    canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(dmask))
    canv = cv.add(canv,desert_top)

    print("Drawing glaciers...")
    biome = cv.imread(maps["bm"],cv.IMREAD_COLOR)
    glacier = np.zeros(biome.shape, dtype="uint8")
    glacier[np.where((biome==[255,255,0]).all(axis=2))] = [255,255,255]
    glacier[np.where((biome==[255,255,64]).all(axis=2))] = [255,255,255]
    glacier[np.where((biome==[255,255,128]).all(axis=2))] = [255,255,255]
    #glacier = cv.dilate(glacier, kernel, iterations=1)
    #[247,253,254]

    gmask = np.uint8(cv.cvtColor(glacier, cv.COLOR_BGR2GRAY))
    glac_top = cv.bitwise_and(canv,canv,mask=gmask)
    glac_top = cv.addWeighted(glac_top,1-glac_alpha,glacier,glac_alpha,0)

    canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(gmask))
    canv = cv.add(canv,glac_top)

    #cv.imshow("dd",canv)
    #cv.waitKey(1)

    print("Drawing water...")
    water = cv.imread(maps["hyd"],cv.IMREAD_COLOR)

    rivers = np.zeros(veg.shape, dtype="uint8")
    rivers[np.where((water==[255,96,0]).all(axis=2))] = [255]      #lake
    rivers[np.where((water==[255,112,0]).all(axis=2))] = [255]    #ocean river
    rivers[np.where((water==[255,128,0]).all(axis=2))] = [255]    #major river
    rivers[np.where((water==[255,160,0]).all(axis=2))] = [255]    #river
    rivers[np.where((water==[255,192,0]).all(axis=2))] = [255]    #minor river
    rivers[np.where((water==[255,224,0]).all(axis=2))] = [255]    #stream
    if brook:
        rivers[np.where((water==[255,255,0]).all(axis=2))] = [255]    #brook

    ret,riv_mask = cv.threshold(rivers,1,255,cv.THRESH_BINARY)
    canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(riv_mask))

    col = color[72]
    rivers = cv.merge([riv_mask/255*col[2],riv_mask/255*col[1],riv_mask/255*col[0]])
    canv = cv.add(np.uint8(canv),np.uint8(rivers))

    if territory_check:
        print("Drawing territories...")
        i = 0
        k = cv.getStructuringElement(cv.MORPH_ELLIPSE,(15,15))

        #VORONOI TERRITORY 2 ELECTRIC BOOGALGOO
        delauny = np.zeros(elevation.shape, dtype="uint8")
        pts = []
        rulers = []
        for s in occ_sites:#d_sites:
            if "ruler" in occ_sites[s] and int(occ_sites[s]["ruler"]) >= 0 and occ_sites[s]["ruler"] in ents:
                ((x1,y1),(x2,y2)) = d_sites[s]["rect"]
                x = int((int(x1)+int(x2))/2)
                y = int((int(y1)+int(y2))/2)
                pts.append((x,y))
                rulers.append(int(d_sites[s]["ruler"]))
                cv.circle(delauny,(x,y), 2, (255,255,255), -1)

        russet = sorted(set(rulers))
        i = 0
        for s in russet:
            rulers = [i if s == x else x for x in rulers]
            i = i + 1

        rect = (0, 0, maxy, maxx)
        subdiv  = cv.Subdiv2D(rect);
        for p in pts:
            subdiv.insert(p)

        def draw_voronoi(img, subdiv) :
            (facets, centers) = subdiv.getVoronoiFacetList([])
            for i in range(0,len(facets)) :
                ifacet_arr = []
                for f in facets[i] :
                    ifacet_arr.append(f)

                ifacet = np.array(ifacet_arr, np.intc)
                color = (rulers[i],rulers[i],rulers[i])#ent_colors[rulers[i]]

                cv.fillConvexPoly(img, ifacet, color, cv.LINE_4, 0);
                #ifacets = np.array([ifacet])
                #cv.polylines(img, ifacets, True, (0, 0, 0), 1, cv.LINE_AA, 0)
                #cv.circle(img, (centers[i][0], centers[i][1]), 3, (0, 0, 0), -1, cv.LINE_AA, 0)

        draw_voronoi(delauny,subdiv)

        facets = []
        for i in range(0,max(rulers)+1):
            vp = np.zeros(veg.shape, dtype="uint8")
            vp[np.where((delauny==[i,i,i]).all(axis=2))] = [255]#ent_colors[i]
            facets.append(vp)

        #    terr = cv.bitwise_and(vp,vp,mask=t[73])
        #    terr_top = cv.bitwise_and(canv,canv,mask=terr)
        #    terr_overlay = np.ones(img.shape,dtype="uint8")*[ent_colors[i][2],ent_colors[i][1],ent_colors[i][0]]
        #    terr_overlay = cv.bitwise_and(terr_overlay,terr_overlay,mask=terr).astype(np.uint8)
        #    terr_top = cv.addWeighted(terr_top,1-terr_alpha,terr_overlay,terr_alpha,0)
        #    canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(terr))
        #    canv = cv.add(canv,terr_top)

        i = 0
        terrs = []
        disp = []
        for e in ents:
            terr = np.zeros(veg.shape, dtype="uint8")
            occ_pts = []
            for s in occ_sites:
                if occ_sites[s]["ruler"] == e:
        #            xy = occ_sites[s]["pos"]
        #            x = int(xy[0])*16
        #            y = int(xy[1])*16
                    ((x1,y1),(x2,y2)) = occ_sites[s]["rect"]
                    x = int((int(x1)+int(x2))/2)
                    y = int((int(y1)+int(y2))/2)
                    occ_pts = (x,y)
                    #cv.rectangle(terr,(int(x),int(y)),(int(x+16),int(y+16)),(255),-1)
                    cv.circle(terr,(x,y), 8, (255), -1)
                    
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
            if occ_pts == []:
                continue
        
            for q in range(len(facets)):
                if facets[q][occ_pts[1]][occ_pts[0]]:
                    ii = q
                    break;
            #ii is the biggest voronoi cell(s)
        #    print(ii,n)
            
            disp.append(terr)
            terr = cv.bitwise_and(terr,terr,mask=facets[ii])
            terrs.append(terr)
        
        for i,terr in enumerate(terrs):
            c1 = int(list(ents)[i])
        
            for j,uerr in enumerate(disp):
                c2 = int(list(ents)[j])
                if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                    terr = cv.subtract(terr,uerr)
        
            terr = cv.bitwise_and(terr,terr, mask = t[73])
            terr_top = cv.bitwise_and(canv,canv,mask=terr)
            if i >= len(ent_colors):
                print("Error: Not enough colors in ent_colors")
                i = i % len(ent_colors)
            terr_overlay = np.ones(elevation.shape,dtype="uint8")*[ent_colors[i][2],ent_colors[i][1],ent_colors[i][0]]
            terr_overlay = cv.bitwise_and(terr_overlay,terr_overlay,mask=terr).astype(np.uint8)
        
            terr_top = cv.addWeighted(terr_top,1-terr_alpha,terr_overlay,terr_alpha,0)
        
            canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(terr))
            canv = cv.add(canv,terr_top)
        #    i = i + 1
        #################################################################################
        diag_width = 1
        diag_space = 0
        
        outerlay = np.zeros(elevation.shape,dtype="uint8")
        outermask = np.zeros(veg.shape,dtype="uint8")
        for i,terr in enumerate(terrs):
            c1 = int(list(ents)[i])
        
            diag = np.zeros(veg.shape,dtype="uint8")
            for d in range(0,2*maxx,len(disp)*(diag_width+diag_space)):
                    cv.line(diag,(maxy,d-maxx+i*(diag_width+diag_space)),(0,d+i*(diag_width+diag_space)),(255),diag_width)
            
            for j,uerr in enumerate(disp):
                c2 = int(list(ents)[j])
                m = 0
                if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                    inter = cv.bitwise_and(disp[i],disp[j])
                    m = cv.countNonZero(inter)
                if m > 0:
                    if i >= len(ent_colors):
                        i = i % len(ent_colors)
                    overlay = np.ones(elevation.shape,dtype="uint8")*[ent_colors[i][2],ent_colors[i][1],ent_colors[i][0]]
                    mask = cv.bitwise_and(inter,diag)
                    overlay = cv.bitwise_and(overlay,overlay,mask=mask).astype(np.uint8)
                        
                    eiag = np.zeros(veg.shape,dtype="uint8")
                    for d in range(0,2*maxx,len(terrs)*(diag_width+diag_space)):
                        cv.line(eiag,(maxy,d-maxx+j*(diag_width+diag_space)),(0,d+j*(diag_width+diag_space)),(255),diag_width)
                    
                    if j >= len(ent_colors):
                        j = j % len(ent_colors)
        
                    everlay = np.ones(elevation.shape,dtype="uint8")*[ent_colors[j][2],ent_colors[j][1],ent_colors[j][0]]
                    emask = cv.bitwise_and(inter,eiag)
                    everlay = cv.bitwise_and(everlay,everlay,mask=emask).astype(np.uint8)
                    
                    fmask = cv.add(mask,emask)
            
                    overlay = cv.add(overlay,everlay)
        
                    templay = cv.bitwise_and(overlay,overlay,mask=cv.bitwise_not(outermask))
                    outerlay = cv.add(outerlay,templay)
                    outermask = cv.add(outermask,fmask)
        
        
        outermask = cv.bitwise_and(outermask,outermask,mask = t[73])
        outerlay = cv.bitwise_and(outerlay,outerlay,mask = outermask)
        canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(outermask))
        canv = cv.add(canv,outerlay)
        
        #BORDERS
        for i,terr in enumerate(terrs):
            edges = cv.Canny(terr,0,0)
            edges = cv.dilate(edges, kernel, iterations=1)
            edges = cv.erode(edges, kernel, iterations=1)
        #cv.imshow("d",edges)
        #cv.waitKey(0)
            c1 = int(list(ents)[i])
            for j,uerr in enumerate(disp):
                c2 = int(list(ents)[j])
                if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                    edges = cv.subtract(edges,uerr)
        
            edges = cv.bitwise_and(edges,edges,mask=t[73])
        
            if i >= len(ent_colors):
                i = i % len(ent_colors)
        
            overlay = np.ones(elevation.shape,dtype="uint8")*[ent_colors[i][2],ent_colors[i][1],ent_colors[i][0]]
            overlay = cv.bitwise_and(overlay,overlay,mask=edges).astype(np.uint8)
            canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(edges))
            canv = cv.add(canv,overlay)
            
        #vp = cv.dilate(vp, kernel, iterations=1)
        #    vcont, hierarchy = cv.findContours(vp, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        #    cv.drawContours(canv, vcont, -1, (0,0,0), 1, cv.LINE_4)
        #    cv.imshow("d",canv)
        #    cv.waitKey(0)
    
    
    if structure_check:
        print("Drawing structures...")
        struct = cv.imread(maps["str"],cv.IMREAD_COLOR)
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
        
        
        castle[np.where((struct==[128,128,128]).all(axis=2))] = [255]    #castle
        village[np.where((struct==[255,255,255]).all(axis=2))] = [255]    #village
        tunnel[np.where((struct==[20,20,20]).all(axis=2))] = [255]    #tunnel
        sbridge[np.where((struct==[224,224,224]).all(axis=2))] = [255]    #stone bridge
        sroad[np.where((struct==[192,192,192]).all(axis=2))] = [255]    #stone road
        swall[np.where((struct==[96,96,96]).all(axis=2))] = [255]    #stone wall
        bridge[np.where((struct==[20,167,180]).all(axis=2))] = [255]    #other bridge
        road[np.where((struct==[20,127,150]).all(axis=2))] = [255]    #other road
        wall[np.where((struct==[20,127,160]).all(axis=2))] = [255]    #other wall
        
        crop1[np.where((struct==[0,128,255]).all(axis=2))] = [255]    #crops (all crops are humans)
        crop2[np.where((struct==[0,160,255]).all(axis=2))] = [255]    #crops
        crop3[np.where((struct==[0,192,255]).all(axis=2))] = [255]    #crops
        pasture[np.where((struct==[0,255,0]).all(axis=2))] = [255]    #pasture (dwarves mostly, some human)
        meadow[np.where((struct==[0,255,64]).all(axis=2))] = [255]    #meadow
        woodland[np.where((struct==[0,128,0]).all(axis=2))] = [255]    #woodland
        orchard[np.where((struct==[0,160,0]).all(axis=2))] = [255]    #orchard (elves)
        
        #print("Drawing villages...")
        #village = cv.dilate(village, kernel, iterations=2)
        #village = cv.erode(village, kernel, iterations=1)
        #vill_overlay = cv.merge([np.uint8(village/255*vill_color[2]),np.uint8(village/255*vill_color[1]),np.uint8(village/255*vill_color[0])])
        #vill_top = cv.bitwise_and(canv,canv,mask=village)
        #vill_top = cv.addWeighted(vill_top,1-vill_alpha,vill_overlay,vill_alpha,0)
        #canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(village))
        #canv = cv.add(canv,vill_top)
        
        print("Drawing crops...")
        crops = cv.add(crop1,crop2)
        crops = cv.add(crops,crop3)
        plain = cv.add(pasture,meadow)
        woods = cv.add(woodland,orchard)
        ag = cv.add(crops,plain)
        ag = cv.add(ag,woods)
        
        ag_overlay = cv.merge([np.uint8(ag/255*ag_color[2]),np.uint8(ag/255*ag_color[1]),np.uint8(ag/255*ag_color[0])])
        ag_top = cv.bitwise_and(canv,canv,mask=ag)
        ag_top = cv.addWeighted(ag_top,1-ag_alpha,ag_overlay,ag_alpha,0)
        canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(ag))
        canv = cv.add(canv,ag_top)
        
        #convil, hierarchy = cv.findContours(village, 1, 2)
        
        #for c in convil:
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
        
        #CASTLES
        #print("Drawing castles...")
        #castle = cv.dilate(castle, kernel, iterations=1)
        #castle = cv.erode(castle, kernel, iterations=1)
        #concast, hierarchy = cv.findContours(castle, 1, 2)
        #for c in concast:
        #    M = cv.moments(c)
        #    if M["m00"] == 0:
        #        continue
        #    cX = int(M["m10"] / M["m00"])
        #    cY = int(M["m01"] / M["m00"])
        #    radius = math.sqrt(cv.contourArea(c))/2
            #print(radius)
        #    cv.circle(canv, (cX, cY), math.floor(radius), (0,0,0), -1)
        
        print("Drawing roads...")
        roads = cv.add(road,sroad)
        bridges = cv.add(bridge,sbridge)
        
        path = cv.add(roads,bridges)
        path = cv.add(path,tunnel)
        
        pts = []
        for s in d_sites:
            ((x1,y1),(x2,y2)) = d_sites[s]["rect"]
            x = int((int(x1)+int(x2))/2)
            y = int((int(y1)+int(y2))/2)
            pts.append((x,y))
            #cv.circle(path,(x,y), 1, (255), -1)
        
        #corners = cv.goodFeaturesToTrack(path, 200, 0.05, 16)
        #hole = []
        #for i in range(0,len(corners)):
        #    for j in range(i+1,len(corners)):
        #        x1,y1 = corners[i].ravel()
        #        x2,y2 = corners[j].ravel()
        #        w = 16
        #        if abs(x1-x2)<=w and abs(y1-y2)<=w:
        #            hole.append((x1,y1,x2,y2))
        #            cv.circle(path,(int(x1),int(y1)), 3, (255), -1)
        #for h in hole:
        #    (x1,y1,x2,y2) = h
        #    cv.line(path,(int(x1),int(y1)),(int(x2),int(y2)),(255),1)
        
        #cv.imshow("p",path)
        
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
            print(it,":",clen,"contours")
            for i in range(len(cnt)):
                area = cv.contourArea(cnt[i])
                dist = 99
                for j in range(i+1,len(cnt)):
                    for pi in cnt[i]:
                        for pj in cnt[j]:
                            x1,y1 = pi.ravel()
                            x2,y2 = pj.ravel()
                            d = math.sqrt((x1-x2)**2 + (y1-y2)**2)
                            if d < dist:
                                dist = d
                                a = (x1,y1)
                                b = (x2,y2)
                if dist < 32:
                    holes.append((a,b))
            for h in holes:
                cv.line(path,h[0],h[1],(255),1)
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
        
        #for p in pts:
        #    cv.circle(path,p, 1, (127), -1)
        
        #cv.imshow("d",path)
        #cv.waitKey(0)
        
        path_overlay = cv.merge([np.uint8(path/255*path_color[2]),np.uint8(path/255*path_color[1]),np.uint8(path/255*path_color[0])])
        canv = cv.bitwise_and(canv,canv,mask=cv.bitwise_not(path))
        canv = cv.add(canv,path_overlay)
    
    
    if grid_draw:
        print("Drawing grid...")
        size = len(canv)
        grid_spacing = 43
        grid_width = 1
        grid_color = [200,200,200]
        grid_offset = 5
        grid_alpha = .7
        for i in range(grid_offset, grid_width + grid_offset):    
            canv[i:size:grid_spacing,:] = grid_color
            canv[:,i:size:grid_spacing] = grid_color
        
    # grid_top = cv.addWeighted(glac_top,1-grid_alpha,glacier,grid_alpha,0)
    
    print("Drawing labels...")
    bigprint = ["tower","dark fortress","castle",]
    medprint = ["town","fort","monastery","tomb","fortress","labyrinth","mountain halls"]
    smallprint = ["dark pits","hillocks","hamlet","forest retreat"]
    noprint = ["camp","cave","lair","vault","shrine"]
    typeprint = ["tower","dark fortress","fortress","castle"]
    
    marquee = []
    im = Image.fromarray(canv[:,:,::-1])
    im = im.convert("RGBA")
    overlap = np.zeros(veg.shape, dtype="uint8")
    
    if other_labels_check:
        ###############################
        for s in d_sites:
            if d_sites[s]["name"] in mandatory_cities:
                marquee.append(s)
        
        for s in d_sites:
            if (d_sites[s]["type"] in bigprint+medprint+smallprint or d_sites[s]["name"] in mandatory_cities):
                ((x1,y1),(x2,y2)) = d_sites[s]["rect"]
                x = int((int(x1)+int(x2))/2)
                y = int((int(y1)+int(y2))/2)
        
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
                    
                cv.circle(canv,(x,y), size, col, -1)
        
        #        print(x,y,d_sites[s]["rect"])
            elif d_sites[s]["type"] in noprint:
                continue
            else:
                print(d_sites[s]["type"])
        
        
        
        for s in marquee:
            back = Image.new("RGBA", (maxx,maxy))
            draw = ImageDraw.Draw(back)    
            
            ((x1,y1),(x2,y2)) = d_sites[s]["rect"]
            x = int((int(x1)+int(x2))/2)
            y = int((int(y1)+int(y2))/2)        
            
            subtext = ""
            if "trans" in d_sites[s]:
                if d_sites[s]["trans"][0].isascii():
                    text = d_sites[s]["trans"].title()
                else:
                    text = d_sites[s]["trans"]
                subtext = d_sites[s]["name"].title()
            else:
                text = d_sites[s]["name"].title()
                
            bbox = draw.textbbox((0,0), text, font)
            textsize = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            bbox2 = draw.textbbox((0,0), subtext, subfont)
            textsize2 = (bbox2[2] - bbox2[0], bbox2[3] - bbox2[1])
                
            testlap = np.zeros(veg.shape, dtype="uint8")
            if x < maxx-textsize[0]-text_offset[0]:
                anchor = "lm"
                cv.rectangle(testlap,(x+text_offset[0],int(y+textsize[1]/2+textsize2[1])),(x+text_offset[0]+textsize[0],int(y-textsize[1]/2)),(255),-1)
            else:
                print(d_sites[s]["name"],"reversed.")
                anchor = "rm"
                cv.rectangle(testlap,(x-textsize[0]-text_offset[0],int(y+textsize[1]/2+textsize2[1])),(x-text_offset[0],int(y-textsize[1]/2)),(255),-1)
                    
            if cv.countNonZero(cv.bitwise_and(testlap,overlap)) > 0:
                print(d_sites[s]["name"],"label clash")
                continue
            
            #Shadows
            overlap = cv.add(testlap,overlap)
            if anchor == "lm":
                draw.text((x+text_offset[0],y),text,font = font,anchor=anchor,fill=(0,0,0,255))
                draw.text((x+text_offset[0]+textsize[0]/2,y+textsize[1]/2),subtext,font = subfont,anchor="ma",fill=blur_color)
            else:
                draw.text((x-text_offset[0],y),text,font = font,anchor=anchor,fill=(0,0,0,255))
                draw.text((x-text_offset[0]-textsize[0]/2,y+textsize[1]/2),subtext,font = subfont,anchor="ma",fill=blur_color)
                    
            back = back.filter(ImageFilter.GaussianBlur(radius=3))
            back.alpha_composite(back)
            back.alpha_composite(back)
                
            #Text
            draw = ImageDraw.Draw(back)
            if anchor == "lm":
                draw.text((x+text_offset[0],y),text,font = font,anchor=anchor,color=label_color)
                draw.text((x+text_offset[0]+textsize[0]/2,y+textsize[1]/2),subtext,font = subfont,color=label_color,anchor="ma")
            else:
                draw.text((x-text_offset[0],y),text,font = font,anchor=anchor)
                draw.text((x-text_offset[0]-textsize[0]/2,y+textsize[1]/2),subtext,font = subfont,color=label_color,anchor="ma")
            im.alpha_composite(back)
    
    
    back = Image.new("RGBA", (maxx,maxy))
    draw = ImageDraw.Draw(back)
    
    titlebox = draw.textbbox((0,0), worldtransname, titlefont)
    titlesize = (titlebox[2] - titlebox[0], titlebox[3] - titlebox[1])
    subbox = draw.textbbox((0,0), worldname, subtitlefont)
    subsize = (subbox[2] - subbox[0], subbox[3] - subbox[1])
    if title_align == "":
        n = 999
        for i in ["tl","tr","bl","br"]:
            titlebox = np.zeros(veg.shape, dtype="uint8")
            if i == "tl":
                anchor = "la"
                (x,y) = (0+titleadjust[0],0+titleadjust[1])
                (x1,y1) = (int(x+titlesize[0]/2),y+titlesize[1])
                cv.rectangle(titlebox,(x,y),(x+titlesize[0],y+titlesize[1]),(255),-1)    
                cv.rectangle(titlebox,(int(x1-subsize[0]/2),y1),(int(x1+subsize[0]/2),y+titlesize[1]),(255),-1)
            elif i == "tr":
                anchor = "ra"
                (x,y) = (maxx-titleadjust[0],0+titleadjust[1])
                (x1,y1) = (int(x-titlesize[0]/2),y+titlesize[1])
                cv.rectangle(titlebox,(x-titlesize[0],y),(x,y+titlesize[1]),(255),-1)    
                cv.rectangle(titlebox,(int(x1-subsize[0]/2),y1),(int(x1+subsize[0]/2),y+titlesize[1]),(255),-1)
            elif i == "bl":
                anchor = "ld"
                (x,y) = (0+titleadjust[0],maxy-titleadjust[1]-subsize[1])
                (x1,y1) = (int(x+titlesize[0]/2),y)
                cv.rectangle(titlebox,(x,y-titlesize[1]),(x+titlesize[0],y),(255),-1)    
                cv.rectangle(titlebox,(int(x1-subsize[0]/2),y1),(int(x1+subsize[0]/2),y+titlesize[1]),(255),-1)
            elif i == "br":
                anchor = "rd"
                (x,y) = (maxx-titleadjust[0],maxy-titleadjust[1]-subsize[1])
                (x1,y1) = (int(x-titlesize[0]/2),y)
                cv.rectangle(titlebox,(x-titlesize[0],y-titlesize[1]),(x,y),(255),-1)    
                cv.rectangle(titlebox,(int(x1-subsize[0]/2),y1),(int(x1+subsize[0]/2),y+titlesize[1]),(255),-1)
            m = cv.countNonZero(cv.bitwise_and(titlebox,overlap))
            if m < n:
                n = m
                title_align = i
        print("Autotitle in", title_align)
    
    #titlesize = (max(titlesize[0],subsize[0]),titlesize[1])
    
    if title_align == "tm":
        anchor = "ma"
        (x,y) = (maxx/2,0+titleadjust[1])
        (x1,y1) = (x,y+titlesize[1])
    if title_align == "tl":
        anchor = "la"
        (x,y) = (0+titleadjust[0],0+titleadjust[1])
        (x1,y1) = (x+titlesize[0]/2,y+titlesize[1])
    elif title_align == "tr":
        anchor = "ra"
        (x,y) = (maxx-titleadjust[0],0+titleadjust[1])
        (x1,y1) = (x-titlesize[0]/2,y+titlesize[1])
    elif title_align == "bl":
        anchor = "ld"
        (x,y) = (0+titleadjust[0],maxy-titleadjust[1]-subsize[1])
        (x1,y1) = (x+titlesize[0]/2,y)
    elif title_align == "br":
        anchor = "rd"
        (x,y) = (maxx-titleadjust[0],maxy-titleadjust[1]-subsize[1])
        (x1,y1) = (x-titlesize[0]/2,y)
    
    draw.text((x,y),worldtransname,font = titlefont,anchor=anchor,fill=(0,0,0,255))
    draw.text((x1,y1),worldname,font = subtitlefont,anchor="ma",fill=blur_color)
    back = back.filter(ImageFilter.GaussianBlur(radius=3))
    back.alpha_composite(back)
    back.alpha_composite(back)
    
    draw = ImageDraw.Draw(back)
    draw.text((x,y),worldtransname,font = titlefont,anchor=anchor,color=label_color)
    draw.text((x1,y1),worldname,font = subtitlefont,anchor="ma",color=label_color)
    im.alpha_composite(back)
            
    im.show()
    print("Saving to file...")
    output_path = "Maps/"
    im.save(f"{output_path}{worldtransname} - extra.png")
    print("---------------------------")
    print(f"All maps generated for {worldtransname}")
    print("---------------------------")
    '''
    overlap = np.zeros(veg.shape, dtype="uint8")
    for s in d_sites:
        if d_sites[s]["name"] in mandatory_cities:
            testlap = np.zeros(veg.shape, dtype="uint8")
                
            ((x1,y1),(x2,y2)) = d_sites[s]["rect"]
            x = int((int(x1)+int(x2))/2)
            y = int((int(y1)+int(y2))/2)        
            
            if "trans" in d_sites[s]:
                text = d_sites[s]["trans"].title()
            else:
                text = d_sites[s]["name"].title()

            textsize = cv.getTextSize(text, font, 1, 1)[0]
            
            if x < maxx-textsize[0]:
                cv.rectangle(testlap,(x+text_offset[0],y+text_offset[1]),(x+text_offset[0]+textsize[0],y+text_offset[1]-textsize[1]),(255),-1)
                if cv.countNonZero(cv.bitwise_and(testlap,overlap)) == 0:
                    overlap = cv.add(testlap,overlap)
                    #cv.rectangle(canv,(x+5,y+5),(x+5+textsize[0],y+5-textsize[1]),(255,255,255),-1)
                    sub_canv = canv[y+text_offset[1]-textsize[1]-text_margin:y+text_offset[1]+text_margin,x+text_offset[0]-text_margin:x+text_offset[0]+textsize[0]+text_margin]
                    wrect = np.zeros(sub_canv.shape,dtype=np.uint8)
                    cv.putText(wrect,text,(text_margin,textsize[1]+text_margin), font, 1, (255,255,255), 2, cv.LINE_AA)
                    wrect = cv.blur(wrect,blur)
                    if blur_color == "black":
                        res = cv.subtract(sub_canv,np.uint8(wrect*glow_alpha))
                    else:
                        res = cv.add(sub_canv,np.uint8(wrect*glow_alpha))
    #                wrect = np.ones(sub_canv.shape, dtype=np.uint8)*255
    #                res = cv.addWeighted(sub_canv,0.5,wrect,0.5,1.0)
                    canv[y+text_offset[1]-text_margin-textsize[1]:y+text_offset[1]+text_margin,x+text_offset[0]-text_margin:x+text_offset[0]+textsize[0]+text_margin] = res
                    cv.putText(canv,text,(x+text_offset[0],y+text_offset[1]), font, 1, label_color, 1, cv.LINE_AA)
            else:
                cv.rectangle(testlap,(x-textsize[0]-text_offset[0],y+text_offset[1]),(x-text_offset[0],y+text_offset[1]-textsize[1]),(255),-1)
                if cv.countNonZero(cv.bitwise_and(testlap,overlap)) == 0:
                    overlap = cv.add(testlap,overlap)
    #                cv.rectangle(canv,(x-textsize[0]-5,y+5),(x-5,y+5-textsize[1]),(255,255,255),-1)
                    sub_canv = canv[y+text_offset[1]-textsize[1]-text_margin:y+text_offset[1]+text_margin,x-textsize[0]-text_offset[0]-text_margin:x-text_offset[0]+text_margin]
                    wrect = np.zeros(sub_canv.shape, dtype=np.uint8)
                    cv.putText(wrect,text,(text_margin,textsize[1]+text_margin), font, 1, (255,255,255), 2, cv.LINE_AA)
                    wrect = cv.blur(wrect,blur)
                    if blur_color == "black":
                        res = cv.subtract(sub_canv,np.uint8(wrect*glow_alpha))
                    else:
                        res = cv.add(sub_canv,np.uint8(wrect*glow_alpha))
                    #res = cv.addWeighted(sub_canv,0.5,wrect,0.5,1.0)
                    canv[y+text_offset[1]-textsize[1]-text_margin:y+text_offset[1]+text_margin,x-textsize[0]-text_offset[0]-text_margin:x-text_offset[0]+text_margin] = res
                    cv.putText(canv,text,(x-textsize[0]-text_offset[0],y+text_offset[1]), font, 1, label_color, 1, cv.LINE_AA)

    for s in d_sites:
        if d_sites[s]["type"] in typeprint:
            testlap = np.zeros(veg.shape, dtype="uint8")
            
            ((x1,y1),(x2,y2)) = d_sites[s]["rect"]
            x = int((int(x1)+int(x2))/2)
            y = int((int(y1)+int(y2))/2)        
            
            if "trans" in d_sites[s]:
                text = d_sites[s]["trans"].title()
            else:
                text = d_sites[s]["name"].title()
            textsize = cv.getTextSize(text, font, 1, 1)[0]
            
            if x < maxx-textsize[0]:
                cv.rectangle(testlap,(x+text_offset[0],y+text_offset[1]),(x+text_offset[0]+textsize[0],y+text_offset[1]-textsize[1]),(255),-1)
                if cv.countNonZero(cv.bitwise_and(testlap,overlap)) == 0:
                    overlap = cv.add(testlap,overlap)
                    #cv.rectangle(canv,(x+5,y+5),(x+5+textsize[0],y+5-textsize[1]),(255,255,255),-1)
                    sub_canv = canv[y+text_offset[1]-textsize[1]-text_margin:y+text_offset[1]+text_margin,x+text_offset[0]-text_margin:x+text_offset[0]+textsize[0]+text_margin]
                    wrect = np.zeros(sub_canv.shape,dtype=np.uint8)
                    cv.putText(wrect,text,(text_margin,textsize[1]+text_margin), font, 1, (255,255,255), 2, cv.LINE_AA)
                    wrect = cv.blur(wrect,blur)
                    if blur_color == "black":
                        res = cv.subtract(sub_canv,np.uint8(wrect*glow_alpha))
                    else:
                        res = cv.add(sub_canv,np.uint8(wrect*glow_alpha))
    #                wrect = np.ones(sub_canv.shape, dtype=np.uint8)*255
    #                res = cv.addWeighted(sub_canv,0.5,wrect,0.5,1.0)
                    canv[y+text_offset[1]-text_margin-textsize[1]:y+text_offset[1]+text_margin,x+text_offset[0]-text_margin:x+text_offset[0]+textsize[0]+text_margin] = res
                    cv.putText(canv,text,(x+text_offset[0],y+text_offset[1]), font, 1, label_color, 1, cv.LINE_AA)
            else:
                cv.rectangle(testlap,(x-textsize[0]-text_offset[0],y+text_offset[1]),(x-text_offset[0],y+text_offset[1]-textsize[1]),(255),-1)
                if cv.countNonZero(cv.bitwise_and(testlap,overlap)) == 0:
                    overlap = cv.add(testlap,overlap)
    #                cv.rectangle(canv,(x-textsize[0]-5,y+5),(x-5,y+5-textsize[1]),(255,255,255),-1)
                    sub_canv = canv[y+text_offset[1]-textsize[1]-text_margin:y+text_offset[1]+text_margin,x-textsize[0]-text_offset[0]-text_margin:x-text_offset[0]+text_margin]
                    wrect = np.zeros(sub_canv.shape, dtype=np.uint8)
                    cv.putText(wrect,text,(text_margin,textsize[1]+text_margin), font, 1, (255,255,255), 2, cv.LINE_AA)
                    wrect = cv.blur(wrect,blur)
                    if blur_color == "black":
                        res = cv.subtract(sub_canv,np.uint8(wrect*glow_alpha))
                    else:
                        res = cv.add(sub_canv,np.uint8(wrect*glow_alpha))
                    #res = cv.addWeighted(sub_canv,0.5,wrect,0.5,1.0)
                    canv[y+text_offset[1]-textsize[1]-text_margin:y+text_offset[1]+text_margin,x-textsize[0]-text_offset[0]-text_margin:x-text_offset[0]+text_margin] = res
                    cv.putText(canv,text,(x-textsize[0]-text_offset[0],y+text_offset[1]), font, 1, label_color, 1, cv.LINE_AA)

    #structs = cv.merge([structs,structs,structs])
    #canv = cv.add(np.uint8(canv),np.uint8(structs))
    '''

    return canv


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog='ARMap',
                    description=DESCRIPTION,
                    )

    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-g', '--grid', action='store_true')
    args = parser.parse_args()


    DEBUG = args.debug
    grid_draw = args.grid

    if DEBUG:
        print(f"OpenCV Version: { cv.__version__ }")

    folders = os.listdir(ROOT_PATH)

    # TODO: confirm with Myckou what is the "complete" flow
    if "Complete" in folders:
        folders.remove("Complete")

    if folders == []:
        print("No map data folders present.")

    canv = None
    for f in folders:
        canv = generate(f)

    if DEBUG and canv:
        cv.imshow("wat",canv)
        cv.waitKey(0)

    print("Done!")
