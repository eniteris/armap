# armap
Automated map maker from Dwarf Fortress maps

## How it works
* Export all maps, xml and txt files for the desired world to a folder within /Map Data.
* Running the script will work through each folder in /Map Data and generate the final PNG file in /Maps.
* /Map Data/Complete will be ignored in the folder search so you can move completed Map Data folders there.
* All palette options will be generated, for the moment simply comment out the unwanted palettes in the palette dictionary.

## What is needed
The maps that are required are:
* Elevation
* Biome
* Vegetation
* Hydrosphere
* Structure

The exportlegends.lua is an edited script file for DF Hacks that will export all the necessary files. The added command is "exportlegends armaps".

## How to customize
Most parameters are in the beginning of the program, including various alternate color schemes.

Code is ultimate spaghetti. Observe at your own risk.

## Examples
![example map](/examples/carte-color-palette.png?raw=true)

You can find more examples at the example folder