"""Build PandaQuest's Database/ from the Vanilla snapshot plus the Turtle WoW overlay.

PandaQuest ships ONE merged world database. It is built offline, here, from two
read-only inputs, and never assembled at runtime:

  * the Vanilla snapshot of PandaQuest 0.5.2's own Database/ folder
    (#Addons-dev/references/PandaQuest_Vanilla_DB_0.5.2): pfQuest's packaging
    of the VMaNGOS world database plus PandaQuest's own VMaNGOS extracts
    (quest XP/reputation, trainers, patrols, instance provenance);
  * Rivi's pfQuest-turtle overlay, repackaged for PandaQuest
    (#Addons-dev/references/PandaQuest_Turtle_DB_Rivi_1.0.38_Ready).

Always merge FROM the snapshot. The addon's Database/ folder holds the merged
output, and merging Turtle onto it again would apply the overlay twice.

The overlay follows pfQuest's own rules: a Turtle row replaces the whole
Vanilla row and the string "_" deletes it. Rivi's two hand-maintained
correction scripts (feature-compat-turtle.lua, overwrites-turtle.lua) are Lua
code, so they are executed unchanged in a Lua 5.1 runtime (lupa) before the
merge, exactly as the overlay's own loader would have run them in game.

On top of the plain merge this tool keeps every PandaQuest feature fed:

  * quests[id].xp / .rep (PandaQuest's VMaNGOS reward sync) are carried onto a
    Turtle row of the same quest when its level is unchanged;
  * translated text: a Turtle translation wins; a Vanilla translation is kept
    only while the English row it translates is unchanged; a Turtle "
    translation" identical to the English text is a placeholder and dropped.
    The quest-log language flags read exactly this (Data/Database.lua
    GetQuestTextForLanguage), so a Turtle quest offers no French flag;
  * derived tables keyed by Vanilla IDs (trainers, patrols, instance
    provenance, dungeon-approach reviews, sell prices) are pruned of IDs Turtle
    deleted or moved;
  * locales stay enUS, esES, frFR, ruRU, zhCN (deDE and ptBR are not shipped);
  * Turtle-only metadata no PandaQuest code reads (quests_patch, units_patch,
    quests_requireClientCompletion, quests_talkObjectives,
    questProfessionRequirements, quests[id].repeatable) is not shipped.

Memory: rows are written with positional list constructors, so coordinate and
route lists live in the Lua array part instead of the hash part, and empty item
rows and exact duplicate spawn points are not written. Every field PandaQuest
reads keeps its shape; see docs/TURTLE-DB.md.

Run with a Python that has lupa (Lua 5.1), e.g.:

    py -3.10 -B tools/import_turtle_db.py            # write Database/ + report
    py -3.10 -B tools/import_turtle_db.py --dry-run  # report only
"""
import argparse
import difflib
import json
import os
import re
import shutil
import sys

try:
    from lupa import lua51
except ImportError:  # pragma: no cover - environment guard
    sys.exit("lupa with Lua 5.1 is required: run with a Python that has lupa (py -3.10)")

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.dirname(HERE)
GAME = os.path.dirname(os.path.dirname(os.path.dirname(ADDON)))
REFERENCES = os.path.join(GAME, "#Addons-dev", "references")
DEFAULT_VANILLA = os.path.join(REFERENCES, "PandaQuest_Vanilla_DB_0.5.2")
DEFAULT_TURTLE = os.path.join(REFERENCES, "PandaQuest_Turtle_DB_Rivi_1.0.38_Ready")
DEFAULT_OUT = os.path.join(ADDON, "Database")
DEFAULT_REPORT = os.path.join(HERE, "turtle_import_report.json")

TURTLE_SOURCE = "pfQuest-turtle 1.0.38 by Rivi (MIT), https://github.com/rivi-s/pfQuest-turtle"
LOCALES = ("enUS", "esES", "frFR", "ruRU", "zhCN")
TRANSLATED = ("esES", "frFR", "ruRU", "zhCN")
TEXT_KINDS = ("quests", "units", "objects", "items", "zones", "professions")
# Merged with the plain pfQuest rule (whole-row replace, "_" deletes).
DATA_TABLES = ("items", "units", "objects", "refloot", "quests-itemreq", "quests",
               "zones", "minimap", "areatrigger", "meta")
# PandaQuest-curated files copied verbatim from the Vanilla snapshot.
CURATED_FILES = ("instances.lua", "factions.lua", "dungeon_approach_units.lua")
# Fields a Turtle row may carry that nothing in PandaQuest reads.
UNREAD_QUEST_FIELDS = (b"repeatable",)
# Vanilla-only fields PandaQuest added from VMaNGOS; carried onto Turtle rows.
CARRIED_QUEST_FIELDS = (b"xp", b"rep")
GM_ONLY_NAME = re.compile(rb"\(Only GM can see it\)", re.I)
# A patrol is kept for a Turtle-replaced creature only while one of its spawns
# lies in a zone of the route, within this many map percent of a route point.
PATROL_MATCH_DISTANCE = 10.0
# Quest translation is kept when the English title is unchanged and the
# objective / description text changed no more than this (difflib ratio).
QUEST_OBJECTIVE_RATIO = 0.9
QUEST_DESCRIPTION_RATIO = 0.8

LUA_KEYWORDS = {b"and", b"break", b"do", b"else", b"elseif", b"end", b"false", b"for",
                b"function", b"if", b"in", b"local", b"nil", b"not", b"or", b"repeat",
                b"return", b"then", b"true", b"until", b"while"}
IDENT = re.compile(rb"^[A-Za-z_][A-Za-z0-9_]*$")

PFQUEST_HEADER = (
    "-- PandaQuest bundled world data. GENERATED by tools/import_turtle_db.py; do not edit.\n"
    "-- Vanilla: the VMaNGOS world database as packaged by pfQuest (MIT, Eric Mauser / Shagu).\n"
    "-- Turtle WoW 1.18.1: " + TURTLE_SOURCE + ".\n"
    "-- See Database/CREDITS.md and LICENSE in the addon root.\n"
)
VMANGOS_HEADER = (
    "-- PandaQuest bundled world data. GENERATED by tools/import_turtle_db.py; do not edit.\n"
    "-- Extracted from VMaNGOS db-sqlite-6958f26 (Vanilla 1.12.1), pruned to the\n"
    "-- creatures that still exist unchanged in the Turtle WoW 1.18.1 data\n"
    "-- (" + TURTLE_SOURCE + ").\n"
    "-- See Database/CREDITS.md.\n"
)
TABLE_NOTES = {
    "quests": (
        "-- Quest XP/reputation rewards synchronized from VMaNGOS revision 6958f26, Vanilla patch 10 (1.12.1);\n"
        "-- carried onto a Turtle quest only when its level is unchanged.\n"
        "-- [\"xp\"] = base RewXP; [\"rep\"] = flat { factionId, value, ... } direct quest reputation rewards.\n"
    ),
    "trainers": (
        "-- Locale-independent trainer metadata.\n"
        "-- Names come from Database/<locale>/units.lua.\n"
        "-- Locations come from the full Database/units.lua record for the same NPC ID.\n"
        "-- record: { trainer_type, trainer_class, trainer_race, trainer_spell, trainer_id }\n"
        "-- trainer_type: 0=class, 1=mount, 2=profession/tradeskill, 3=pet.\n"
    ),
    "waypoint_index": (
        "-- Lightweight NPC -> open-world patrol route index.\n"
        "-- group: 0=Eastern Kingdoms, 1=Kalimdor.\n"
        "-- Battleground and instance patrols are intentionally excluded.\n"
        "-- Values are route IDs stored in Database/Waypoints/*.lua.\n"
    ),
    "instance_only_units": (
        "-- Instance-only creature provenance for Vanilla 1.12.1.\n"
        "-- Generated from: VMaNGOS mangos.sqlite / db-sqlite-6958f26.zip, revision 6958f26, 2026-08-22; latest migration 20260822042038.\n"
        "-- A creature appears here only when every active spawn is on a listed\n"
        "-- dungeon or raid map. Values record all source instance map IDs.\n"
        "-- Creatures Turtle deleted, or gave a spawn in a new area, are removed.\n"
    ),
}


# Lua -> Python -------------------------------------------------------------

def to_python(value, lua_type):
    kind = lua_type(value)
    if kind != "table":
        return value
    out = {}
    for key, item in value.items():
        out[key] = to_python(item, lua_type)
    return out


def run_file(lua, path):
    with open(path, "rb") as handle:
        source = handle.read()
    lua.execute(source)


def lua_files(folder):
    found = []
    for root, _, files in os.walk(folder):
        for name in files:
            if name.endswith(".lua"):
                found.append(os.path.join(root, name))
    return sorted(found)


def load_inputs(vanilla_dir, turtle_dir):
    lua = lua51.LuaRuntime(encoding=None)
    lua_type = lua51.lua_type
    lua.execute("PandaQuestData = {}")
    for path in lua_files(vanilla_dir):
        run_file(lua, path)
    special = ("feature-compat-turtle.lua", "overwrites-turtle.lua", "turtle-overlay-apply.lua")
    for path in lua_files(turtle_dir):
        if os.path.basename(path) not in special:
            run_file(lua, path)
    # Rivi's corrections, in the order TOC_INCLUDE_AFTER_VANILLA.txt loads
    # them, against the untouched Vanilla tables they expect as `base`.
    run_file(lua, os.path.join(turtle_dir, "feature-compat-turtle.lua"))
    run_file(lua, os.path.join(turtle_dir, "overwrites-turtle.lua"))
    globals_ = lua.globals()
    vanilla = {}
    for key, value in globals_.PandaQuestData.items():
        vanilla[key.decode("latin-1")] = to_python(value, lua_type)
    turtle = {}
    for key, value in globals_.PandaQuestTurtleDB.items():
        turtle[key.decode("latin-1")] = to_python(value, lua_type)
    return vanilla, turtle


# Text comparison ----------------------------------------------------------

WHITESPACE = re.compile(rb"\s+")
TOKEN = re.compile(rb"\$([A-Za-z])")


def norm_text(value):
    if not isinstance(value, bytes):
        return b""
    value = WHITESPACE.sub(b" ", value).strip()
    return TOKEN.sub(lambda match: b"$" + match.group(1).upper(), value)


def ratio(left, right):
    left, right = norm_text(left), norm_text(right)
    if left == right:
        return 1.0
    return difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()


def same_quest_text(old, new):
    if not isinstance(old, dict) or not isinstance(new, dict):
        return False
    if norm_text(old.get(b"T")) != norm_text(new.get(b"T")):
        return False
    if ratio(old.get(b"O"), new.get(b"O")) < QUEST_OBJECTIVE_RATIO:
        return False
    return ratio(old.get(b"D"), new.get(b"D")) >= QUEST_DESCRIPTION_RATIO


def same_text(kind, old, new):
    if kind == "quests":
        return same_quest_text(old, new)
    return isinstance(old, bytes) and isinstance(new, bytes) and norm_text(old) == norm_text(new)


def identical_text(kind, left, right):
    """A Turtle 'translation' that is just the English row again."""
    if kind == "quests":
        if not isinstance(left, dict) or not isinstance(right, dict):
            return False
        return all(norm_text(left.get(f)) == norm_text(right.get(f)) for f in (b"T", b"O", b"D"))
    return isinstance(left, bytes) and isinstance(right, bytes) and norm_text(left) == norm_text(right)


# Merge --------------------------------------------------------------------

def overlay(base, additions):
    merged = dict(base or {})
    deleted, replaced, added = set(), set(), set()
    for key, value in (additions or {}).items():
        if value == b"_":
            if key in merged:
                deleted.add(key)
            merged.pop(key, None)
        else:
            if key in merged:
                replaced.add(key)
            else:
                added.add(key)
            merged[key] = value
    return merged, deleted, replaced, added


def merge_data(vanilla, turtle, report):
    data = {}
    changes = {}
    for name in DATA_TABLES:
        merged, deleted, replaced, added = overlay(vanilla.get(name), turtle.get(name))
        data[name] = merged
        changes[name] = {"deleted": deleted, "replaced": replaced, "added": added}
        report["tables"][name] = {
            "vanilla": len(vanilla.get(name) or {}), "turtle_rows": len(turtle.get(name) or {}),
            "deleted": len(deleted), "replaced": len(replaced), "added": len(added),
            "merged": len(merged),
        }
    return data, changes


def carry_quest_fields(vanilla, data, changes, report):
    carried = 0
    level_changed = []
    for quest_id in changes["quests"]["replaced"]:
        old, new = vanilla["quests"][quest_id], data["quests"][quest_id]
        if not isinstance(old, dict) or not isinstance(new, dict):
            continue
        if not any(field in old for field in CARRIED_QUEST_FIELDS):
            continue
        if old.get(b"lvl") != new.get(b"lvl"):
            level_changed.append(quest_id)
            continue
        new = dict(new)
        for field in CARRIED_QUEST_FIELDS:
            if field in old and field not in new:
                new[field] = old[field]
        data["quests"][quest_id] = new
        carried += 1
    unread = 0
    for quest_id, record in list(data["quests"].items()):
        if isinstance(record, dict) and any(f in record for f in UNREAD_QUEST_FIELDS):
            record = dict((k, v) for k, v in record.items() if k not in UNREAD_QUEST_FIELDS)
            data["quests"][quest_id] = record
            unread += 1
    report["quests"] = {
        "rewardsCarried": carried,
        "rewardsDroppedLevelChanged": len(level_changed),
        "rewardsDroppedLevelChangedIds": sorted(level_changed),
        "unreadFieldsRemoved": unread,
    }


def merge_texts(vanilla, turtle, report):
    texts = {}
    stats = {}
    for kind in TEXT_KINDS:
        english_key = kind + "_enUS"
        vanilla_en = vanilla.get(english_key) or {}
        merged_en, deleted_en, _, _ = overlay(vanilla_en, turtle.get(english_key))
        texts[english_key] = merged_en
        changed = set()
        for key, value in merged_en.items():
            if key in vanilla_en and not same_text(kind, vanilla_en[key], value):
                changed.add(key)
        stats[english_key] = {"rows": len(merged_en), "englishChanged": len(changed)}
        for locale in TRANSLATED:
            key = kind + "_" + locale
            vanilla_l = vanilla.get(key) or {}
            turtle_l = turtle.get(key) or {}
            out = {}
            placeholders = kept_vanilla = stale = used_turtle = 0
            for row_id in set(vanilla_l) | set(turtle_l):
                if row_id in deleted_en or turtle_l.get(row_id) == b"_":
                    continue
                candidate = turtle_l.get(row_id)
                if candidate is not None:
                    english = merged_en.get(row_id)
                    if english is not None and identical_text(kind, candidate, english):
                        placeholders += 1
                    else:
                        out[row_id] = candidate
                        used_turtle += 1
                        continue
                if row_id in vanilla_l:
                    if row_id in changed:
                        stale += 1
                    else:
                        out[row_id] = vanilla_l[row_id]
                        kept_vanilla += 1
            if out or key in vanilla:
                texts[key] = out
            stats[key] = {"rows": len(out), "turtle": used_turtle, "vanillaKept": kept_vanilla,
                          "vanillaStaleDropped": stale, "turtlePlaceholdersDropped": placeholders}
    report["texts"] = stats
    return texts


# Optimisation and derived-table pruning -----------------------------------

def dedupe_coords(table, report_key, report):
    removed = 0
    for row_id, record in table.items():
        if not isinstance(record, dict):
            continue
        coords = record.get(b"coords")
        if not isinstance(coords, dict) or len(coords) < 2:
            continue
        seen = set()
        kept = []
        for index in sorted(k for k in coords if isinstance(k, int)):
            point = coords[index]
            signature = tuple(sorted(point.items())) if isinstance(point, dict) else point
            if signature in seen:
                removed += 1
                continue
            seen.add(signature)
            kept.append(point)
        if len(kept) != len(coords):
            record = dict(record)
            record[b"coords"] = dict((i + 1, p) for i, p in enumerate(kept))
            table[row_id] = record
    report["optimisation"][report_key + "DuplicateSpawnsRemoved"] = removed


def drop_empty_items(data, report):
    empty = [k for k, v in data["items"].items() if isinstance(v, dict) and not v]
    for key in empty:
        del data["items"][key]
    report["optimisation"]["emptyItemRowsRemoved"] = len(empty)


def referenced_units(data):
    refs = set()
    for record in data["quests"].values():
        if not isinstance(record, dict):
            continue
        for relation in (b"start", b"end", b"obj"):
            rel = record.get(relation)
            if isinstance(rel, dict) and isinstance(rel.get(b"U"), dict):
                refs.update(rel[b"U"].values())
    for record in data["items"].values():
        if isinstance(record, dict):
            for field in (b"U", b"V"):
                if isinstance(record.get(field), dict):
                    refs.update(record[field].keys())
    for record in data["refloot"].values():
        if isinstance(record, dict) and isinstance(record.get(b"U"), dict):
            refs.update(record[b"U"].keys())
    for relation in data["meta"].values():
        if isinstance(relation, dict):
            refs.update(k for k in relation if isinstance(k, int) and k > 0)
    for targets in data["quests-itemreq"].values():
        if isinstance(targets, dict):
            refs.update(k for k in targets if isinstance(k, int) and k > 0)
    return refs


def drop_gm_units(data, texts, report):
    names = texts["units_enUS"]
    refs = referenced_units(data)
    dropped = []
    for unit_id, name in list(names.items()):
        record = data["units"].get(unit_id)
        if not isinstance(name, bytes) or not GM_ONLY_NAME.search(name) or unit_id in refs:
            continue
        coords = record.get(b"coords") if isinstance(record, dict) else None
        if isinstance(coords, dict) and coords:
            continue
        dropped.append(unit_id)
        data["units"].pop(unit_id, None)
        for locale in LOCALES:
            table = texts.get("units_" + locale)
            if table is not None:
                table.pop(unit_id, None)
    report["optimisation"]["gmOnlyUnitsRemoved"] = sorted(dropped)


def unit_areas(record):
    areas = set()
    coords = record.get(b"coords") if isinstance(record, dict) else None
    if isinstance(coords, dict):
        for point in coords.values():
            if isinstance(point, dict) and isinstance(point.get(3), (int, float)):
                areas.add(point[3])
    return areas


def prune_patrols(vanilla, data, changes, report):
    index = dict(vanilla.get("waypoint_index") or {})
    routes = vanilla.get("waypoint_routes") or {}
    deleted = replaced_dropped = 0
    out = {}
    for unit_id, groups in index.items():
        record = data["units"].get(unit_id)
        if record is None:
            deleted += 1
            continue
        if unit_id not in changes["units"]["replaced"]:
            out[unit_id] = groups
            continue
        spawns = []
        coords = record.get(b"coords") if isinstance(record, dict) else None
        if isinstance(coords, dict):
            for point in coords.values():
                if isinstance(point, dict) and all(isinstance(point.get(i), (int, float)) for i in (1, 2, 3)):
                    spawns.append((point[3], point[1], point[2]))
        kept_groups = {}
        for group, route_ids in groups.items():
            kept = []
            for position in sorted(route_ids):
                route_id = route_ids[position]
                route = routes.get(route_id)
                zones = route.get(b"zones") if isinstance(route, dict) else None
                if isinstance(zones, dict) and route_matches(spawns, zones):
                    kept.append(route_id)
                else:
                    replaced_dropped += 1
            if kept:
                kept_groups[group] = dict((i + 1, r) for i, r in enumerate(kept))
        if kept_groups:
            out[unit_id] = kept_groups
    used = set()
    for groups in out.values():
        for route_ids in groups.values():
            used.update(route_ids.values())
    kept_routes = dict((k, v) for k, v in routes.items() if k in used)
    report["derived"]["patrols"] = {
        "indexedUnits": len(index), "unitsDeletedByTurtle": deleted,
        "routesDroppedUnitMoved": replaced_dropped, "unitsKept": len(out),
        "routes": len(routes), "routesKept": len(kept_routes),
    }
    return out, kept_routes


def route_matches(spawns, zones):
    limit = PATROL_MATCH_DISTANCE * PATROL_MATCH_DISTANCE
    for area, x, y in spawns:
        points = zones.get(area)
        if not isinstance(points, dict):
            continue
        for point in points.values():
            if isinstance(point, dict) and isinstance(point.get(1), (int, float)):
                dx, dy = point[1] - x, point[2] - y
                if dx * dx + dy * dy <= limit:
                    return True
    return False


def prune_instance_only(vanilla, data, changes, report):
    """Keep VMaNGOS instance provenance unless Turtle moved the creature outdoors.

    Turtle's data, unlike Vanilla's, records spawns INSIDE dungeons (the Turtle
    client draws dungeon maps), so most of these creatures gain a coordinate in
    their own instance's area. That is not an outdoor spawn. Only an area some
    Vanilla creature or object already had a coordinate in -- the outdoor
    zones, since Vanilla records none inside instances -- disqualifies one.
    """
    source = vanilla.get("instance_only_units") or {}
    outdoor = set()
    for name in ("units", "objects"):
        for record in (vanilla.get(name) or {}).values():
            outdoor |= unit_areas(record)
    out = {}
    deleted = moved = 0
    for unit_id, maps in source.items():
        record = data["units"].get(unit_id)
        if record is None:
            deleted += 1
            continue
        if unit_id in changes["units"]["replaced"]:
            new_areas = unit_areas(record) - unit_areas(vanilla["units"].get(unit_id))
            if new_areas & outdoor:
                moved += 1
                continue
        out[unit_id] = maps
    report["derived"]["instanceOnlyUnits"] = {
        "vanilla": len(source), "deletedByTurtle": deleted,
        "removedNewOutdoorArea": moved, "kept": len(out),
    }
    return out


def prune_by_units(name, vanilla, data, report):
    source = vanilla.get(name) or {}
    out = dict((k, v) for k, v in source.items() if k in data["units"])
    report["derived"][name] = {"vanilla": len(source), "removed": len(source) - len(out),
                               "removedIds": sorted(k for k in source if k not in out)}
    return out


def check_curated(vanilla, data, report):
    approach = vanilla.get("dungeon_approach_units") or {}
    missing = sorted({unit for area in approach.values() if isinstance(area, dict)
                      for unit in area if unit not in data["units"]})
    triggers = []
    for map_id, record in (vanilla.get("instances") or {}).items():
        if not isinstance(record, dict):
            continue
        ids = [record.get(b"access_trigger")]
        entrances = record.get(b"entrances")
        if isinstance(entrances, dict):
            ids += [e.get(b"trigger") for e in entrances.values() if isinstance(e, dict)]
        for trigger in ids:
            if isinstance(trigger, int) and trigger not in data["areatrigger"]:
                triggers.append([map_id, trigger])
    fixes = dict((q, q in data["quests"]) for q in (409, 2206))
    report["derived"]["curated"] = {
        "dungeonApproachUnitsMissing": missing,
        "instanceTriggersMissing": triggers,
        "dataFixQuestsPresent": fixes,
    }
    return missing


def prune_sellprices(vanilla, changes, texts, report):
    source = vanilla.get("sellprices") or {}
    deleted = changes["items"]["deleted"]
    out = dict((k, v) for k, v in source.items() if k not in deleted)
    report["derived"]["sellprices"] = {"vanilla": len(source), "removedDeletedItems": len(source) - len(out)}
    return out


def meta_orphans(data, report):
    missing = 0
    for category, relation in data["meta"].items():
        if not isinstance(relation, dict):
            continue
        for raw_id in relation:
            if not isinstance(raw_id, int):
                continue
            table = data["units"] if raw_id > 0 else data["objects"]
            if abs(raw_id) not in table:
                missing += 1
    report["derived"]["metaEntriesWithoutEntity"] = missing


# Lua writer ---------------------------------------------------------------

def format_number(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if value == int(value) and abs(value) < 1e15:
        return str(int(value))
    return repr(value)


def format_string(value):
    out = bytearray(b'"')
    for byte in value:
        if byte == 0x5C:
            out += b"\\\\"
        elif byte == 0x22:
            out += b'\\"'
        elif byte == 0x0A:
            out += b"\\n"
        elif byte == 0x0D:
            out += b"\\r"
        elif byte < 0x20 or byte == 0x7F:
            out += b"\\%03d" % byte
        else:
            out.append(byte)
    out += b'"'
    return bytes(out)


def sort_key(key):
    if isinstance(key, (int, float)) and not isinstance(key, bool):
        return (0, key, b"")
    return (1, 0, key if isinstance(key, bytes) else str(key).encode())


def format_key(key):
    if isinstance(key, bytes):
        if IDENT.match(key) and key not in LUA_KEYWORDS:
            return key
        return b"[" + format_string(key) + b"]"
    return b"[" + format_number(key).encode() + b"]"


def is_list(table):
    count = len(table)
    if count == 0:
        return False
    for index in range(1, count + 1):
        if index not in table:
            return False
    return True


def format_value(value):
    if isinstance(value, dict):
        if not value:
            return b"{}"
        if is_list(value):
            return b"{" + b",".join(format_value(value[i]) for i in range(1, len(value) + 1)) + b"}"
        parts = []
        for key in sorted(value, key=sort_key):
            parts.append(format_key(key) + b"=" + format_value(value[key]))
        return b"{" + b",".join(parts) + b"}"
    if isinstance(value, bytes):
        return format_string(value)
    return format_number(value).encode()


def write_table(path, header, target, table, dry_run, written, base):
    lines = [header.encode("utf-8"), target.encode("latin-1") + b" = {\n"]
    for key in sorted(table, key=sort_key):
        lines.append(b"  " + format_key(key) + b"=" + format_value(table[key]) + b",\n")
    lines.append(b"}\n")
    blob = b"".join(lines)
    written[os.path.relpath(path, base).replace(os.sep, "/")] = len(blob)
    if not dry_run:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(blob)


def write_routes(path, header, routes, dry_run, written, base):
    lines = [header.encode("utf-8"),
             b'PandaQuestData["waypoint_routes"] = PandaQuestData["waypoint_routes"] or {}\n',
             b'local routes = PandaQuestData["waypoint_routes"]\n']
    for key in sorted(routes, key=sort_key):
        lines.append(b"routes" + format_key(key) + b" = " + format_value(routes[key]) + b"\n")
    blob = b"".join(lines)
    written[os.path.relpath(path, base).replace(os.sep, "/")] = len(blob)
    if not dry_run:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(blob)


# Main ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--vanilla", default=DEFAULT_VANILLA)
    parser.add_argument("--turtle", default=DEFAULT_TURTLE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--report", default=DEFAULT_REPORT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if os.path.abspath(args.vanilla) == os.path.abspath(args.out):
        sys.exit("refusing to merge from the output folder: use the Vanilla snapshot")

    report = {"source": {"vanilla": os.path.basename(args.vanilla), "turtle": TURTLE_SOURCE},
              "tables": {}, "optimisation": {}, "derived": {}}
    vanilla, turtle = load_inputs(args.vanilla, args.turtle)
    report["turtleTablesNotShipped"] = sorted(
        k for k in turtle if k not in DATA_TABLES and not any(
            k == kind + "_" + locale for kind in TEXT_KINDS for locale in LOCALES))

    data, changes = merge_data(vanilla, turtle, report)
    carry_quest_fields(vanilla, data, changes, report)
    texts = merge_texts(vanilla, turtle, report)

    for name in ("units", "objects"):
        dedupe_coords(data[name], name, report)
    drop_empty_items(data, report)
    drop_gm_units(data, texts, report)

    waypoint_index, waypoint_routes = prune_patrols(vanilla, data, changes, report)
    instance_only = prune_instance_only(vanilla, data, changes, report)
    trainers = prune_by_units("trainers", vanilla, data, report)
    approach_missing = check_curated(vanilla, data, report)
    sellprices = prune_sellprices(vanilla, changes, texts, report)
    meta_orphans(data, report)
    if approach_missing:
        sys.exit("dungeon_approach_units names creatures Turtle deleted: %s; review that curated file first"
                 % approach_missing)

    out = args.out
    written = {}
    for name in DATA_TABLES:
        header = PFQUEST_HEADER + TABLE_NOTES.get(name, "")
        write_table(os.path.join(out, name + ".lua"), header,
                    'PandaQuestData["%s"]' % name, data[name], args.dry_run, written, out)
    for key, table in sorted(texts.items()):
        kind, locale = key.rsplit("_", 1)
        write_table(os.path.join(out, locale, kind + ".lua"), PFQUEST_HEADER,
                    'PandaQuestData["%s"]' % key, table, args.dry_run, written, out)
    write_table(os.path.join(out, "trainers.lua"), VMANGOS_HEADER + TABLE_NOTES["trainers"],
                'PandaQuestData["trainers"]', trainers, args.dry_run, written, out)
    write_table(os.path.join(out, "waypoint_index.lua"), VMANGOS_HEADER + TABLE_NOTES["waypoint_index"],
                'PandaQuestData["waypoint_index"]', waypoint_index, args.dry_run, written, out)
    write_table(os.path.join(out, "instance_only_units.lua"),
                VMANGOS_HEADER + TABLE_NOTES["instance_only_units"],
                'PandaQuestData["instance_only_units"]', instance_only, args.dry_run, written, out)
    write_table(os.path.join(out, "sellprices.lua"),
                "-- Vendor sell prices in copper, from pfUI's pfSellData (Eric Mauser / Shagu, MIT).\n"
                "-- GENERATED: tools/make_sell_prices.py, then pruned of items Turtle WoW deleted by\n"
                "-- tools/import_turtle_db.py. Vanilla prices; an item Turtle added has no row.\n",
                'PandaQuestData["sellprices"]', sellprices, args.dry_run, written, out)
    regions = {0: "EasternKingdoms", 1: "Kalimdor"}
    for map_id, region in regions.items():
        routes = dict((k, v) for k, v in waypoint_routes.items()
                      if isinstance(v, dict) and v.get(b"map") == map_id)
        header = (VMANGOS_HEADER + "\n-- Permanent patrol routes: " + region + ".\n"
                  "-- Extracted from VMaNGOS creature_movement and active\n"
                  "-- creature_movement_template records.\n"
                  "-- creature_movement_special and script_waypoint are intentionally excluded.\n"
                  "-- This file appends to the shared locale-independent waypoint_routes table.\n")
        write_routes(os.path.join(out, "Waypoints", region + ".lua"), header, routes, args.dry_run, written, out)
    stray = [k for k, v in waypoint_routes.items() if not (isinstance(v, dict) and v.get(b"map") in regions)]
    if stray:
        sys.exit("waypoint routes outside both regions: %s" % stray[:10])

    # Hand-curated tables pass through unchanged: check_curated verified above
    # that every ID they name still exists in the merged data.
    for name in CURATED_FILES:
        source = os.path.join(args.vanilla, name)
        with open(source, "rb") as handle:
            written[name] = len(handle.read())
        if not args.dry_run:
            shutil.copyfile(source, os.path.join(out, name))

    report["filesWritten"] = dict(sorted(written.items()))
    report["bytesWritten"] = sum(written.values())
    with open(args.report, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True, default=str)
    print(json.dumps({k: report[k] for k in ("tables", "quests", "optimisation", "derived")},
                     indent=1, default=str)[:6000])
    print("bytes written:", report["bytesWritten"], "dry run" if args.dry_run else "")


if __name__ == "__main__":
    main()
