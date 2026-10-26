--[[
PandaQuest / Quest/QuestHistory.lua

Locally-tracked quest completions, keyed by database quest ID.

This client exposes no quest-ID-returning call and no completed-quest history
call at all (docs/CLIENT-COMPATIBILITY.md, "No quest ID API"). A "still to
take" map marker can therefore never know about a quest the player finished
before this addon was first loaded -- there is nothing to ask the server or
the client. What it CAN do is remember, from here on, every quest it
personally watches disappear from the quest log while complete, plus whatever
the player marks by hand. That is the full extent of what "done" means here.

Storage goes through Config's existing shallow section store (SavedVariables),
keyed by the numeric quest ID -- never a title, path or other unsafe string --
so QuestHistory carries no persistence risk beyond what Config already
guards against. The section is capped by Config's per-section entry limit,
which is raised for the history sections specifically: they hold one entry per
quest a character has ever finished, so the working-set ceiling that fits
"quests I am tracking right now" would silently refuse most of a career.

Two smaller sections shadow the first, each recording WHERE a "done" came
from so it can be taken back on its own:

  * questHistoryManual -- every quest ID the player marked by hand, through
    WorldMapPins' shift-click (bulk) or Ctrl+click (single-quest) giver
    gesture. That split is what lets /pq resetmarked undo only what the player
    clicked, without also un-completing quests this addon correctly inferred
    from watching the log on its own.
  * questHistoryImported -- every quest ID that came in from another addon's
    saved history (Quest/PfQuestImport.lua). An import is a bulk claim about a
    career this addon never watched, sourced from data it cannot verify, so it
    has to be reversible as one act rather than one quest at a time.

The auto-detection below (QUEST_REMOVED and the turn-in window) writes to
neither. A quest can be in
both shadow sections at once (imported, then re-marked by hand); clearing
either one clears the "done" flag, which is the conservative reading -- a mark
the player asked to undo goes away whatever else also claimed it.
]]

local PQ = PandaQuest
local QuestHistory = PQ:NewModule("QuestHistory")

local SECTION = "questHistory"
local MANUAL_SECTION = "questHistoryManual"
local IMPORTED_SECTION = "questHistoryImported"

local function Config()
    return PQ:GetModule("Config")
end

-- The keys of a section that are actually set, as an array. Collected before
-- anything is removed: nothing here deletes from a table while iterating it.
local function CollectMarked(section)
    local marked = {}
    local key, value
    for key, value in pairs(section) do
        if value == 1 then
            table.insert(marked, key)
        end
    end
    return marked
end

-- Clears one provenance section (manual or imported) and the matching "done"
-- flags, returning the quest IDs it cleared. Quests not recorded in that
-- section are untouched, whatever else marked them done.
local function ClearShadowSection(name)
    local config = Config()
    if not config then
        return {}
    end
    local reset = CollectMarked(config:GetSection(name))
    local index = 1
    local total = table.getn(reset)
    while index <= total do
        local id = reset[index]
        config:SetSectionEntry(name, id, nil)
        config:SetSectionEntry(SECTION, id, nil)
        index = index + 1
    end
    return reset
end

function QuestHistory:IsDone(questId)
    if type(questId) ~= "number" then
        return false
    end
    local config = Config()
    if not config then
        return false
    end
    return config:GetSection(SECTION)[questId] == 1
end

function QuestHistory:MarkDone(questId)
    if type(questId) ~= "number" then
        return false
    end
    local config = Config()
    if not config then
        return false
    end
    return config:SetSectionEntry(SECTION, questId, 1)
end

function QuestHistory:MarkNotDone(questId)
    if type(questId) ~= "number" then
        return false
    end
    local config = Config()
    if not config then
        return false
    end
    config:SetSectionEntry(MANUAL_SECTION, questId, nil)
    config:SetSectionEntry(IMPORTED_SECTION, questId, nil)
    return config:SetSectionEntry(SECTION, questId, nil)
end

-- The manual-gesture counterpart of MarkDone: same effect on the "done" flag,
-- plus a record in MANUAL_SECTION so /pq resetmarked can find it again later.
function QuestHistory:MarkDoneManually(questId)
    if type(questId) ~= "number" then
        return false
    end
    local config = Config()
    if not config then
        return false
    end
    config:SetSectionEntry(MANUAL_SECTION, questId, 1)
    return config:SetSectionEntry(SECTION, questId, 1)
end

-- The import counterpart: the same effect on the "done" flag, plus a record in
-- IMPORTED_SECTION so the whole import can be rolled back later.
--
-- Returns false when the quest was ALREADY done before this call, so an
-- importer can report how many quests it actually added rather than how many
-- it looked at -- and so rolling that import back cannot un-complete a quest
-- this addon had established on its own. A quest already recorded keeps
-- whatever provenance it had; the import does not claim it.
function QuestHistory:MarkDoneImported(questId)
    if type(questId) ~= "number" then
        return false
    end
    local config = Config()
    if not config then
        return false
    end
    if config:GetSection(SECTION)[questId] == 1 then
        return false
    end
    config:SetSectionEntry(IMPORTED_SECTION, questId, 1)
    return config:SetSectionEntry(SECTION, questId, 1)
end

-- Clears every quest ID recorded in MANUAL_SECTION from both sections and
-- returns how many were reset. Quests QuestHistory learned about on its own
-- (QUEST_REMOVED while complete) were never added to MANUAL_SECTION, so they
-- are left exactly as they were.
function QuestHistory:ResetManual()
    return ClearShadowSection(MANUAL_SECTION)
end

-- Clears every quest ID that came in through an import, from both sections,
-- and returns the list. Quests this addon inferred for itself and quests the
-- player marked by hand were never written to IMPORTED_SECTION, so they are
-- left exactly as they were -- an import can be undone without costing the
-- player the history they earned in this addon.
function QuestHistory:ResetImported()
    return ClearShadowSection(IMPORTED_SECTION)
end

-- How many quest IDs are recorded as having come from an import.
function QuestHistory:GetImportedCount()
    local config = Config()
    if not config then
        return 0
    end
    return table.getn(CollectMarked(config:GetSection(IMPORTED_SECTION)))
end

-- Every quest ID marked done, manual or not. Used to size the gap between
-- what ResetManual can see and what is actually recorded -- MANUAL_SECTION
-- only started being written the moment MarkDoneManually shipped, so a quest
-- shift-clicked before that update is done in SECTION with no matching
-- MANUAL_SECTION entry, and ResetManual alone cannot find it.
function QuestHistory:GetDoneCount()
    local config = Config()
    if not config then
        return 0
    end
    return table.getn(CollectMarked(config:GetSection(SECTION)))
end

-- Clears every quest marked done at all, manual-gesture or auto-detected
-- alike, and returns how many. The blunt fallback for /pq resetmarked all,
-- for undoing a mark made before MANUAL_SECTION existed to track it.
function QuestHistory:ResetAll()
    local config = Config()
    if not config then
        return {}
    end
    local reset = CollectMarked(config:GetSection(SECTION))
    local index = 1
    local total = table.getn(reset)
    while index <= total do
        local id = reset[index]
        config:SetSectionEntry(MANUAL_SECTION, id, nil)
        config:SetSectionEntry(IMPORTED_SECTION, id, nil)
        config:SetSectionEntry(SECTION, id, nil)
        index = index + 1
    end
    return reset
end

-- Chain inference -------------------------------------------------------------
--
-- A follow-up can only be accepted once its predecessor was turned in, so a
-- quest known done, or sitting in the log, proves its prerequisite done too.
-- This closes the gap the QUEST_REMOVED heuristic below leaves: a step with no
-- objectives (Refugees no More, 41187, a "go and speak to" quest) is never
-- reported complete by the log, so its turn-in went unrecorded and every
-- quest gated on it -- A Crown of Flowers, 41191 -- kept its "!" hidden while
-- the server was already offering it.
--
-- `pre` lists alternatives (see QuestEligibility), so a predecessor is only
-- inferred when it is the one alternative this character's race and class
-- could have taken; with two left there is no telling which was done. Manual
-- and imported marks are never a source, so undoing one cannot leave behind
-- an inferred predecessor the player has no way to trace.

local MAX_CHAIN_DEPTH = 40

local function SolePrerequisite(database, eligibility, record)
    if type(record.pre) ~= "table" then
        return nil
    end
    local found = nil
    local index = 1
    local total = table.getn(record.pre)
    while index <= total do
        local candidateId = record.pre[index]
        if type(candidateId) == "number" and (not eligibility
            or eligibility:MatchesRaceClass(database:GetQuest(candidateId))) then
            if found then
                return nil
            end
            found = candidateId
        end
        index = index + 1
    end
    return found
end

-- Marks the predecessors of `questId` done, walking back while each step has
-- a single possible predecessor. Returns how many entries were added.
function QuestHistory:InferPrerequisites(questId)
    local config = Config()
    local database = PQ:GetModule("Database")
    if type(questId) ~= "number" or not config or not database then
        return 0
    end
    local eligibility = PQ:GetModule("QuestEligibility")
    local section = config:GetSection(SECTION)
    local inferred = 0
    local current = questId
    local depth = 0
    while depth < MAX_CHAIN_DEPTH do
        local record = database:GetQuest(current)
        if type(record) ~= "table" then
            break
        end
        local previous = SolePrerequisite(database, eligibility, record)
        if not previous or previous == questId then
            break
        end
        if section[previous] ~= 1 then
            if not config:SetSectionEntry(SECTION, previous, 1) then
                break
            end
            inferred = inferred + 1
        end
        current = previous
        depth = depth + 1
    end
    return inferred
end

-- Every identified quest in the log vouches for its predecessors. Run on
-- QUEST_LOG_CHANGED rather than QUEST_ADDED: identities can resolve a scan
-- after the row appeared, and that only announces itself as a log change.
-- An "ambiguous" match is a guess and is not trusted to prove anything.
function QuestHistory:InferFromLog(questState)
    local quests = questState:GetOrderedQuestsView()
    local inferred = 0
    local index = 1
    local total = table.getn(quests)
    while index <= total do
        local quest = quests[index]
        if quest and type(quest.questId) == "number"
            and quest.matchConfidence ~= "ambiguous" then
            inferred = inferred + self:InferPrerequisites(quest.questId)
        end
        index = index + 1
    end
    return inferred
end

-- Once per session: history recorded before chain inference existed (or by a
-- removal whose predecessor was never seen) gets its gaps filled. Sources are
-- collected first because inference writes into the section being read.
function QuestHistory:InferFromHistory()
    local config = Config()
    if not config then
        return 0
    end
    local manual = config:GetSection(MANUAL_SECTION)
    local imported = config:GetSection(IMPORTED_SECTION)
    local sources = {}
    local key, value
    for key, value in pairs(config:GetSection(SECTION)) do
        if value == 1 and type(key) == "number"
            and manual[key] ~= 1 and imported[key] ~= 1 then
            table.insert(sources, key)
        end
    end
    local inferred = 0
    local index = 1
    local total = table.getn(sources)
    while index <= total do
        inferred = inferred + self:InferPrerequisites(sources[index])
        index = index + 1
    end
    return inferred
end

-- Turn-in window -------------------------------------------------------------
--
-- The log never reports a quest without objectives as complete, so the
-- QUEST_REMOVED test below cannot see it handed in -- and when nothing later
-- in a chain names it as `pre` (Earth Sapta, 1463, a one-step side quest at
-- Canaga Earthcaller), inference cannot recover it either: its "!" stayed on
-- the giver after the turn-in. The reward window is the missing signal: it
-- only opens for a quest the server accepts as ready to hand in.
--
-- QUEST_COMPLETE records which quest the window shows. That quest then
-- counts as turned in when it leaves the log while the window is open or
-- shortly after it closes, or -- a quest accepted and handed in between two
-- scans is never modelled at all -- when a full scan taken after the window
-- opened does not hold it. A window closed without handing in leaves the
-- quest in the log, and the pending entry expires.

local TURN_IN_SETTLE = 1
local TURN_IN_GRACE = 10
-- Only reached if QUEST_FINISHED never arrives to close the window.
local TURN_IN_MAX_OPEN = 600
local TURN_IN_JOB = "quest.history.turnin"

local function FinishedBySpeaker(database, questId, speakerKey)
    local finishers = database:GetQuestFinishers(questId)
    local units = type(finishers) == "table" and finishers.U
    if type(units) ~= "table" then
        return false
    end
    local index = 1
    local total = table.getn(units)
    while index <= total do
        if PQ.NameKey(database:GetUnitName(units[index])) == speakerKey then
            return true
        end
        index = index + 1
    end
    return false
end

-- The reward window carries only a title. When QuestMatch cannot settle it,
-- the candidates this character could take AND whose finisher is the unit
-- being spoken to are tried: Earth Sapta is both 1462 (Seer Ravenfeather) and
-- 1463 (Canaga Earthcaller), with the same level, races and class.
local function TurnInQuestId(title)
    local matcher = PQ:GetModule("QuestMatch")
    local questId = matcher and matcher:ResolveGiverQuestId()
    if type(questId) == "number" then
        return questId
    end
    local database = PQ:GetModule("Database")
    local key = PQ.NameKey(title)
    local ids = database and key and database:FindQuestIdsByTitleKey(key)
    if type(ids) ~= "table" then
        return nil
    end
    local eligibility = PQ:GetModule("QuestEligibility")
    local speaker = PQ.Client.GetQuestDialogueSpeaker
        and PQ.Client.GetQuestDialogueSpeaker()
    local speakerKey = speaker and PQ.NameKey(speaker)
    local found = nil
    local index = 1
    local total = table.getn(ids)
    while index <= total do
        local candidate = ids[index]
        if (not eligibility or eligibility:MatchesRaceClass(database:GetQuest(candidate)))
            and (not speakerKey or FinishedBySpeaker(database, candidate, speakerKey)) then
            if found then
                return nil
            end
            found = candidate
        end
        index = index + 1
    end
    return found
end

local function InLogById(questState, questId)
    local quests = questState:GetOrderedQuestsView()
    local index = 1
    local total = table.getn(quests)
    while index <= total do
        local quest = quests[index]
        if quest and quest.questId == questId then
            return true
        end
        index = index + 1
    end
    return false
end

local function MarkMapDirty()
    local pins = PQ:GetModule("WorldMapPins")
    if pins then
        pins.dirty = true
    end
    local minimap = PQ:GetModule("MinimapPins")
    if minimap then
        minimap.dirty = true
    end
    local driver = PQ:GetModule("Driver")
    if driver then
        driver:Wake("map.worldpins")
        driver:Wake("map.minimappins")
    end
end

function QuestHistory:RecordTurnIn(questId)
    if type(questId) ~= "number" then
        return false
    end
    self:MarkDone(questId)
    self:InferPrerequisites(questId)
    return true
end

function QuestHistory:ClearPendingTurnIn()
    self.pendingTurnIn = nil
    local driver = PQ:GetModule("Driver")
    if driver then
        driver:Unschedule(TURN_IN_JOB)
    end
end

function QuestHistory:OnTurnInWindow()
    local title = PQ.Client.GetQuestGiverTitle and PQ.Client.GetQuestGiverTitle()
    local titleKey = title and PQ.NameKey(title)
    if not titleKey then
        return
    end
    self.pendingTurnIn = {
        titleKey = titleKey,
        questId = TurnInQuestId(title),
        openedAt = PQ.Client.Now(),
    }
    local driver = PQ:GetModule("Driver")
    if driver then
        driver:Schedule(TURN_IN_JOB, 0.5, function() QuestHistory:CheckTurnIn() end)
    end
end

function QuestHistory:OnTurnInWindowClosed()
    local pending = self.pendingTurnIn
    if pending and not pending.closedAt then
        pending.closedAt = PQ.Client.Now()
    end
end

-- A modelled quest is settled by its QUEST_REMOVED; this only handles the one
-- that never reached a scan, and expires the entry once the window is gone.
function QuestHistory:CheckTurnIn()
    local pending = self.pendingTurnIn
    local questState = PQ:GetModule("QuestState")
    if not pending or not questState then
        self:ClearPendingTurnIn()
        return
    end
    local now = PQ.Client.Now()
    if (pending.closedAt and now - pending.closedAt > TURN_IN_GRACE)
        or now - pending.openedAt > TURN_IN_MAX_OPEN then
        self:ClearPendingTurnIn()
        return
    end
    if pending.modelled then
        return
    end
    if questState:GetQuest(pending.titleKey)
        or (pending.questId and InLogById(questState, pending.questId)) then
        pending.modelled = true
        return
    end
    -- Absent from a scan of the whole log taken after the window opened.
    if not questState:IsComplete() or type(questState.lastScan) ~= "number"
        or questState.lastScan < pending.openedAt + TURN_IN_SETTLE then
        return
    end
    local questId = pending.questId
    self:ClearPendingTurnIn()
    if self:RecordTurnIn(questId) then
        MarkMapDirty()
    end
end

function QuestHistory:OnQuestRemoved(quest)
    local pending = self.pendingTurnIn
    if pending and quest.titleKey == pending.titleKey then
        local questId = pending.questId
        if not questId and quest.matchConfidence ~= "ambiguous" then
            questId = quest.questId
        end
        self:ClearPendingTurnIn()
        if self:RecordTurnIn(questId) then
            return
        end
    end
    -- A quest that was complete (ready to hand in) on its last scan and then
    -- disappeared from the log almost always means it was turned in rather
    -- than abandoned. This is a heuristic, not a certainty; shift-clicking a
    -- marker lets the player correct it either way.
    if quest.isComplete == 1 then
        self:RecordTurnIn(quest.questId)
    end
end

-- The history backfill waits for the first log change instead of running
-- here: QuestEligibility enables after this module, and until it has read the
-- player's race and class every multi-alternative `pre` stays unresolved.
function QuestHistory:OnEnable()
    local events = PQ:GetModule("Events")
    if events then
        events:Register("QUEST_COMPLETE", function()
            QuestHistory:OnTurnInWindow()
        end)
        events:Register("QUEST_FINISHED", function()
            QuestHistory:OnTurnInWindowClosed()
        end)
    end
    local questState = PQ:GetModule("QuestState")
    if questState then
        questState:AddListener(function(event, quest)
            if event == "QUEST_REMOVED" and quest then
                QuestHistory:OnQuestRemoved(quest)
            elseif event == "QUEST_LOG_CHANGED" then
                if not QuestHistory.historyInferred then
                    QuestHistory.historyInferred = true
                    QuestHistory:InferFromHistory()
                end
                QuestHistory:InferFromLog(questState)
            end
        end)
    end
end
