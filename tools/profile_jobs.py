"""Offline per-job CPU profile of PandaQuest in a given zone scenario.

Loads the real addon and bundled data through the smoke harness's mocked
client (everything in tools/smoke.py before "bootstrapping"), places the player
in a scenario, and times every driver job callback with time.perf_counter over a run of
simulated frames. Host Lua is not Octo's Lua 5.0, so absolute times are not
runtime evidence; the comparison between jobs and between scenarios is a lead.

  py -3.10 -B tools/profile_jobs.py thalassian
  py -3.10 -B tools/profile_jobs.py elwynn
  py -3.10 -B tools/profile_jobs.py thalassian 60 --walk

--walk moves the player every frame at running speed (7 yd/s) on a 60-yard
circle around the scenario position, with IsPlayerMoving true and positions
quantized to one yard as measured on Octo. Without it the player stands still.
"""
import os, sys, time
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

SCENARIOS = {
    "thalassian": r"""
        PQ_TEST_MAP_FILE = "ThalassianHighlands"
        PQ_TEST_ZONE_NAME = "Thalassian Highlands"
        PQ_TEST_SUBZONE_NAME = "Brinthilien"
        table.insert(PQ_TEST_MAP_ZONE_LIST, "Thalassian Highlands")
        PQ_TEST_MAP_ZONE_FILES["Thalassian Highlands"] = "ThalassianHighlands"
        PQ_TEST_ZONE_YARDS = { 3082, 2061 }
        PQ_TEST_PLAYER_POSITION = { 0.4866, 0.8349 }
        PQ_TEST_RACE = { "High Elf", "BloodElf", 10 }
        PQ_TEST_CLASS = { "Mage", "MAGE", 8 }
        PQ_TEST_LEVEL = 2
        PQ_TEST_LOG = {
            { "Thalassian Highlands", 0, nil, 1, nil, nil },
            { "Provisions for Refugees", 1, nil, nil, nil, nil,
              { { "Young Thalassian Boar Flank: 0/10", "item", nil } } },
        }
    """,
    "elwynn": r"""
        PQ_TEST_LEVEL = 6
        PQ_TEST_LOG = {
            { "Elwynn Forest", 0, nil, 1, nil, nil },
            { "Kobold Camp Cleanup", 6, nil, nil, nil, nil,
              { { "Kobold Vermin slain: 4/10", "monster", nil } } },
        }
    """,
}

PROFILE = r"""
PQ_PROFILE = {}
local WIDGET = { "SetPoint", "ClearAllPoints", "SetText", "SetTexture", "SetTexCoord",
    "SetWidth", "SetHeight", "Show", "Hide", "SetAlpha", "SetVertexColor",
    "SetFrameLevel", "SetScale", "GetChildren", "CreateTexture", "CreateFontString" }
local sample = CreateFrame("Frame")
local metas, seen = {}, {}
for _, object in ipairs({ sample, sample:CreateTexture(), sample:CreateFontString() }) do
    local mt = getmetatable(object)
    local index = mt and mt.__index
    if type(index) == "table" and not seen[index] then
        seen[index] = true
        table.insert(metas, index)
    end
end
for _, meta in ipairs(metas) do
    for _, name in ipairs(WIDGET) do
        local real = rawget(meta, name)
        if type(real) == "function" then
            meta[name] = function(...)
                local job = PQ_CURRENT_JOB
                if job then
                    job.widget = job.widget + 1
                    job.methods[name] = (job.methods[name] or 0) + 1
                end
                return real(...)
            end
        end
    end
end
PQ_PROFILE_METAS = table.getn(metas)
local driver = PandaQuest:GetModule('Driver')
for _, job in ipairs(driver.jobs) do
    local real = job.callback
    local entry = { name = job.name, interval = job.interval, calls = 0, total = 0, worst = 0, widget = 0, methods = {} }
    PQ_PROFILE[job.name] = entry
    job.callback = function(a)
        local t0 = PQ_CLOCK()
        local outer = PQ_CURRENT_JOB
        PQ_CURRENT_JOB = entry
        real(a)
        PQ_CURRENT_JOB = outer
        local dt = PQ_CLOCK() - t0
        entry.calls = entry.calls + 1
        entry.total = entry.total + dt
        if dt > entry.worst then entry.worst = dt end
    end
end
"""


WALK = r"""
PQ_TEST_MOVING = true
PQ_TEST_QUANTIZE_YARDS = true
local centreX, centreY = PQ_TEST_PLAYER_POSITION[1], PQ_TEST_PLAYER_POSITION[2]
local radius, speed, walked = 60, 7, 0
local realTick = PQ_TEST_TICK
function PQ_TEST_TICK(seconds, steps)
    steps = steps or 1
    for _ = 1, steps do
        walked = walked + seconds
        local angle = walked * speed / radius
        PQ_TEST_PLAYER_POSITION = {
            centreX + radius * math.cos(angle) / PQ_TEST_ZONE_YARDS[1],
            centreY + radius * math.sin(angle) / PQ_TEST_ZONE_YARDS[2],
        }
        realTick(seconds, 1)
    end
end
"""


WRAP = r"""
PQ_WRAPPED = {}
function PQ_WRAP(target)
    local _, _, moduleName, method = string.find(target, "^([%w_]+):([%w_]+)$")
    local owner, key
    if moduleName then
        owner = PandaQuest:GetModule(moduleName)
        key = method
    else
        local _, _, field = string.find(target, "^Client%.([%w_]+)$")
        owner = PandaQuest.Client
        key = field
    end
    if not owner or type(owner[key]) ~= "function" then
        PQ_WRAPPED[target] = { missing = true, calls = 0, total = 0 }
        return
    end
    local real = owner[key]
    local entry = { calls = 0, total = 0 }
    PQ_WRAPPED[target] = entry
    owner[key] = function(...)
        local t0 = PQ_CLOCK()
        local r = table.pack(real(...))
        entry.total = entry.total + (PQ_CLOCK() - t0)
        entry.calls = entry.calls + 1
        return table.unpack(r, 1, r.n)
    end
end
"""


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "thalassian"
    walk = "--walk" in sys.argv
    if walk:
        sys.argv.remove("--walk")
    seconds = float(sys.argv[2]) if len(sys.argv) > 2 else 60
    source = (TOOLS / "smoke.py").read_text(encoding="utf-8")
    cut = source.index('print("bootstrapping")')
    devnull = open(os.devnull, "w")
    real_stdout = sys.stdout
    sys.stdout = devnull
    namespace = {"__file__": str(TOOLS / "smoke.py"), "__name__": "pq_profile"}
    exec(compile(source[:cut], "smoke.py", "exec"), namespace)
    rt = namespace["rt"]
    rt.execute(SCENARIOS[name])
    rt.execute("PQ_TEST_FIRE('VARIABLES_LOADED')")
    rt.execute("PQ_TEST_FIRE('PLAYER_ENTERING_WORLD')")
    # Let start-up indexing finish before measuring, as in game.
    rt.execute("PQ_TEST_TICK(0.0125, 4000)")
    rt.globals().PQ_CLOCK = time.perf_counter
    if walk:
        rt.execute(WALK)
        # One lap of settling so pins exist before the measured run.
        rt.execute("PQ_TEST_TICK(0.0125, 400)")
    rt.execute(PROFILE)
    wrap = [a for a in sys.argv[3:]]
    if wrap:
        rt.execute(WRAP)
        for target in wrap:
            rt.eval("PQ_WRAP")(target)
    frames = int(seconds / 0.0125)
    rt.execute("PQ_TEST_TICK(0.0125, %d)" % frames)
    sys.stdout = real_stdout

    rows = []
    for job_name, entry in rt.eval("PQ_PROFILE").items():
        methods = sorted(((v, k) for k, v in entry.methods.items()), reverse=True)[:8]
        rows.append((entry.total, job_name, entry.interval, entry.calls, entry.worst, entry.widget, methods))
    rows.sort(reverse=True)
    total = sum(r[0] for r in rows)
    zone = rt.eval("GetRealZoneText()")
    area = rt.eval("(function() local mc = PandaQuest:GetModule('MapContext'); "
                   "local a = mc and mc:GetCurrentZoneView(); return tostring(a) end)()")
    print("scenario %s%s: zone %s, areaId %s, %d frames, %.0f s simulated" % (
        name, " (walking)" if walk else "", zone, area, frames, seconds))
    print("total job CPU %.1f ms per simulated second" % (total / seconds * 1000))
    print("widget calls per second, all jobs: %.0f" % (sum(r[5] for r in rows) / seconds))
    print("%9s %9s %9s %7s %8s  %s" % ("ms/s", "ms/call", "worst ms", "calls", "widget/s", "job"))
    for total_s, job_name, interval, calls, worst, widget, methods in rows[:25]:
        per_call = total_s / calls * 1000 if calls else 0
        top = ", ".join("%s %.0f" % (k, v / seconds) for v, k in methods)
        print("%9.2f %9.3f %9.2f %7d %8.0f  %s@%s  %s" % (total_s / seconds * 1000, per_call, worst * 1000, calls, widget / seconds, job_name, interval, top))


    if wrap:
        print("wrapped:")
        for target, entry in rt.eval("PQ_WRAPPED").items():
            if entry.missing:
                print("  missing  %s" % target)
            else:
                print("%9.2f ms/s %9.4f ms/call %7d calls  %s" % (
                    entry.total / seconds * 1000,
                    entry.total / entry.calls * 1000 if entry.calls else 0,
                    entry.calls, target))
    print("navigator: context=%s reason=%s shown=%s" % (
        rt.eval("tostring(PandaQuest:GetModule('Navigator').context ~= nil)"),
        rt.eval("tostring(PandaQuest:GetModule('Navigator').contextReason)"),
        rt.eval("tostring(PandaQuest:GetModule('Navigator').shown)")))


if __name__ == "__main__":
    main()
