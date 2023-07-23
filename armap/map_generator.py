# TODO: Add license

import typing
import time

import cv2 as cv
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from .config_parser import ConfigParser
from .legends_parser import LegendParser

class MapGenerator():
    """TODO: add description"""

    def __init__(self, config:ConfigParser, legends:LegendParser, base_map_file:str) -> None:
        self.config = config
        self.legends = legends
        self.size = cv.imread(base_map_file, cv.IMREAD_GRAYSCALE).shape
        (self.maxx, self.maxy) = self.size
        self.canvas = np.ones((self.maxx,self.maxy), np.uint8)
        self.ground = None
        self.kernel = None

    def generate_map(self, color_name:str) -> None:
        """TODO: add description"""
        # Get color from palette
        color = self.config.palette_dict[color_name]
        self.canvas = np.ones((self.maxx,self.maxy), np.uint8)
        print(f"Beginning {color_name} map generation")

        self.draw_base(self.legends.maps["el"], color)
        self.draw_vegetation(self.legends.maps["veg"])
        self.draw_biomes(self.legends.maps["bm"])
        self.draw_water(self.legends.maps["hyd"], color)
        
        if self.config.territory_check:
            self.draw_territory()
        """
        if self.config.structure_check:
            print("Drawing structures...")
            struct = cv.imread(self.legends.maps["str"], cv.IMREAD_COLOR)
            castle = np.zeros(size, dtype="uint8")
            village = np.zeros(size, dtype="uint8")
            tunnel = np.zeros(size, dtype="uint8")
            sbridge = np.zeros(size, dtype="uint8")
            sroad = np.zeros(size, dtype="uint8")
            swall = np.zeros(size, dtype="uint8")
            bridge = np.zeros(size, dtype="uint8")
            road = np.zeros(size, dtype="uint8")
            wall = np.zeros(size, dtype="uint8")
            crop1 = np.zeros(size, dtype="uint8")
            crop2 = np.zeros(size, dtype="uint8")
            crop3 = np.zeros(size, dtype="uint8")
            pasture = np.zeros(size, dtype="uint8")
            meadow = np.zeros(size, dtype="uint8")
            woodland = np.zeros(size, dtype="uint8")
            orchard = np.zeros(size, dtype="uint8")

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
            # vill_overlay = cv.merge([np.uint8(village/255*vill_color[2]),
            #   np.uint8(village/255*vill_color[1]),np.uint8(village/255*vill_color[0])])
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
            if not process_road:
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
                    cv.line(path, h[0], h[1], 255, 1)

            path_overlay = cv.merge([np.uint8(path / 255 * path_color[2]), np.uint8(path / 255 * path_color[1]),
                                    np.uint8(path / 255 * path_color[0])])
            canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(path))
            canv = cv.add(canv, path_overlay)
        """

        """
        if self.config.grid_draw:
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
        """

        """
        print("Drawing labels...")
        bigprint = ["tower", "dark fortress", "castle", ]
        medprint = ["town", "fort", "monastery", "tomb", "fortress", "labyrinth", "mountain halls"]
        smallprint = ["dark pits", "hillocks", "hamlet", "forest retreat"]
        noprint = ["camp", "cave", "lair", "vault", "shrine"]
        typeprint = ["tower", "dark fortress", "fortress", "castle"]

        marquee = []

        if self.config.other_labels_check:
            ###############################
            for s in d_sites:
                if d_sites[s]["name"] in self.config.required_cities:
                    marquee.append(s)

            for s in d_sites:
                if d_sites[s]["type"] in bigprint + medprint + smallprint or d_sites[s]["name"] in mandatory_cities:
                    ((x1, y1), (x2, y2)) = d_sites[s]["rect"]
                    x = int((int(x1) + int(x2)) / 2)
                    y = int((int(y1) + int(y2)) / 2)

                    if d_sites[s]["type"] in bigprint:
                        size = self.config.big_point
                    elif d_sites[s]["type"] in medprint:
                        size = self.config.med_point
                    else:
                        size = self.config.small_point

                    if d_sites[s]["type"] in typeprint or d_sites[s]["name"] in mandatory_cities:
                        col = self.config.primary_label_color
                    else:
                        col = self.config.secondary_label_color

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

                bbox = draw.textbbox((0, 0), text, self.config.font)
                textsize = (bbox[2] - bbox[0], bbox[3] - bbox[1])
                bbox2 = draw.textbbox((0, 0), subtext, self.config.subfont)
                textsize2 = (bbox2[2] - bbox2[0], bbox2[3] - bbox2[1])

                testlap = np.zeros(size, dtype="uint8")
                if x < maxx - textsize[0] - self.config.text_offset[0]:
                    anchor = "lm"
                    cv.rectangle(testlap, (x + self.config.text_offset[0], int(y + textsize[1] / 2 + textsize2[1])),
                                (x + self.config.text_offset[0] + textsize[0], int(y - textsize[1] / 2)), 255, -1)
                else:
                    print(d_sites[s]["name"], "reversed.")
                    anchor = "rm"
                    cv.rectangle(testlap, (x - textsize[0] - self.config.text_offset[0], int(y + textsize[1] / 2 + textsize2[1])),
                                (x - self.config.text_offset[0], int(y - textsize[1] / 2)), 255, -1)

                if cv.countNonZero(cv.bitwise_and(testlap, overlap)) > 0:
                    print(d_sites[s]["name"], "label clash")
                    continue

                # Shadows
                overlap = cv.add(testlap, overlap)
                if anchor == "lm":
                    draw.text((x + self.config.text_offset[0], y), text, font=self.config.font, anchor=anchor, fill=(0, 0, 0, 255))
                    draw.text((x + self.config.text_offset[0] + textsize[0] / 2, y + textsize[1] / 2), subtext, font=self.config.subfont,
                            anchor="ma", fill=self.config.blur_color)
                else:
                    draw.text((x - self.config.text_offset[0], y), text, font=self.config.font, anchor=anchor, fill=(0, 0, 0, 255))
                    draw.text((x - self.config.text_offset[0] - textsize[0] / 2, y + textsize[1] / 2), subtext, font=self.config.subfont,
                            anchor="ma", fill=self.config.blur_color)

                back = back.filter(ImageFilter.GaussianBlur(radius=3))
                back.alpha_composite(back)
                back.alpha_composite(back)

                # Text
                draw = ImageDraw.Draw(back)
                if anchor == "lm":
                    draw.text((x + self.config.text_offset[0], y), text, font=self.config.font, anchor=anchor, color=label_color)
                    draw.text((x + self.config.text_offset[0] + textsize[0] / 2, y + textsize[1] / 2), subtext, font=subfont,
                            color=label_color, anchor="ma")
                else:
                    draw.text((x - text_offset[0], y), text, font=font, anchor=anchor)
                    draw.text((x - text_offset[0] - textsize[0] / 2, y + textsize[1] / 2), subtext, font=subfont,
                            color=label_color, anchor="ma")
                im.alpha_composite(back)
        """

        print("Preparing final image")
        im = Image.fromarray(self.canvas[:, :, ::-1])
        im = im.convert("RGBA")
        overlap = np.zeros(self.size, dtype="uint8")
        background = Image.new("RGBA", (self.maxx, self.maxy))
        draw = ImageDraw.Draw(background)

        print("Drawing titles")
        title_font = ImageFont.truetype("resources/" + self.config.title_font, self.config.title_size)
        subtitle_font = ImageFont.truetype("resources/" + self.config.subtitle_font, self.config.subtitle_size)
        titlebox = draw.textbbox((0, 0), self.legends.world_translated_name, title_font)
        titlesize = (titlebox[2] - titlebox[0], titlebox[3] - titlebox[1])
        subbox = draw.textbbox((0, 0), self.legends.world_name, subtitle_font)
        subsize = (subbox[2] - subbox[0], subbox[3] - subbox[1])

        title_align = self.config.title_align
        title_adjust = self.config.title_adjust
        if title_align == "tm":
            anchor = "ma"
            (x, y) = (self.maxx / 2, 0 + title_adjust[1])
            (x1, y1) = (x, y + titlesize[1])
        if title_align == "tl":
            anchor = "la"
            (x, y) = (0 + title_adjust[0], 0 + title_adjust[1])
            (x1, y1) = (x + titlesize[0] / 2, y + titlesize[1])
        elif title_align == "tr":
            anchor = "ra"
            (x, y) = (self.maxx - title_adjust[0], 0 + title_adjust[1])
            (x1, y1) = (x - titlesize[0] / 2, y + titlesize[1])
        elif title_align == "bl":
            anchor = "ld"
            (x, y) = (0 + title_adjust[0], self.maxy - title_adjust[1] - subsize[1])
            (x1, y1) = (x + titlesize[0] / 2, y)
        elif title_align == "br":
            anchor = "rd"
            (x, y) = (self.maxx - title_adjust[0], self.maxy - title_adjust[1] - subsize[1])
            (x1, y1) = (x - titlesize[0] / 2, y)

        draw.text((x, y), self.legends.world_translated_name, font=title_font, anchor=anchor, fill=(0, 0, 0, 255))
        draw.text((x1, y1), self.legends.world_name, font=subtitle_font, anchor="ma", fill=self.config.blur_color)
        background = background.filter(ImageFilter.GaussianBlur(radius=3))
        background.alpha_composite(background)
        background.alpha_composite(background)

        draw = ImageDraw.Draw(background)
        draw.text((x, y), self.legends.world_translated_name, font=title_font, anchor=anchor, color=self.config.label_color)
        draw.text((x1, y1), self.legends.world_name, font=subtitle_font, anchor="ma", color=self.config.label_color)

        print("Saving to file...")
        im.alpha_composite(background)
        output_path = "output/"
        im.save(f"{output_path}{self.legends.world_translated_name} - {color_name}.png")
        print("---------------------------")
        print(f"All maps generated for {self.legends.world_translated_name}")
        print("---------------------------")

    def draw_base(self, elevation_file:str, color:dict[int, tuple[int, int, int]]):
        """
        Draw the elevation
        """
        print("Drawing elevation...")
        elevation = self.blue_conversion(cv.imread(elevation_file, cv.IMREAD_COLOR))
        grey = np.uint8(cv.cvtColor(elevation, cv.COLOR_BGR2GRAY))

        self.canvas = cv.merge([self.canvas * color[0][2], self.canvas * color[0][1], self.canvas * color[0][0]])

        kernel = np.ones((3, 3), "uint8")
        contour_color = 0.8
        erode = 2
        dilate = 2
        for i in range(256):
            if self.config.interactive:
                time.sleep(self.config.wait)
            _, thresh = cv.threshold(grey, i, 255, cv.THRESH_BINARY)
            thresh = cv.erode(thresh, kernel, iterations=erode)
            thresh = cv.dilate(thresh, kernel, iterations=dilate)

            if i == 73:
                ground = thresh

            if i in color.keys():
                col = color[i]
                self.canvas = cv.bitwise_and(self.canvas, self.canvas, mask=cv.bitwise_not(thresh))
                cols = cv.merge([thresh / 255 * col[2], thresh / 255 * col[1], thresh / 255 * col[0]])
                self.canvas = cv.add(self.canvas, np.uint8(cols))
                contours, _ = cv.findContours(thresh, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

                if i >= 73:
                    con_col = (
                        int(col[2] * contour_color),
                        int(col[1] * contour_color),
                        int(col[0] * contour_color)
                    )
                    cv.drawContours(self.canvas, contours, -1, con_col, 1)

        return self.canvas, ground, kernel

    def draw_vegetation(self, vegetation_file:str):
        """
        Draw the vegetation
        """
        print("Drawing vegetation...")
        veg = cv.imread(vegetation_file, cv.IMREAD_GRAYSCALE)
        _, veg_mask = cv.threshold(veg, 1, 255, cv.THRESH_BINARY)

        if self.config.vegetation_type == "green":
            veg_overlay = cv.merge(
                [
                    np.uint8((-0.4549 * veg) + 116),
                    np.uint8((-0.3804 * veg) + 172),
                    np.uint8((-0.6118 * veg) + 156)
                ]
            )
            veg_overlay = cv.bitwise_and(veg_overlay, veg_overlay, mask=veg)
        else:
            veg_overlay = cv.merge(
                [
                    np.uint8(veg * (1 - self.config.vegetation_green)),
                    np.uint8(veg * self.config.vegetation_green),
                    np.uint8(veg * (1 - self.config.vegetation_green))
                ]
            )
        veg_top = cv.bitwise_and(self.canvas, self.canvas, mask=veg)
        veg_top = cv.addWeighted(veg_top, 1 - self.config.vegetation_alpha, veg_overlay, self.config.vegetation_alpha, 0)

        self.canvas = cv.bitwise_and(self.canvas, self.canvas, mask=cv.bitwise_not(veg_mask))
        self.canvas = cv.add(self.canvas, veg_top)

    def draw_biomes(self, biome_file:str):
        """
        Draw the biomes
        """
        print("Drawing deserts...")
        biome = cv.imread(biome_file, cv.IMREAD_COLOR)
        desert = np.zeros(biome.shape, dtype="uint8")
        desert[np.where((biome == [32, 96, 255]).all(axis=2))] = [108, 107, 94]  # Badland desert
        desert[np.where((biome == [0, 255, 255]).all(axis=2))] = [82, 142, 206]  # Sand desert
        desert[np.where((biome == [64, 128, 255]).all(axis=2))] = [108, 107, 94]  # Rock desert

        dmask = np.uint8(cv.cvtColor(desert, cv.COLOR_BGR2GRAY))
        dmask[np.where(dmask != 0)] = 255
        desert_top = cv.bitwise_and(self.canvas, self.canvas, mask=dmask)
        desert_top = cv.addWeighted(desert_top, 1 - self.config.desert_alpha, desert, self.config.desert_alpha, 0)

        self.canvas = cv.bitwise_and(self.canvas, self.canvas, mask=cv.bitwise_not(dmask))
        self.canvas = cv.add(self.canvas, desert_top)

        print("Drawing glaciers...")
        glacier = np.zeros(biome.shape, dtype="uint8")
        glacier[np.where((biome == [255, 255, 0]).all(axis=2))] = [255, 255, 255]
        glacier[np.where((biome == [255, 255, 64]).all(axis=2))] = [255, 255, 255]
        glacier[np.where((biome == [255, 255, 128]).all(axis=2))] = [255, 255, 255]
        # glacier = cv.dilate(glacier, kernel, iterations=1)
        # [247,253,254]

        gmask = np.uint8(cv.cvtColor(glacier, cv.COLOR_BGR2GRAY))
        glac_top = cv.bitwise_and(self.canvas, self.canvas, mask=gmask)
        glac_top = cv.addWeighted(glac_top, 1 - self.config.glacier_alpha, glacier, self.config.glacier_alpha, 0)

        self.canvas = cv.bitwise_and(self.canvas, self.canvas, mask=cv.bitwise_not(gmask))
        self.canvas = cv.add(self.canvas, glac_top)

    def draw_water(self, water_file:str, color:dict[int, tuple[int, int, int]]):
        """
        Draw water
        """
        print("Drawing water...")
        water = cv.imread(water_file, cv.IMREAD_COLOR)

        rivers = np.zeros(self.size, dtype="uint8")
        rivers[np.where((water == [255, 96, 0]).all(axis=2))] = [255]  # lake
        rivers[np.where((water == [255, 112, 0]).all(axis=2))] = [255]  # ocean river
        rivers[np.where((water == [255, 128, 0]).all(axis=2))] = [255]  # major river
        rivers[np.where((water == [255, 160, 0]).all(axis=2))] = [255]  # river
        rivers[np.where((water == [255, 192, 0]).all(axis=2))] = [255]  # minor river
        rivers[np.where((water == [255, 224, 0]).all(axis=2))] = [255]  # stream
        if self.config.brook:
            rivers[np.where((water == [255, 255, 0]).all(axis=2))] = [255]  # brook

        ret, riv_mask = cv.threshold(rivers, 1, 255, cv.THRESH_BINARY)
        self.canvas = cv.bitwise_and(self.canvas, self.canvas, mask=cv.bitwise_not(riv_mask))

        col = color[72]
        rivers = cv.merge([riv_mask / 255 * col[2], riv_mask / 255 * col[1], riv_mask / 255 * col[0]])
        self.canvas = cv.add(np.uint8(self.canvas), np.uint8(rivers))

    def draw_territory(self):
        """
        Draw territory
        """
        d_sites = self.legends.d_sites
        occ_sites = self.legends.occ_sites
        entities = self.legends.entities
        active_wars = self.legends.active_wars
        if len(occ_sites) == 0 or len(entities) == 0:
            print("No territory to draw")
            return
        print(f"Drawing { len(occ_sites) } territories...")
        k = cv.getStructuringElement(cv.MORPH_ELLIPSE, (15, 15))

        # VORONOI TERRITORY 2 ELECTRIC BOOGALGOO
        delauny = np.zeros(self.size, dtype="uint8")
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

        rect = (0, 0, self.maxy, self.maxx)
        subdiv = cv.Subdiv2D(rect)
        for p in pts:
            subdiv.insert(p)

        (facets, centers) = subdiv.getVoronoiFacetList([])
        for i in range(0, len(facets)):
            ifacet_arr = []
            for f in facets[i]:
                ifacet_arr.append(f)

            ifacet = np.array(ifacet_arr, np.intc)
            color = (rulers[i], rulers[i], rulers[i])

            cv.fillConvexPoly(delauny, ifacet, color, cv.LINE_4, 0)

        facets = []
        for i in range(0, max(rulers) + 1):
            vp = np.zeros(self.size, dtype="uint8")
            vp[np.where((delauny == [i, i, i]).all(axis=2))] = [255]  # entity_colors[i]
            facets.append(vp)

        terrs = []
        disp = []
        for e in entities:
            terr = np.zeros(self.size, dtype="uint8")
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

            terr = cv.bitwise_and(terr, terr, mask=self.ground)
            terr_top = cv.bitwise_and(self.canvas, self.canvas, mask=terr)
            if i >= len(self.config.entity_colors):
                print("Error: Not enough colors in entity_colors")
                i = i % len(self.config.entity_colors)
            terr_overlay = np.ones(self.size, dtype="uint8") * [self.config.entity_colors[i][2], self.config.entity_colors[i][1],
                                                                    self.config.entity_colors[i][0]]
            terr_overlay = cv.bitwise_and(terr_overlay, terr_overlay, mask=terr).astype(np.uint8)

            terr_top = cv.addWeighted(terr_top, 1 - self.config.terr_alpha, terr_overlay, self.config.terr_alpha, 0)

            self.canvas = cv.bitwise_and(self.canvas, self.canvas, mask=cv.bitwise_not(terr))
            self.canvas = cv.add(self.canvas, terr_top)
        #    i = i + 1
        #################################################################################
        diag_width = 1
        diag_space = 0

        outerlay = np.zeros(self.size, dtype="uint8")
        outermask = np.zeros(self.size, dtype="uint8")
        for i, terr in enumerate(terrs):
            c1 = int(list(entities)[i])

            diag = np.zeros(self.size, dtype="uint8")
            for d in range(0, 2 * self.maxx, len(disp) * (diag_width + diag_space)):
                cv.line(diag, (self.maxy, d - self.maxx + i * (diag_width + diag_space)), (0, d + i * (diag_width + diag_space)),
                        255, diag_width)

            for j, uerr in enumerate(disp):
                c2 = int(list(entities)[j])
                m = 0
                if (c1 in active_wars and c2 in active_wars[c1]) or (c2 in active_wars and c1 in active_wars[c2]):
                    inter = cv.bitwise_and(disp[i], disp[j])
                    m = cv.countNonZero(inter)
                if m > 0:
                    if i >= len(entity_colors):
                        i = i % len(entity_colors)
                    overlay = np.ones(size, dtype="uint8") * [entity_colors[i][2], entity_colors[i][1],
                                                                        entity_colors[i][0]]
                    mask = cv.bitwise_and(inter, diag)
                    overlay = cv.bitwise_and(overlay, overlay, mask=mask).astype(np.uint8)

                    eiag = np.zeros(size, dtype="uint8")
                    for d in range(0, 2 * maxx, len(terrs) * (diag_width + diag_space)):
                        cv.line(eiag, (maxy, d - maxx + j * (diag_width + diag_space)),
                                (0, d + j * (diag_width + diag_space)), 255, diag_width)

                    if j >= len(entity_colors):
                        j = j % len(entity_colors)

                    everlay = np.ones(size, dtype="uint8") * [entity_colors[j][2], entity_colors[j][1],
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

            overlay = np.ones(size, dtype="uint8") * [entity_colors[i][2], entity_colors[i][1],
                                                                entity_colors[i][0]]
            overlay = cv.bitwise_and(overlay, overlay, mask=edges).astype(np.uint8)
            canv = cv.bitwise_and(canv, canv, mask=cv.bitwise_not(edges))
            canv = cv.add(canv, overlay)

    def blue_conversion(self, img: cv.Mat):
        """TODO: add a description for this function"""
        mask = img[:, :, 2] == 0
        grey_value = img[mask, 0] * 0.73
        img[mask, 0] = grey_value
        img[mask, 1] = grey_value
        img[mask, 2] = grey_value
        return img

    def display(self, img):
        """TODO: add description"""
        cv.namedWindow("output", cv.WINDOW_NORMAL)
        cv.imshow("output", img)
        while True:
            key = cv.waitKey(500)
            if key > 0:
                break
        cv.destroyWindow("output")

    def display_thread(self):
        """TODO: add description"""
        cv.namedWindow("output", cv.WINDOW_NORMAL)
        while True:
            cv.imshow("output", self.canvas)
            if cv.waitKey(500) & 0xFF == ord('q'):
                break
        cv.destroyWindow("output")
