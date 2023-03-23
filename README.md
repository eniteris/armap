# armap
Automated map maker from Dwarf Fortress maps

* Export all maps and xml and txt files for each world to a folder within /Map Data.
* Running the script will work through each folder in /Map Data and generate the final PNG file in /Maps.
* /Map Data/Complete will be ignored in the folder search so you can move completed Map Data folders there.
* All palette options will be generated, for the moment simply comment out the unwanted palettes in the palette dictionary.

The maps that are required are:
* Elevation
* Biome
* Vegetation
* Hydrosphere
* Structure

The exportlegends.lua is an edited script file for DF Hacks that will export all the necessary files. The added command is "exportlegends armaps".

Most parameters are in the beginning of the program, including various alternate color schemes.

Code is ultimate spaghetti. Observe at your own risk.

![example map](https://github.com/Myckou/armap/blob/eb52067b8839ae3dc281c8afdb9e8e5e0141ab2a/map.png?raw=true)
