"""Make every shipped PandaQuest texture loadable on OctoWoW.

Two client limits (diagnostics knowledge records texture.power_of_two_required
and texture.large_dimensions): width and height must be powers of two, and
neither may exceed 512 px. Nothing here rescales, filters, quantizes or
recompresses a pixel. A texture is either padded with transparent texels
(its art stays at the top-left, Lua crops it with SetTexCoord), repacked as
exact atlas cells, or split into exact tiles. Every written region is decoded
again and compared with its source, all four channels.

Run it from the addon root after any media import or generator
(make_quest_tracker_art.py writes the 1024x512 Forever sheet that this splits):

    python tools/make_client_safe_textures.py

A second run changes nothing. The Lua coordinates live in
Compatibility/ClientAPI.lua: Client.TEXTURE_CROP, TrackerArt.pieces,
QuestLogSkin.skins, TrackerArt.foldHoverCell and STANDALONE_QUEST_LOG.pages.
"""

import math
import os
import sys

from PIL import Image

MAX_SIDE = 512
TEXTURES = os.path.join("media", "Textures")

# Small art padded to the next power of two (Client.TEXTURE_CROP).
PADDED = [
    os.path.join("Flags", "cn.tga"),
    os.path.join("Flags", "en.tga"),
    os.path.join("Flags", "fr.tga"),
    os.path.join("Flags", "ru.tga"),
    os.path.join("HUD", "NavigationArc.tga"),
    os.path.join("Map", "Pins", "ActiveQuestIcon.tga"),
    os.path.join("Map", "Pins", "CompleteQuestIcon.tga"),
    os.path.join("Map", "Pins", "QuestIcon-lowlvl.tga"),
    os.path.join("Map", "Pins", "questIcon.tga"),
    os.path.join("Tracker", "following-arrow.tga"),
    os.path.join("Tracker", "quest-marker.tga"),
    os.path.join("Tracker", "search-icon.tga"),
]

# 128RedButton (512x2048): each used cell with a one-texel apron of its source
# neighbours, so bilinear sampling at a cell edge reads what it read before.
# Bars keep x; each state's row starts at 128 * state + 1; caps move to x 300.
RED_BUTTON = os.path.join("QuestLog", "128RedButton.tga")
RED_CELLS = [
    ("normal bar", (0, 522, 293, 649), (0, 0)),
    ("normal cap", (391, 912, 433, 1039), (299, 0)),
    ("hover bar", (0, 782, 293, 909), (0, 128)),
    ("hover cap", (377, 1042, 419, 1169), (299, 128)),
    ("disabled bar", (0, 652, 293, 779), (0, 256)),
    ("disabled cap", (261, 1042, 303, 1169), (299, 256)),
    ("glow", (14, 417, 425, 491), (14, 384)),
]

# 128GoldRedButton (512x1024): bar and short button share each row, so whole
# rows move with x unchanged; each state's row starts at 128 * state + 1.
GOLD_BUTTON = os.path.join("QuestLog", "128GoldRedButton.tga")
GOLD_CELLS = [
    ("normal row", (0, 522, 512, 649), (0, 0)),
    ("disabled row", (0, 652, 512, 779), (0, 128)),
    ("pressed row", (0, 782, 512, 909), (0, 256)),
    ("glow rows", (0, 389, 512, 491), (0, 384)),
]

# Quest Log pages: the visible art (the rest of each canvas is transparent
# padding) cut into tiles of at most TILE_STEP texels, each carrying a
# one-texel apron of its neighbours on every inner edge. Tile c-r is saved as
# <name>-<c>-<r>.tga; STANDALONE_QUEST_LOG.pages repeats this rule.
TILE_STEP = 510
QUEST_LOG_PAGES = [
    (os.path.join("QuestLog", "QuestLogPageLeft.tga"), (896, 896), (896, 823)),
    (os.path.join("QuestLog", "QuestLogPageRight.tga"), (448, 896), (298, 823)),
]

# The Forever tracker sheet (1024x512). Every piece the tracker uses except the
# three wide rails lies in its right half, which becomes the sheet itself.
# The rails are wider than 512, so each is cut at its centre into two halves
# (TrackerArt.pieces.*Left / *Right) packed with one-texel aprons into
# QuestTrackerRails.tga.
TRACKER_SHEET = os.path.join("Tracker", "QuestTrackerSheet.tga")
TRACKER_RAILS = os.path.join("Tracker", "QuestTrackerRails.tga")
TRACKER_RAIL_PIECES = [
    ("header", 20, 247, 551, 71),
    ("zone", 25, 335, 546, 48),
    ("goldLine", 1, 385, 710, 11),
]


def power_of_two(value):
    result = 1
    while result < value:
        result *= 2
    return result


def load(path):
    with Image.open(path) as opened:
        return opened.convert("RGBA")


def tga_type(path):
    with open(path, "rb") as handle:
        return handle.read(3)[2]


def save(image, path, rle):
    if image.size[0] > MAX_SIDE or image.size[1] > MAX_SIDE:
        raise ValueError("refusing to write %s at %s" % (path, image.size))
    if image.size != (power_of_two(image.size[0]), power_of_two(image.size[1])):
        raise ValueError("refusing to write non power of two %s" % path)
    image.save(path, format="TGA", compression="tga_rle" if rle else None)
    with open(path, "rb") as handle:
        header = handle.read(18)
    if (len(header) != 18 or header[2] != (10 if rle else 2)
            or header[16] != 32 or header[17] != 8):
        raise ValueError("unexpected TGA encoding: " + path)
    written = load(path)
    if written.tobytes() != image.tobytes():
        raise ValueError("decoded pixels differ: " + path)


def same(source, box, output, xy, label):
    width, height = box[2] - box[0], box[3] - box[1]
    if (source.crop(box).tobytes()
            != output.crop((xy[0], xy[1], xy[0] + width, xy[1] + height)).tobytes()):
        raise ValueError("pixel verification failed: " + label)


def pack(source, size, cells):
    output = Image.new("RGBA", size, (0, 0, 0, 0))
    for label, box, xy in cells:
        output.paste(source.crop(box), xy)
    for label, box, xy in cells:
        same(source, box, output, xy, label)
    return output


def pad(root, relative, changed):
    path = os.path.join(root, relative)
    source = load(path)
    width, height = source.size
    target = (power_of_two(width), power_of_two(height))
    if target == source.size:
        return
    output = Image.new("RGBA", target, (0, 0, 0, 0))
    output.paste(source, (0, 0))
    same(source, (0, 0, width, height), output, (0, 0), relative)
    save(output, path, tga_type(path) == 10)
    changed.append("padded   %-36s %dx%d -> %dx%d crop %s, %s"
                   % (relative, width, height, target[0], target[1],
                      fraction(width, target[0]), fraction(height, target[1])))


def fraction(value, whole):
    return "1" if value == whole else "%d / %d" % (value, whole)


def repack(root, relative, expected, cells, changed):
    path = os.path.join(root, relative)
    source = load(path)
    if source.size == (MAX_SIDE, MAX_SIDE):
        return
    if source.size != expected:
        raise ValueError("unexpected size %s for %s" % (source.size, relative))
    save(pack(source, (MAX_SIDE, MAX_SIDE), cells), path, True)
    changed.append("repacked %-36s %dx%d -> 512x512"
                   % (relative, expected[0], expected[1]))


def tiles(width, height):
    for row in range(int(math.ceil(height / float(TILE_STEP)))):
        for column in range(int(math.ceil(width / float(TILE_STEP)))):
            left, top = column * TILE_STEP, row * TILE_STEP
            right = min(width, left + TILE_STEP)
            bottom = min(height, top + TILE_STEP)
            yield column, row, (left, top, right, bottom)


def split_page(root, relative, expected, visible, changed):
    path = os.path.join(root, relative)
    base = os.path.splitext(path)[0]
    if not os.path.isfile(path):
        for column, row, _ in tiles(visible[0], visible[1]):
            if not os.path.isfile("%s-%d-%d.tga" % (base, column, row)):
                raise ValueError("missing quest log tile for " + relative)
        return
    source = load(path)
    if source.size != expected:
        raise ValueError("unexpected size %s for %s" % (source.size, relative))
    if source.crop((0, visible[1]) + source.size).getbbox() is not None or (
            visible[0] < source.size[0]
            and source.crop((visible[0], 0) + source.size).getbbox() is not None):
        raise ValueError("art outside the visible area of " + relative)
    for column, row, (left, top, right, bottom) in tiles(visible[0], visible[1]):
        # The apron reaches into the transparent padding on the outer edges too.
        box = (max(0, left - 1), max(0, top - 1),
               min(source.size[0], right + 1), min(source.size[1], bottom + 1))
        size = (power_of_two(box[2] - box[0]), power_of_two(box[3] - box[1]))
        output = pack(source, size, [("tile %d-%d" % (column, row), box, (0, 0))])
        tile = "%s-%d-%d.tga" % (base, column, row)
        save(output, tile, True)
        changed.append("tiled    %-36s %d,%d %dx%d (content at %d,%d)"
                       % (os.path.relpath(tile, root), left, top, right - left,
                          bottom - top, left - box[0], top - box[1]))
    os.remove(path)
    changed.append("removed  " + relative)


def split_tracker(root, changed):
    path = os.path.join(root, TRACKER_SHEET)
    source = load(path)
    if source.size == (MAX_SIDE, MAX_SIDE):
        if not os.path.isfile(os.path.join(root, TRACKER_RAILS)):
            raise ValueError("missing " + TRACKER_RAILS)
        return
    if source.size != (1024, 512):
        raise ValueError("unexpected size %s for %s" % (source.size, TRACKER_SHEET))
    cells = []
    lua = []
    top = 0
    for name, x, y, width, height in TRACKER_RAIL_PIECES:
        middle = x + width / 2.0
        for side, start, end in (("Left", x, middle), ("Right", middle, x + width)):
            box = (int(math.floor(start)) - 1, y - 1,
                   int(math.ceil(end)) + 1, y + height + 1)
            box = (max(0, box[0]), max(0, box[1]),
                   min(source.size[0], box[2]), min(source.size[1], box[3]))
            cells.append((name + side, box, (0, top)))
            lua.append("%s%s = { %s, %s, %s, %d, \"rails\" },"
                       % (name, side, number(start - box[0]), number(top + y - box[1]),
                          number(end - start), height))
            top += box[3] - box[1]
    save(pack(source, (MAX_SIDE, power_of_two(top)), cells),
         os.path.join(root, TRACKER_RAILS), True)
    save(pack(source, (MAX_SIDE, MAX_SIDE),
              [("right half", (512, 0, 1024, 512), (0, 0))]), path, True)
    changed.append("split    %s 1024x512 -> right half 512x512 (x - 512)"
                   % TRACKER_SHEET)
    changed.append("packed   %s 512x%d:" % (TRACKER_RAILS, power_of_two(top)))
    changed.extend("           " + line for line in lua)


def number(value):
    return ("%g" % value)


def audit(root):
    problems = []
    for folder, _, names in os.walk(os.path.join(root, "media")):
        for name in names:
            if not name.lower().endswith((".tga", ".blp")):
                continue
            path = os.path.join(folder, name)
            with Image.open(path) as opened:
                width, height = opened.size
            if (width > MAX_SIDE or height > MAX_SIDE
                    or width != power_of_two(width) or height != power_of_two(height)):
                problems.append("%s %dx%d" % (os.path.relpath(path, root), width, height))
    return problems


def main():
    root = os.getcwd()
    if not os.path.isfile(os.path.join(root, "pandaQuest.toc")):
        sys.exit("run from the pandaQuest addon root")
    textures = os.path.join(root, TEXTURES)
    changed = []
    for relative in PADDED:
        pad(textures, relative, changed)
    repack(textures, RED_BUTTON, (512, 2048), RED_CELLS, changed)
    repack(textures, GOLD_BUTTON, (512, 1024), GOLD_CELLS, changed)
    for relative, expected, visible in QUEST_LOG_PAGES:
        split_page(textures, relative, expected, visible, changed)
    split_tracker(textures, changed)
    for line in changed:
        print(line)
    problems = audit(root)
    for problem in problems:
        print("NOT CLIENT SAFE " + problem)
    print("%d change(s); %d texture(s) outside the client limits"
          % (len(changed), len(problems)))
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
