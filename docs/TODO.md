# Parameters
-h --help
-d --debug
-n --new={color|parameters}
-i --interactive
-p --parameters={file}
-f --font={file}
-c --color={color_name}
-v --vegetation={default,green}
-g --grid
-b --brook
-t --territory
-s --structure
-r --road
-i --input{folder}
-o --output{folder|file}

# Files
init:
- if main with command parsing
- expose re-usable functions
world/parser:
- parses legend files
map/generate:
map/utils:
color/read:
color/create:
parameters/read:
parameters/create:

# Base Pseudo Code
1. Parse Command Parameters

## Map Generations
2. Parse World Parameters
    - Read XML
    - Read World Name
    - Identify Map Files

### Non-interactive
3. Generate Map
4. Save/Show Map

### Interactive
3. Generate Map
4. Save/Show Map

## Color Palette Generation


## Parameters File Generation


# TO-DO List

