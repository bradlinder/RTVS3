-- @description RTVS3: Sync Trimmed & Split Clips on Timeline
-- @version 1.2.0
-- @author Radio & TV Story Segmenter
-- @about
--   One-shot manual action for REAPER DAW.
--   Scans all media items on the timeline that originated from RTVS3.
--   If any clips were extended, trimmed, or split with 'S', this script
--   immediately updates Item Notes (P_NOTES) with line and paragraph breaks,
--   updates the Take Name timecode range, and re-aligns Take Markers.

local function resolve_companion_path()
    -- 1. Try action context filename
    if reaper and reaper.get_action_context then
        local _, action_file = reaper.get_action_context()
        if action_file and action_file ~= "" then
            local dir = string.match(action_file, "^(.*[\\/])") or ""
            local cand = dir .. "rtvs_reaper_companion.lua"
            local f = io.open(cand, "r")
            if f then f:close(); return cand end
        end
    end

    -- 2. Try REAPER ResourcePath
    if reaper and reaper.GetResourcePath then
        local cand = reaper.GetResourcePath() .. "/Scripts/RTVS3/rtvs_reaper_companion.lua"
        local f = io.open(cand, "r")
        if f then f:close(); return cand end
    end

    -- 3. Try standard APPDATA / HOME paths
    local appdata = os.getenv("APPDATA")
    if appdata and appdata ~= "" then
        local cand = appdata .. "\\REAPER\\Scripts\\RTVS3\\rtvs_reaper_companion.lua"
        local f = io.open(cand, "r")
        if f then f:close(); return cand end
    end

    local home = os.getenv("HOME")
    if home and home ~= "" then
        local cand = home .. "/Library/Application Support/REAPER/Scripts/RTVS3/rtvs_reaper_companion.lua"
        local f = io.open(cand, "r")
        if f then f:close(); return cand end
        cand = home .. "/.config/REAPER/Scripts/RTVS3/rtvs_reaper_companion.lua"
        f = io.open(cand, "r")
        if f then f:close(); return cand end
    end

    return "rtvs_reaper_companion.lua"
end

local comp_file = resolve_companion_path()
_G.RTVS3_COMPANION_LIBRARY_MODE = true
local ok_comp, Companion_or_err = pcall(dofile, comp_file)
_G.RTVS3_COMPANION_LIBRARY_MODE = nil

local Companion = (ok_comp and type(Companion_or_err) == "table") and Companion_or_err or (_G.RTVS3_Companion or {})

local function main()
    if not reaper then return end
    if not Companion.load_latest_index_payload or not Companion.sync_trimmed_or_split_items then
        local err_msg = tostring(Companion_or_err or "Companion table empty")
        reaper.ShowMessageBox(
            "RTVS3 companion functions could not be loaded.\n\nResolved path: " .. tostring(comp_file)
            .. "\n\nError: " .. err_msg,
            "RTVS3 Sync Error",
            0
        )
        return
    end

    local index_data, path = Companion.load_latest_index_payload()
    if not index_data then
        reaper.ShowMessageBox(
            "No RTVS3 transcript index found on disk.\n\n"
            .. "Please copy a story or transcript selection in RTVS3 first to emit the project index.",
            "RTVS3 Sync",
            0
        )
        return
    end

    local synced_count = Companion.sync_trimmed_or_split_items(index_data, true)
    if Companion.start_background_watcher then
        Companion.start_background_watcher()
    end
    if synced_count and synced_count > 0 then
        if reaper.MB then
            reaper.MB(
                string.format("Successfully synchronized %d RTVS3 clip(s) on the timeline with the transcript index.", synced_count),
                "RTVS3 Transcript Sync",
                0
            )
        end
    else
        if reaper.MB then
            reaper.MB(
                "All RTVS3 media items on the timeline are already up to date with the transcript index.",
                "RTVS3 Transcript Sync",
                0
            )
        end
    end
end

main()
