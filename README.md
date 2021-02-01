**ABOUT**

This is a randomizer for Bravely Default: Where the Fairy Flies and
Bravely Second: End Layer. It has been built and tested only on North
American releases.

**OPTIONS**

Several options are available:

- Shuffle job abilities (commands, spells, and support skills).

- Random job specialties

- Shuffle job stats ("affinities")

- QOL: Scale experience, JP, and pg earned from battles.

Several options are only available to specific games (unfortunatly).

- Shuffle treasure chests and hidden items (only Bravely Default)

- Shuffle job equipment stats ("aptitudes") (only Bravely Second)

**USAGE**

To run the executable from the Releases page, it is assumed that you
have [extracted RomFS from your
cartridge](https://gist.github.com/PixelSergey/73d0a4bc1437dbaa53a1d1ce849fdda1).
It will not work with `*.3ds`, `*.cia`, etc. files. The executable
requires that you input the path to (and including) the folder
`romfs`.

The executable outputs a directory entitled
```patch_<game>_<number>```, e.g. ```patch_BD_42``` is an output for
Bravely Default with seed 42. This folder contains a spoiler log, a
file `settings.json`, and a folder `romfs`. The settings file is a
record of selected options. The `romfs` folder is the patch generated
for your game. It can be run on your console with [Luma
LayeredFS](https://gist.github.com/PixelSergey/5dbb4a9b90d290736353fa58e4fcbb42).
