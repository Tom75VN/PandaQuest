"""Print PandaRuntimeProbe results from the SavedVariables file.

Reads only the requested PandaRuntimeProbeDB.latest groups, so the multi-MB
file never has to be opened by hand. Needs lupa (Python 3.10 on this machine:
py -3.10 -B tools/probe_results.py ...). Read it only after /reload or logout,
never while the client may be writing it.

  py -3.10 -B tools/probe_results.py gcwrap                 summary
  py -3.10 -B tools/probe_results.py gcjobs:map. gcheap     several groups
  py -3.10 -B tools/probe_results.py gcbaseline --raw out.lua
                                     serialised groups, for diagnostics/runtime/raw/
"""

import argparse
import os
import sys

from lupa import lua51

DEFAULT_SV = os.path.join("C:\\", "Games", "Wow-Octo", "WTF", "Account", "TOTOM",
                          "SavedVariables", "PandaRuntimeProbe.lua")

SERIALISE = r'''
function PQ_SERIALISE(v, ind)
  ind = ind or ""
  local t = type(v)
  if t == "string" then return string.format("%q", v) end
  if t ~= "table" then return tostring(v) end
  local keys = {}
  for k in pairs(v) do keys[#keys + 1] = k end
  table.sort(keys, function(a, b)
    local ta, tb = type(a), type(b)
    if ta ~= tb then return ta < tb end
    return a < b
  end)
  local out = { "{\n" }
  for _, k in ipairs(keys) do
    local kk = type(k) == "string" and string.format("[%q]", k) or "[" .. tostring(k) .. "]"
    out[#out + 1] = ind .. "  " .. kk .. " = " .. PQ_SERIALISE(v[k], ind .. "  ") .. ",\n"
  end
  out[#out + 1] = ind .. "}"
  return table.concat(out)
end
'''


def rows(table):
    return [table[i] for i in range(1, len(table) + 1)] if table else []


def summarise(name, run):
    print("== %s  completed %s  author %s" % (name, run.completedAt, run.author))
    for test in run.tests.values():
        ev = test.evidence
        print("   %s %s" % (test.id, test.status))
        if name.startswith("gcwrap"):
            print("   all addons %.1f KB/s, wrapped jobs %.1f KB/s, %s s" % (
                ev.allAddonsKBPerSecond, ev.wrappedJobsKBPerSecond, ev.seconds))
            for line in rows(ev.ranking):
                print("   " + line)
        elif name.startswith("gcjobs"):
            print("   baseline %.1f KB/s" % ev.baselineKBPerSecond)
            for line in rows(ev.ranking):
                print("   " + line)
        elif name == "gcheap":
            for p in rows(ev.phases):
                pauses = ", ".join("%.0f ms" % (c.pause * 1000) for c in rows(p.collections))
                print("   %-10s live %.1f MB, natural %s, %.1f KB/s" % (
                    p.name, p.liveKB / 1024, pauses, p.allocatedKBPerSecond or 0))
    if name == "gcbaseline":
        print("   use --raw for the full gcbaseline tables")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("groups", nargs="+")
    parser.add_argument("--sv", default=DEFAULT_SV)
    parser.add_argument("--raw", help="write the serialised groups to this file")
    args = parser.parse_args()

    lua = lua51.LuaRuntime()
    with open(args.sv, encoding="utf-8", errors="replace") as handle:
        lua.execute(handle.read())
    lua.execute(SERIALISE)
    latest = lua.globals().PandaRuntimeProbeDB.latest
    out = []
    for name in args.groups:
        run = latest[name]
        if run is None:
            print("== %s: no stored result" % name)
            continue
        if args.raw:
            out.append("-- latest[%r]\n%s\n" % (name, lua.globals().PQ_SERIALISE(run)))
        else:
            summarise(name, run)
    if args.raw:
        env = lua.globals().PandaRuntimeProbeDB.environment
        out.append("-- environment\n%s\n" % lua.globals().PQ_SERIALISE(env))
        with open(args.raw, "w", encoding="utf-8") as handle:
            handle.write("\n".join(out))
        print("wrote " + args.raw)


if __name__ == "__main__":
    sys.exit(main())
