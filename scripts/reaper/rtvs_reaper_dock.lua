-- @description RTVS3: Dockable ReaImGui Transcript & Story Browser
-- @version 1.1.0
-- @author Radio & TV Story Segmenter
-- @about
--   Optional dockable ReaImGui panel for REAPER DAW that connects to
--   Radio & TV Story Segmenter (RTVS3) via its sidecar JSON files.
--   Allows searching transcript segments, browsing segmented stories,
--   inserting any story or speaker turn directly at the REAPER edit cursor,
--   and automatically syncing Item Notes and Take Markers in real time
--   whenever RTVS3 clips are trimmed, extended, or split on the REAPER timeline.

local script_dir = ({reaper and reaper.get_action_context and reaper.get_action_context() or ""})[2] or ""
script_dir = string.match(script_dir, "^(.*[\\/])") or ""

_G.RTVS3_COMPANION_LIBRARY_MODE = true
local ok_comp, Companion = pcall(dofile, script_dir .. "rtvs_reaper_companion.lua")
_G.RTVS3_COMPANION_LIBRARY_MODE = nil

if not ok_comp or type(Companion) ~= "table" then
    Companion = _G.RTVS3_Companion or {}
end

local Dock = {
    ctx = nil,
    window_title = "RTVS3 Transcript & Story Companion",
    search_query = "",
    last_poll_time = 0.0,
    poll_interval_sec = 0.5,
    last_cue_timestamp = "",
    last_index_timestamp = "",
    latest_cue = nil,
    latest_index = nil,
    status_msg = "Ready. Copy any selection or story in RTVS3.",
}

--------------------------------------------------------------------------------
-- 1. Sidecar Index Discovery & Live Trim/Split Polling
--------------------------------------------------------------------------------
function Dock.get_candidate_index_paths()
    if Companion.get_candidate_index_paths then
        return Companion.get_candidate_index_paths()
    end
    local paths = {}
    local local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata and local_appdata ~= "" then
        paths[#paths + 1] = local_appdata .. "\\RadioTVStorySegmenter\\reaper_ipc\\latest_transcript_index.json"
    end
    local home = os.getenv("HOME")
    if home and home ~= "" then
        paths[#paths + 1] = home .. "/Library/Application Support/RadioTVStorySegmenter/reaper_ipc/latest_transcript_index.json"
        paths[#paths + 1] = home .. "/.local/share/RadioTVStorySegmenter/reaper_ipc/latest_transcript_index.json"
    end
    local tmp = os.getenv("TEMP") or os.getenv("TMP") or os.getenv("TMPDIR") or "/tmp"
    local sep = package.config:sub(1, 1)
    paths[#paths + 1] = tmp .. sep .. "rtvs3_reaper_index.json"
    return paths
end

function Dock.format_clock(seconds)
    if Companion.format_clock then
        return Companion.format_clock(seconds)
    end
    local sec = math.max(0.0, tonumber(seconds) or 0.0)
    local m = math.floor(sec / 60)
    local s = sec - (m * 60)
    return string.format("%02d:%04.1f", m, s)
end

function Dock.poll_sidecars(force)
    local now = (reaper and reaper.time_precise) and reaper.time_precise() or os.clock()
    if not force and (now - Dock.last_poll_time) < Dock.poll_interval_sec then
        return
    end
    Dock.last_poll_time = now

    if Companion.load_latest_cue_payload then
        local cue, _ = Companion.load_latest_cue_payload()
        if cue and cue.timestamp_utc ~= Dock.last_cue_timestamp then
            Dock.latest_cue = cue
            Dock.last_cue_timestamp = tostring(cue.timestamp_utc or "")
            Dock.status_msg = "Synced clip cue: " .. tostring(cue.take_name or cue.title or "RTVS3 Clip")
        end
    end

    if Companion.read_file_text and Companion.decode_json then
        for _, idx_path in ipairs(Dock.get_candidate_index_paths()) do
            local raw = Companion.read_file_text(idx_path)
            if raw and #raw > 2 then
                local parsed, _ = Companion.decode_json(raw)
                if parsed and type(parsed) == "table" then
                    if tostring(parsed.timestamp_utc or "") ~= Dock.last_index_timestamp then
                        Dock.latest_index = parsed
                        Dock.last_index_timestamp = tostring(parsed.timestamp_utc or "")
                    end
                    break
                end
            end
        end
    end

    -- Automatically detect and sync any RTVS3 clips trimmed, extended, or split on the REAPER timeline
    if Dock.latest_index and Companion.sync_trimmed_or_split_items then
        local synced = Companion.sync_trimmed_or_split_items(Dock.latest_index, false)
        if synced and synced > 0 then
            Dock.status_msg = string.format("Auto-synced %d trimmed/split clip(s) on timeline.", synced)
        end
    end
end

--------------------------------------------------------------------------------
-- 2. Direct Story & Segment Insertion Builders
--------------------------------------------------------------------------------
function Dock.active_marker_style()
    if Dock.latest_cue and Dock.latest_cue.marker_style then
        return tostring(Dock.latest_cue.marker_style)
    end
    return "speakers"
end

function Dock.insert_story_from_index(story)
    if not Dock.latest_index or type(story) ~= "table" then return end
    local s_sec = tonumber(story.start_sec) or 0.0
    local e_sec = tonumber(story.end_sec) or s_sec
    local dur = math.max(0.05, e_sec - s_sec)
    local m_style = Dock.active_marker_style()

    local sliced
    if Companion.slice_transcript_for_range then
        sliced = Companion.slice_transcript_for_range(Dock.latest_index, s_sec, e_sec, m_style)
    else
        sliced = { plain_text = "", speakers = {}, sentence_cues = {}, primary_color_hex = "#38bdf8" }
    end

    local range_str = string.format("[%s - %s]", Dock.format_clock(s_sec), Dock.format_clock(e_sec))
    local title = tostring(story.title or "Untitled Story")
    local payload = {
        schema_version = "1.0",
        source_media_path = Dock.latest_index.source_media_path or "",
        project_path = Dock.latest_index.project_path or "",
        clip_type = "story",
        title = title,
        take_name = title .. " " .. range_str,
        start_sec = s_sec,
        end_sec = e_sec,
        duration_sec = dur,
        fade_in_sec = tonumber(story.fade_in_sec) or 0.0,
        fade_out_sec = tonumber(story.fade_out_sec) or 0.0,
        plain_text = sliced.plain_text or "",
        speaker_color_hex = sliced.primary_color_hex or "#38bdf8",
        marker_style = m_style,
        speakers = sliced.speakers or {},
        sentence_cues = sliced.sentence_cues or {},
        word_cues = {},
        rendered_wav_path = "",
    }
    local ok, msg = Companion.insert_cue_payload(payload)
    Dock.status_msg = ok and ("Inserted story: " .. msg) or ("Error: " .. tostring(msg))
end

function Dock.insert_segment_from_index(seg)
    if not Dock.latest_index or type(seg) ~= "table" then return end
    local s_sec = tonumber(seg.start_sec) or 0.0
    local e_sec = tonumber(seg.end_sec) or s_sec
    local dur = math.max(0.05, e_sec - s_sec)
    local spk = tostring(seg.speaker or "Speaker")
    local txt = tostring(seg.text or "")
    local preview = string.sub(txt, 1, 45)
    if #txt > 45 then preview = preview .. "..." end
    local range_str = string.format("[%s - %s]", Dock.format_clock(s_sec), Dock.format_clock(e_sec))
    local m_style = Dock.active_marker_style()
    local c_hex = seg.color_hex or "#38bdf8"
    local phrase_prev = Companion.build_phrase_preview and Companion.build_phrase_preview(txt, spk) or preview

    local payload = {
        schema_version = "1.0",
        source_media_path = Dock.latest_index.source_media_path or "",
        project_path = Dock.latest_index.project_path or "",
        clip_type = "selection",
        title = spk .. ": " .. preview,
        take_name = string.format("%s: %s %s", spk, preview, range_str),
        start_sec = s_sec,
        end_sec = e_sec,
        duration_sec = dur,
        fade_in_sec = 0.0,
        fade_out_sec = 0.0,
        plain_text = string.format("[%s] %s: %s", Dock.format_clock(s_sec), spk, txt),
        speaker_color_hex = c_hex,
        marker_style = m_style,
        speakers = {
            {
                speaker = spk,
                rel_offset_sec = 0.0,
                abs_start_sec = s_sec,
                color_hex = c_hex,
            },
        },
        sentence_cues = {
            {
                preview = phrase_prev,
                speaker = spk,
                rel_offset_sec = 0.0,
                abs_start_sec = s_sec,
                color_hex = c_hex,
            },
        },
        word_cues = {},
        rendered_wav_path = "",
    }
    local ok, msg = Companion.insert_cue_payload(payload)
    Dock.status_msg = ok and ("Inserted segment: " .. msg) or ("Error: " .. tostring(msg))
end

--------------------------------------------------------------------------------
-- 3. ReaImGui Immediate-Mode Frame Loop (Strictly Stack-Balanced)
--------------------------------------------------------------------------------
function Dock.matches_filter(text, query)
    if not query or query == "" then return true end
    return string.find(string.lower(tostring(text or "")), string.lower(query), 1, true) ~= nil
end

function Dock.draw_contents(ctx)
    -- Top Action Bar
    if reaper.ImGui_Button(ctx, "Paste Copied Clip at Edit Cursor") then
        Dock.poll_sidecars(true)
        if Dock.latest_cue then
            local ok, msg = Companion.insert_cue_payload(Dock.latest_cue)
            Dock.status_msg = ok and ("Pasted: " .. tostring(msg)) or ("Error: " .. tostring(msg))
        else
            Dock.status_msg = "No clip cue found. Copy text or a story in RTVS3 first."
        end
    end
    reaper.ImGui_SameLine(ctx)
    if reaper.ImGui_Button(ctx, "Sync Trimmed Clips") then
        Dock.poll_sidecars(true)
        if Dock.latest_index and Companion.sync_trimmed_or_split_items then
            local synced = Companion.sync_trimmed_or_split_items(Dock.latest_index, true)
            Dock.status_msg = string.format("Synced %d clip(s) on timeline with transcript index.", synced or 0)
        else
            Dock.status_msg = "No transcript index available yet. Copy a clip in RTVS3 first."
        end
    end
    reaper.ImGui_SameLine(ctx)
    if reaper.ImGui_Button(ctx, "Refresh Sidecar") then
        Dock.poll_sidecars(true)
    end

    reaper.ImGui_TextWrapped(ctx, "Status: " .. tostring(Dock.status_msg))
    reaper.ImGui_Separator(ctx)

    -- Active Copied Cue Summary
    if Dock.latest_cue then
        reaper.ImGui_Text(ctx, "Latest Copied Cue: " .. tostring(Dock.latest_cue.take_name or Dock.latest_cue.title))
        local preview = tostring(Dock.latest_cue.plain_text or "")
        if #preview > 180 then
            preview = string.sub(preview, 1, 177) .. "..."
        end
        if preview ~= "" then
            reaper.ImGui_TextWrapped(ctx, preview)
        end
        reaper.ImGui_Separator(ctx)
    end

    -- Search Filter Input
    local changed, new_q = reaper.ImGui_InputText(ctx, "Filter Stories & Transcript", Dock.search_query)
    if changed then
        Dock.search_query = new_q
    end

    -- Stories & Transcript Browser
    local idx_data = Dock.latest_index
    if not idx_data then
        reaper.ImGui_TextWrapped(ctx, "No project transcript index loaded yet. Copy any story or text in RTVS3 to populate the live browser.")
        return
    end

    if type(idx_data.stories) == "table" and #idx_data.stories > 0 then
        reaper.ImGui_Text(ctx, string.format("Stories (%d):", #idx_data.stories))
        for i, st in ipairs(idx_data.stories) do
            local st_label = string.format(
                "%s [%s - %s]",
                tostring(st.title or ("Story " .. i)),
                Dock.format_clock(st.start_sec),
                Dock.format_clock(st.end_sec)
            )
            if Dock.matches_filter(st_label, Dock.search_query) then
                if reaper.ImGui_Button(ctx, "Insert##story_" .. tostring(i)) then
                    Dock.insert_story_from_index(st)
                end
                reaper.ImGui_SameLine(ctx)
                reaper.ImGui_TextWrapped(ctx, st_label)
            end
        end
        reaper.ImGui_Separator(ctx)
    end

    if type(idx_data.segments) == "table" and #idx_data.segments > 0 then
        reaper.ImGui_Text(ctx, string.format("Transcript Segments (%d):", #idx_data.segments))
        if reaper.ImGui_BeginChild(ctx, "rtvs_segments_scroll", 0, 0) then
            for i, seg in ipairs(idx_data.segments) do
                local line_str = string.format(
                    "[%s] %s: %s",
                    Dock.format_clock(seg.start_sec),
                    tostring(seg.speaker or "Speaker"),
                    tostring(seg.text or "")
                )
                if Dock.matches_filter(line_str, Dock.search_query) then
                    if reaper.ImGui_Button(ctx, "Insert##seg_" .. tostring(i)) then
                        Dock.insert_segment_from_index(seg)
                    end
                    reaper.ImGui_SameLine(ctx)
                    reaper.ImGui_TextWrapped(ctx, line_str)
                end
            end
            reaper.ImGui_EndChild(ctx)
        end
    end
end

function Dock.loop()
    Dock.poll_sidecars(false)
    reaper.ImGui_SetNextWindowSize(Dock.ctx, 580, 480, reaper.ImGui_Cond_FirstUseEver())
    local visible, open = reaper.ImGui_Begin(Dock.ctx, Dock.window_title, true)
    if visible then
        Dock.draw_contents(Dock.ctx)
    end
    reaper.ImGui_End(Dock.ctx)

    if open then
        reaper.defer(Dock.loop)
    elseif reaper.ImGui_DestroyContext then
        reaper.ImGui_DestroyContext(Dock.ctx)
    end
end

function Dock.start()
    if not reaper then return end
    if not reaper.ImGui_CreateContext then
        local ret = reaper.ShowMessageBox(
            "ReaImGui extension is not installed in REAPER.\n\n"
            .. "To use the dockable Transcript Browser, install 'ReaImGui: ReaScript binding for Dear ImGui' via ReaPack.\n\n"
            .. "Would you like to paste the latest RTVS3 copied clip at the edit cursor now instead?",
            "RTVS3 Transcript Dock — ReaImGui Required",
            4
        )
        if ret == 6 and Companion.main then
            Companion.main()
        end
        return
    end
    Dock.ctx = reaper.ImGui_CreateContext(Dock.window_title)
    Dock.poll_sidecars(true)
    reaper.defer(Dock.loop)
end

_G.RTVS3_Dock = Dock

if reaper and not _G.RTVS3_DOCK_LIBRARY_MODE then
    Dock.start()
end

return Dock
