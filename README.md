# Farming Simulator Tools

** BACK UP YOUR MAP BEFORE FIRST RUN ** 
Not responsible for any lost work/data, this has been tested to some extent, but I cannot guarantee it won't cause some issues with your i3d file as it does overwrite it with one it creates.

## Notice
these tools are in development, they will have bugs, the bugs can be created on GitHub issues

**These tools are not intended for users of the map, they are for creating/modifying maps**. specific
workflows utilizing QGIS are the intended target of this project

#### Abstract
this tool is intended to provide useful tools for working with GiantsEditor

#### Forest Generator
using rasters and a combination of shapefiles, forests can be automatically created (or re-created) within minutes
this requires two main things in the i3d file:
1. a transform group called `baseTrees` that contains template transform groups to use
1. a transform group called `autoForests` this will be _overwritten_ with the forest data
    **any changes within autoForests will be overwritten if you run the script again**

baseTrees should have the following structure:
```
baseTrees
  - basePine
    - pine_stage1
    - pine_stage2
    ...
  - baseSpruce
    - spruce_stage1
    ...
```

### Tutorial
see the corresponding tutorial documentation for how to get started:
[Forest Generation](fstools/tutorial/forests/forest_tutorial.md)