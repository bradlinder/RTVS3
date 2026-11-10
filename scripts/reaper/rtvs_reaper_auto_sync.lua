-- @description RTVS3: Toggle Background Live Auto-Sync for Trimmed & Split Clips
-- @version 1.2.0
-- @author Radio & TV Story Segmenter
-- @about
--   Continuously monitors REAPER project media items in the background.
--   Whenever an RTVS3 clip's left or right boundaries are adjusted (D_STARTOFFS or D_LENGTH),
--   or whenever an item is split with 'S', this watcher automatically re-slices the
--   verbatim transcript from the RTVS3 index, updates Item Notes (P_NOTES) with line
--   and paragraph breaks, updates the Take Name timecode range, and refreshes Take Markers.
--   Can be toggled on/off from a REAPER toolbar button or assigned shortcut.

local function resolve_companion_path()
    if reaper and reaper.get_action_context then
        local _, action_file = reaper.get_action_context()
        if action_file and action_file ~= "" then
            local dir = string.match(action_file, "^(.*[\\/])") or ""
            local cand = dir .. "rtvs_reaper_companion.lua"
            local f = io.open(cand, "r")
            if f then f:close(); return cand end
        end
    end

    if reaper and reaper.GetResourcePath then
        local cand = reaper.GetResourcePath() .. "/Scripts/RTVS3/rtvs_reaper_companion.lua"
        local f = io.open(cand, "r")
        if f then f:close(); return cand end
    end

    local appdata = os.getenv("APPDATA")
    if appdata and appdata ~= "" then
        local cand = appdata .. "\\REAPER\\Scripts\\RTVS3\\rtvs_reaper_companion.lua"
        local f = io.open(cand, "r")
        if f then f:close(); return cand end
    end

    return "rtvs_reaper_companion.lua"
end

local comp_file = resolve_companion_path()
_G.RTVS3_COMPANION_LIBRARY_MODE = true
local ok_comp, Companion_or_err = pcall(dofile, comp_file)
_G.RTVS3_COMPANION_LIBRARY_MODE = nil

local Companion = (ok_comp and type(Companion_or_err) == "table") and Companion_or_err or (_G.RTVS3_Companion or {})

local is_running = true
local _, _, section_id, cmd_id = 0, 0, 0, 0
if reaper and reaper.get_action_context then
    _, _, section_id, cmd_id = reaper.get_action_context()
end
local last_check_time = 0.0
local check_interval_sec = 0.35
local cached_index_data = nil

local function set_toggle_state(state)
    if reaper and section_id and cmd_id and cmd_id > 0 then
        reaper.SetToggleCommandState(section_id, cmd_id, state and 1 or 0)
        reaper.RefreshToolbar2(section_id, cmd_id)
    end
end

local function on_exit()
    set_toggle_state(false)
end

if reaper and reaper.atexit then
    reaper.atexit(on_exit)
end
if reaper and reaper.SetExtState then
    reaper.SetExtState("RTVS3", "AUTO_SYNC_ACTIVE", "0", false)
    reaper.SetExtState("RTVS3", "WATCHER_TOKEN", "", false)
end
set_toggle_state(true)
local first_sync_done = false

local function main_loop()
    if not is_running then return end

    local now = (reaper.time_precise and reaper.time_precise() or os.clock())
    if (now - last_check_time) >= check_interval_sec then
        last_check_time = now

        if Companion.load_latest_index_payload then
            local index_data, _ = Companion.load_latest_index_payload()
            if index_data then
                cached_index_data = index_data
            end
        end

        if cached_index_data and Companion.sync_trimmed_or_split_items then
            Companion.sync_trimmed_or_split_items(cached_index_data, not first_sync_done)
            first_sync_done = true
        end
    end

    reaper.defer(main_loop)
end

if reaper and reaper.defer then
    reaper.defer(main_loop)
end
