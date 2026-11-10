-- @description RTVS3: Paste Transcript Selection / Story Clip at Edit Cursor
-- @version 1.2.0
-- @author Radio & TV Story Segmenter
-- @about
--   Companion ReaScript for Radio & TV Story Segmenter (RTVS3).
--   Reads the latest clip cue sidecar emitted by RTVS3 when copying a story
--   or transcript selection (from either the Transcript or Timeline view),
--   inserts the corresponding audio/video clip at the REAPER edit cursor,
--   populates the Take Name and Item Notes with formatted speaker-attributed
--   transcript text with clean line and paragraph breaks, applies optional
--   speaker color coding, injects configurable Take Markers (Speaker Changes,
--   Sentence Cues, or None), and dynamically re-syncs Item Notes and Take
--   Markers when clips are trimmed, extended, or split non-destructively.

local RTVS3 = {}

--------------------------------------------------------------------------------
-- 1. Pure-Lua Minimal JSON Decoder (Zero External Dependencies)
--------------------------------------------------------------------------------
local function skip_ws(str, idx)
    local _, next_idx = string.find(str, "^[ \t\r\n]*", idx)
    return (next_idx or idx - 1) + 1
end

local function codepoint_to_utf8(n)
    if n <= 0x7f then
        return string.char(n)
    elseif n <= 0x7ff then
        return string.char(math.floor(n / 64) + 192, n % 64 + 128)
    elseif n <= 0xffff then
        return string.char(
            math.floor(n / 4096) + 224,
            math.floor((n % 4096) / 64) + 128,
            n % 64 + 128
        )
    else
        return "?"
    end
end

local parse_value -- forward declaration

local function parse_string(str, idx)
    local out = {}
    local len = #str
    while idx <= len do
        local c = string.sub(str, idx, idx)
        if c == '"' then
            return table.concat(out), idx + 1
        elseif c == "\\" then
            idx = idx + 1
            local esc = string.sub(str, idx, idx)
            if esc == '"' or esc == "\\" or esc == "/" then
                out[#out + 1] = esc
            elseif esc == "b" then
                out[#out + 1] = "\b"
            elseif esc == "f" then
                out[#out + 1] = "\f"
            elseif esc == "n" then
                out[#out + 1] = "\n"
            elseif esc == "r" then
                out[#out + 1] = "\r"
            elseif esc == "t" then
                out[#out + 1] = "\t"
            elseif esc == "u" then
                local hex = string.sub(str, idx + 1, idx + 4)
                local cp = tonumber(hex, 16)
                if cp then
                    out[#out + 1] = codepoint_to_utf8(cp)
                    idx = idx + 4
                end
            else
                out[#out + 1] = esc
            end
            idx = idx + 1
        else
            local next_special = string.find(str, '["\\]', idx)
            if next_special then
                out[#out + 1] = string.sub(str, idx, next_special - 1)
                idx = next_special
            else
                out[#out + 1] = string.sub(str, idx)
                break
            end
        end
    end
    error("Unterminated JSON string")
end

local function parse_number(str, idx)
    local s, e = string.find(str, "^-?%d+%.?%d*[eE]?[+-]?%d*", idx)
    if not s or e < s then
        error("Invalid JSON number at position " .. tostring(idx))
    end
    local num = tonumber(string.sub(str, s, e))
    if num == nil then
        error("Malformed number at position " .. tostring(idx))
    end
    return num, e + 1
end

local function parse_array(str, idx)
    local arr = {}
    idx = skip_ws(str, idx)
    if string.sub(str, idx, idx) == "]" then
        return arr, idx + 1
    end
    while true do
        local val
        val, idx = parse_value(str, idx)
        arr[#arr + 1] = val
        idx = skip_ws(str, idx)
        local ch = string.sub(str, idx, idx)
        if ch == "]" then
            return arr, idx + 1
        elseif ch == "," then
            idx = skip_ws(str, idx + 1)
        else
            error("Expected ',' or ']' in JSON array at position " .. tostring(idx))
        end
    end
end

local function parse_object(str, idx)
    local obj = {}
    idx = skip_ws(str, idx)
    if string.sub(str, idx, idx) == "}" then
        return obj, idx + 1
    end
    while true do
        if string.sub(str, idx, idx) ~= '"' then
            error("Expected string key in JSON object at position " .. tostring(idx))
        end
        local key
        key, idx = parse_string(str, idx + 1)
        idx = skip_ws(str, idx)
        if string.sub(str, idx, idx) ~= ":" then
            error("Expected ':' after key in JSON object at position " .. tostring(idx))
        end
        idx = skip_ws(str, idx + 1)
        local val
        val, idx = parse_value(str, idx)
        obj[key] = val
        idx = skip_ws(str, idx)
        local ch = string.sub(str, idx, idx)
        if ch == "}" then
            return obj, idx + 1
        elseif ch == "," then
            idx = skip_ws(str, idx + 1)
        else
            error("Expected ',' or '}' in JSON object at position " .. tostring(idx))
        end
    end
end

parse_value = function(str, idx)
    idx = skip_ws(str, idx)
    local ch = string.sub(str, idx, idx)
    if ch == '"' then
        return parse_string(str, idx + 1)
    elseif ch == "{" then
        return parse_object(str, idx + 1)
    elseif ch == "[" then
        return parse_array(str, idx + 1)
    elseif ch == "t" and string.sub(str, idx, idx + 3) == "true" then
        return true, idx + 4
    elseif ch == "f" and string.sub(str, idx, idx + 4) == "false" then
        return false, idx + 5
    elseif ch == "n" and string.sub(str, idx, idx + 3) == "null" then
        return nil, idx + 4
    elseif ch == "-" or (ch >= "0" and ch <= "9") then
        return parse_number(str, idx)
    else
        error("Unexpected character '" .. tostring(ch) .. "' at position " .. tostring(idx))
    end
end

function RTVS3.decode_json(raw_str)
    if type(raw_str) ~= "string" or raw_str == "" then
        return nil, "Empty JSON input"
    end
    if string.sub(raw_str, 1, 3) == "\239\187\191" then
        raw_str = string.sub(raw_str, 4)
    end
    local ok, res = pcall(function()
        local val, _ = parse_value(raw_str, 1)
        return val
    end)
    if not ok then
        return nil, tostring(res)
    end
    return res, nil
end

--------------------------------------------------------------------------------
-- 2. Sidecar File Discovery, Time Formatting & Color Helpers
--------------------------------------------------------------------------------
function RTVS3.file_exists(path)
    if not path or path == "" then return false end
    local f = io.open(path, "rb")
    if f then
        f:close()
        return true
    end
    return false
end

function RTVS3.read_file_text(path)
    local f = io.open(path, "rb")
    if not f then return nil end
    local content = f:read("*a")
    f:close()
    return content
end

function RTVS3.format_clock(seconds)
    local sec = math.max(0.0, tonumber(seconds) or 0.0)
    local m = math.floor(sec / 60)
    local s = sec - (m * 60)
    return string.format("%02d:%04.1f", m, s)
end

function RTVS3.normalize_path(p)
    if type(p) ~= "string" then return "" end
    local norm = string.gsub(p, "\\", "/")
    norm = string.gsub(norm, "/+$", "")
    return string.lower(norm)
end

function RTVS3.get_candidate_cue_paths()
    local paths = {}
    local local_appdata = os.getenv("LOCALAPPDATA")
    if local_appdata and local_appdata ~= "" then
        paths[#paths + 1] = local_appdata .. "\\RadioTVStorySegmenter\\reaper_ipc\\latest_clip_cue.json"
    end
    local home = os.getenv("HOME")
    if home and home ~= "" then
        paths[#paths + 1] = home .. "/Library/Application Support/RadioTVStorySegmenter/reaper_ipc/latest_clip_cue.json"
        paths[#paths + 1] = home .. "/.local/share/RadioTVStorySegmenter/reaper_ipc/latest_clip_cue.json"
    end
    local tmp = os.getenv("TEMP") or os.getenv("TMP") or os.getenv("TMPDIR") or "/tmp"
    local sep = package.config:sub(1, 1)
    paths[#paths + 1] = tmp .. sep .. "rtvs3_reaper_cue.json"
    return paths
end

function RTVS3.get_candidate_index_paths()
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

function RTVS3.load_latest_cue_payload()
    local candidates = RTVS3.get_candidate_cue_paths()
    for _, path in ipairs(candidates) do
        local raw = RTVS3.read_file_text(path)
        if raw and #raw > 2 then
            local payload, _ = RTVS3.decode_json(raw)
            if payload and type(payload) == "table" then
                return payload, path
            end
        end
    end
    return nil, "No RTVS3 clip cue sidecar file found. Copy a story or transcript selection in RTVS3 first."
end

function RTVS3.load_latest_index_payload()
    local candidates = RTVS3.get_candidate_index_paths()
    for _, path in ipairs(candidates) do
        local raw = RTVS3.read_file_text(path)
        if raw and #raw > 2 then
            local payload, _ = RTVS3.decode_json(raw)
            if payload and type(payload) == "table" then
                return payload, path
            end
        end
    end
    return nil, nil
end

function RTVS3.hex_to_rgb(hex_str)
    if type(hex_str) ~= "string" then return 56, 189, 248 end
    local h = string.gsub(hex_str, "^#", "")
    if #h == 6 then
        local r = tonumber(string.sub(h, 1, 2), 16)
        local g = tonumber(string.sub(h, 3, 4), 16)
        local b = tonumber(string.sub(h, 5, 6), 16)
        if r and g and b then return r, g, b end
    end
    return 56, 189, 248
end

function RTVS3.rgb_to_reaper_native(r, g, b)
    if reaper and reaper.ColorToNative then
        return reaper.ColorToNative(r or 56, g or 189, b or 248) | 0x1000000
    end
    return 0
end

--------------------------------------------------------------------------------
-- 3. Take Marker Injection & Dynamic Transcript Range Slicer
--------------------------------------------------------------------------------
function RTVS3.clear_take_markers(take)
    if not reaper or not take then return end
    if reaper.GetNumTakeMarkers and reaper.DeleteTakeMarker then
        local num_m = reaper.GetNumTakeMarkers(take)
        for m_idx = num_m - 1, 0, -1 do
            reaper.DeleteTakeMarker(take, m_idx)
        end
    end
end

function RTVS3.apply_markers_to_take(take, start_sec, end_sec, use_rendered_wav, marker_style, speakers, sentence_cues, word_cues, fallback_hex, apply_color)
    if not reaper or not reaper.SetTakeMarker or not take then return end
    RTVS3.clear_take_markers(take)

    local style = string.lower(tostring(marker_style or "speakers"))
    if style == "none" then
        return
    end

    local use_color = (apply_color == nil or apply_color == true or apply_color == 1 or apply_color == "1")

    if style == "sentences" and type(sentence_cues) == "table" and #sentence_cues > 0 then
        local last_spk = nil
        for _, sc in ipairs(sentence_cues) do
            if type(sc) == "table" then
                local rel_off = tonumber(sc.rel_offset_sec) or 0.0
                local abs_pos = tonumber(sc.abs_start_sec) or (start_sec + rel_off)
                if abs_pos >= (start_sec - 0.05) and abs_pos <= (end_sec + 0.05) then
                    local marker_pos = use_rendered_wav and rel_off or abs_pos
                    local spk = tostring(sc.speaker or "")
                    local prev = tostring(sc.preview or "")
                    local label = prev
                    if spk ~= "" and spk ~= last_spk then
                        label = (prev ~= "" and prev ~= spk) and (spk .. ": " .. prev) or spk
                        last_spk = spk
                    elseif label == "" then
                        label = spk
                    end
                    local spk_color = 0
                    if use_color then
                        local sr, sg, sb = RTVS3.hex_to_rgb(sc.color_hex or fallback_hex)
                        spk_color = RTVS3.rgb_to_reaper_native(sr, sg, sb)
                    end
                    reaper.SetTakeMarker(take, -1, label, marker_pos, spk_color)
                end
            end
        end
    elseif type(speakers) == "table" then
        for _, spk in ipairs(speakers) do
            if type(spk) == "table" and spk.speaker then
                local rel_off = tonumber(spk.rel_offset_sec) or 0.0
                local abs_pos = tonumber(spk.abs_start_sec) or (start_sec + rel_off)
                if abs_pos >= (start_sec - 0.05) and abs_pos <= (end_sec + 0.05) then
                    local marker_pos = use_rendered_wav and rel_off or abs_pos
                    local spk_color = 0
                    if use_color then
                        local sr, sg, sb = RTVS3.hex_to_rgb(spk.color_hex or fallback_hex)
                        spk_color = RTVS3.rgb_to_reaper_native(sr, sg, sb)
                    end
                    reaper.SetTakeMarker(take, -1, tostring(spk.speaker), marker_pos, spk_color)
                end
            end
        end
    end

    if type(word_cues) == "table" and #word_cues > 0 then
        for _, w in ipairs(word_cues) do
            if type(w) == "table" and w.word and w.word ~= "" then
                local rel_off = tonumber(w.rel_offset_sec) or 0.0
                local abs_pos = tonumber(w.abs_start_sec) or (start_sec + rel_off)
                if abs_pos >= (start_sec - 0.05) and abs_pos <= (end_sec + 0.05) then
                    local marker_pos = use_rendered_wav and rel_off or abs_pos
                    reaper.SetTakeMarker(take, -1, tostring(w.word), marker_pos, 0)
                end
            end
        end
    end
end

function RTVS3.is_sentence_terminator(text)
    if not text or text == "" then return false end
    local cleaned = string.gsub(text, '[%s"\'%)%]%»\226\128\157\226\128\159\226\128\156\226\128\158]+$', "")
    if cleaned == "" then return false end
    if string.match(cleaned, "%.%.%.$") or string.match(cleaned, "\226\128\166$") then
        return true
    end
    if string.match(cleaned, "[%?%!]$") then
        return true
    end
    if string.match(cleaned, "%.$") then
        local last_word = string.lower(string.match(cleaned, "(%S+)%s*$") or "")
        local abbrevs = {
            ["mr."] = true, ["mrs."] = true, ["ms."] = true, ["dr."] = true,
            ["prof."] = true, ["sr."] = true, ["jr."] = true, ["vs."] = true,
            ["etc."] = true, ["e.g."] = true, ["i.e."] = true, ["u.s."] = true,
            ["inc."] = true, ["ltd."] = true, ["co."] = true, ["corp."] = true,
            ["st."] = true, ["ave."] = true, ["blvd."] = true,
            ["jan."] = true, ["feb."] = true, ["mar."] = true, ["apr."] = true,
            ["jun."] = true, ["jul."] = true, ["aug."] = true, ["sep."] = true,
            ["sept."] = true, ["oct."] = true, ["nov."] = true, ["dec."] = true,
        }
        if abbrevs[last_word] then
            return false
        end
        if string.len(last_word) == 2 and string.match(last_word, "^%a%.$") then
            return false
        end
        return true
    end
    return false
end

function RTVS3.build_phrase_preview(text, fallback_spk)
    local words = {}
    for w in string.gmatch(tostring(text or ""), "%S+") do
        words[#words + 1] = w
        if #words >= 6 then break end
    end
    local preview = table.concat(words, " ")
    local total_words = 0
    for _ in string.gmatch(tostring(text or ""), "%S+") do
        total_words = total_words + 1
    end
    if #preview > 42 then
        preview = string.sub(preview, 1, 39) .. "..."
    elseif total_words > 6 then
        preview = preview .. "..."
    end
    if preview == "" then
        preview = tostring(fallback_spk or "Speaker")
    end
    return preview
end

function RTVS3.slice_transcript_for_range(index_data, start_sec, end_sec, marker_style)
    local s_sec = math.max(0.0, tonumber(start_sec) or 0.0)
    local e_sec = math.max(s_sec, tonumber(end_sec) or s_sec)
    local lines = {}
    local speakers = {}
    local sentence_cues = {}
    local last_spk = nil
    local primary_hex = "#38bdf8"
    local current_turn_speaker = nil
    local current_turn_words = nil
    local current_turn_st = 0.0
    local last_seg_end = nil
    local prev_seg_ended_sentence = true
    local last_sentence_spk = nil
    local use_precomputed_sentences = (type(index_data) == "table" and type(index_data.sentences) == "table" and #index_data.sentences > 0)

    if use_precomputed_sentences then
        for _, sent in ipairs(index_data.sentences) do
            if type(sent) == "table" then
                local st = tonumber(sent.start_sec) or 0.0
                local en = tonumber(sent.end_sec) or st
                if en > s_sec and st < e_sec then
                    local spk = tostring(sent.speaker or "Speaker")
                    local c_hex = tostring(sent.color_hex or primary_hex)
                    if st >= (s_sec - 0.15) and st <= (e_sec + 0.05) then
                        local rel_off = math.max(0.0, st - s_sec)
                        sentence_cues[#sentence_cues + 1] = {
                            preview = tostring(sent.preview or RTVS3.build_phrase_preview(sent.text, spk)),
                            speaker = spk,
                            rel_offset_sec = rel_off,
                            abs_start_sec = st,
                            color_hex = c_hex,
                        }
                    end
                end
            end
        end
    end

    if type(index_data) == "table" and type(index_data.segments) == "table" then
        for _, seg in ipairs(index_data.segments) do
            if type(seg) == "table" then
                local seg_st = tonumber(seg.start_sec) or 0.0
                local seg_en = tonumber(seg.end_sec) or seg_st
                if seg_en > s_sec and seg_st < e_sec then
                    local spk = tostring(seg.speaker or "Speaker")
                    local c_hex = tostring(seg.color_hex or "#38bdf8")
                    local full_seg_txt = tostring(seg.text or "")
                    local seg_txt = full_seg_txt
                    local eff_st = math.max(s_sec, seg_st)
                    local is_para_start = (seg.is_paragraph_start == true or seg.is_paragraph_start == 1)

                    -- Resolve words array (or synthesize proportional word boundaries if missing)
                    local w_list = seg.words
                    if type(w_list) ~= "table" or #w_list == 0 then
                        w_list = {}
                        local tokens = {}
                        for t in string.gmatch(seg_txt, "%S+") do
                            tokens[#tokens + 1] = t
                        end
                        if #tokens > 0 then
                            local dur = math.max(0.01, seg_en - seg_st)
                            local tok_dur = dur / #tokens
                            for t_idx, tok in ipairs(tokens) do
                                w_list[#w_list + 1] = {
                                    word = tok,
                                    start = seg_st + ((t_idx - 1) * tok_dur),
                                    ["end"] = seg_st + (t_idx * tok_dur),
                                }
                            end
                        end
                    end

                    -- Slice exact words overlapping [s_sec, e_sec]
                    if type(w_list) == "table" and #w_list > 0 then
                        local sliced_words = {}
                        local first_w_st = nil
                        for _, w_obj in ipairs(w_list) do
                            if type(w_obj) == "table" then
                                local w_st = tonumber(w_obj.start) or seg_st
                                local w_en = tonumber(w_obj["end"]) or w_st
                                local w_str = tostring(w_obj.word or "")
                                if w_str ~= "" and w_en > s_sec and w_st < e_sec then
                                    sliced_words[#sliced_words + 1] = w_str
                                    if not first_w_st then
                                        first_w_st = math.max(s_sec, w_st)
                                    end
                                end
                            end
                        end
                        if #sliced_words > 0 then
                            seg_txt = table.concat(sliced_words, " ")
                            eff_st = first_w_st or eff_st
                        else
                            seg_txt = ""
                        end
                    end

                    if seg_txt ~= "" then
                        local rel_off = math.max(0.0, eff_st - s_sec)
                        local gap = eff_st - (last_seg_end or eff_st)

                        -- Group consecutive sentences into RTVS-matching paragraphs
                        if current_turn_speaker ~= nil and (spk ~= current_turn_speaker or is_para_start or gap > 3.5) then
                            if current_turn_words and #current_turn_words > 0 then
                                local turn_body = table.concat(current_turn_words, " ")
                                lines[#lines + 1] = string.format("[%s] %s:\r\n%s", RTVS3.format_clock(current_turn_st), current_turn_speaker, turn_body)
                            end
                            current_turn_words = { seg_txt }
                            current_turn_speaker = spk
                            current_turn_st = eff_st
                        elseif current_turn_speaker == nil then
                            current_turn_words = { seg_txt }
                            current_turn_speaker = spk
                            current_turn_st = eff_st
                        else
                            current_turn_words[#current_turn_words + 1] = seg_txt
                        end

                        last_seg_end = tonumber(seg.end_sec or seg["end"]) or eff_st

                        if spk ~= last_spk or #speakers == 0 then
                            speakers[#speakers + 1] = {
                                speaker = spk,
                                rel_offset_sec = rel_off,
                                abs_start_sec = eff_st,
                                color_hex = c_hex,
                            }
                            if #speakers == 1 then
                                primary_hex = c_hex
                            end
                            last_spk = spk
                        end

                        if not use_precomputed_sentences then
                            local is_spk_change = (spk ~= last_sentence_spk)
                            local is_sentence_start = (#sentence_cues == 0) or is_spk_change or prev_seg_ended_sentence

                            if is_sentence_start and seg_st >= (s_sec - 0.15) then
                                local sent_rel = math.max(0.0, seg_st - s_sec)
                                sentence_cues[#sentence_cues + 1] = {
                                    preview = tostring(seg.preview or RTVS3.build_phrase_preview(full_seg_txt, spk)),
                                    speaker = spk,
                                    rel_offset_sec = sent_rel,
                                    abs_start_sec = seg_st,
                                    color_hex = c_hex,
                                }
                                last_sentence_spk = spk
                            end

                            prev_seg_ended_sentence = RTVS3.is_sentence_terminator(full_seg_txt)
                        end
                    end
                end
            end
        end
    end

    if current_turn_speaker ~= nil and current_turn_words and #current_turn_words > 0 then
        local turn_body = table.concat(current_turn_words, " ")
        lines[#lines + 1] = string.format("[%s] %s:\r\n%s", RTVS3.format_clock(current_turn_st), current_turn_speaker, turn_body)
    end

    -- Return formatted text with blank lines (\r\n\r\n) between paragraph blocks
    return {
        plain_text = table.concat(lines, "\r\n\r\n"),
        speakers = speakers,
        sentence_cues = sentence_cues,
        primary_color_hex = primary_hex,
        marker_style = marker_style or "speakers",
    }
end

--------------------------------------------------------------------------------
-- 4. Track Selection, Clip Insertion & Non-Destructive Trim/Split Auto-Sync
--------------------------------------------------------------------------------
function RTVS3.get_or_create_target_track()
    local sel_track = reaper.GetSelectedTrack(0, 0)
    if sel_track then
        return sel_track
    end
    local track_count = reaper.CountTracks(0)
    for i = 0, track_count - 1 do
        local tr = reaper.GetTrack(0, i)
        local _, name = reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", "", false)
        if name == "RTVS3 Assemble" then
            return tr
        end
    end
    reaper.InsertTrackAtIndex(track_count, true)
    local new_tr = reaper.GetTrack(0, track_count)
    if new_tr then
        reaper.GetSetMediaTrackInfo_String(new_tr, "P_NAME", "RTVS3 Assemble", true)
    end
    return new_tr
end

function RTVS3.insert_cue_payload(payload)
    if not reaper then
        return false, "REAPER API environment is not active."
    end
    if type(payload) ~= "table" then
        return false, "Invalid clip cue payload."
    end

    -- Prefer master source_media_path so clips in REAPER can be non-destructively trimmed/extended
    local use_rendered_wav = false
    local media_path = ""
    if payload.source_media_path and payload.source_media_path ~= "" and RTVS3.file_exists(payload.source_media_path) then
        media_path = payload.source_media_path
        use_rendered_wav = false
    elseif payload.rendered_wav_path and payload.rendered_wav_path ~= "" and RTVS3.file_exists(payload.rendered_wav_path) then
        media_path = payload.rendered_wav_path
        use_rendered_wav = true
    else
        media_path = payload.source_media_path or payload.rendered_wav_path or ""
    end

    if media_path == "" or not RTVS3.file_exists(media_path) then
        return false, "Source media file not found on disk:\n" .. tostring(media_path)
    end

    local start_sec = tonumber(payload.start_sec) or 0.0
    local end_sec = tonumber(payload.end_sec) or start_sec
    local duration_sec = tonumber(payload.duration_sec) or math.max(0.05, end_sec - start_sec)
    if duration_sec <= 0 then
        duration_sec = 0.1
    end

    reaper.Undo_BeginBlock()
    reaper.PreventUIRefresh(1)

    local track = RTVS3.get_or_create_target_track()
    local cursor_pos = reaper.GetCursorPosition()

    local item = reaper.AddMediaItemToTrack(track)
    local take = reaper.AddTakeToMediaItem(item)
    local pcm_src = reaper.PCM_Source_CreateFromFile(media_path)
    reaper.SetMediaItemTake_Source(take, pcm_src)

    -- Set timeline geometry & take start offset
    reaper.SetMediaItemInfo_Value(item, "D_POSITION", cursor_pos)
    reaper.SetMediaItemInfo_Value(item, "D_LENGTH", duration_sec)
    reaper.SetMediaItemTakeInfo_Value(take, "D_STARTOFFS", use_rendered_wav and 0.0 or start_sec)

    -- Apply non-destructive fades if specified on the RTVS3 story
    local fade_in = tonumber(payload.fade_in_sec) or 0.0
    local fade_out = tonumber(payload.fade_out_sec) or 0.0
    if fade_in > 0 then
        reaper.SetMediaItemInfo_Value(item, "D_FADEINLEN", math.min(fade_in, duration_sec * 0.5))
    end
    if fade_out > 0 then
        reaper.SetMediaItemInfo_Value(item, "D_FADEOUTLEN", math.min(fade_out, duration_sec * 0.5))
    end

    -- 2.3 Populate Take Name & Verbatim Transcript Item Notes with paragraph breaks
    local base_title = tostring(payload.title or "RTVS3 Clip")
    local take_name = tostring(payload.take_name or base_title)
    local plain_text = tostring(payload.plain_text or "")
    local marker_style = tostring(payload.marker_style or "speakers")

    -- Check if speaker color coding should be applied
    local apply_color = true
    if payload.apply_speaker_color ~= nil then
        apply_color = (payload.apply_speaker_color == true or payload.apply_speaker_color == 1 or payload.apply_speaker_color == "1")
    end

    reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", take_name, true)
    if plain_text ~= "" then
        local notes_crlf = string.gsub(string.gsub(plain_text, "\r\n", "\n"), "\n", "\r\n")
        reaper.GetSetMediaItemInfo_String(item, "P_NOTES", notes_crlf, true)
    end

    -- Tag MediaItem with RTVS3 Extended State for live Trim/Extend/Split Sync
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_MANAGED", "1", true)
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_BASE_TITLE", base_title, true)
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_MARKER_STYLE", marker_style, true)
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_SOURCE_MEDIA", tostring(payload.source_media_path or media_path), true)
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_USE_RENDERED_WAV", use_rendered_wav and "1" or "0", true)
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_LAST_RANGE", string.format("%.4f:%.4f", start_sec, end_sec), true)
    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_APPLY_COLOR", apply_color and "1" or "0", true)

    -- Apply speaker color coding to take/item (if enabled in preferences)
    if apply_color then
        local r, g, b = 56, 189, 248
        if type(payload.reaper_native_color_rgb) == "table" and #payload.reaper_native_color_rgb >= 3 then
            r = tonumber(payload.reaper_native_color_rgb[1]) or 56
            g = tonumber(payload.reaper_native_color_rgb[2]) or 189
            b = tonumber(payload.reaper_native_color_rgb[3]) or 248
        elseif payload.speaker_color_hex then
            r, g, b = RTVS3.hex_to_rgb(payload.speaker_color_hex)
        end
        local native_color = RTVS3.rgb_to_reaper_native(r, g, b)
        if native_color ~= 0 then
            reaper.SetMediaItemInfo_Value(item, "I_CUSTOMCOLOR", native_color)
            reaper.SetMediaItemTakeInfo_Value(take, "I_CUSTOMCOLOR", native_color)
        end
    else
        reaper.SetMediaItemInfo_Value(item, "I_CUSTOMCOLOR", 0)
        reaper.SetMediaItemTakeInfo_Value(take, "I_CUSTOMCOLOR", 0)
    end

    -- 2.4 Inject Take Markers according to marker_style ("speakers", "sentences", or "none")
    RTVS3.apply_markers_to_take(
        take,
        start_sec,
        end_sec,
        use_rendered_wav,
        marker_style,
        payload.speakers,
        payload.sentence_cues,
        payload.word_cues,
        payload.speaker_color_hex,
        apply_color
    )

    -- Select only the newly inserted item and advance the edit cursor
    reaper.SelectAllMediaItems(0, false)
    reaper.SetMediaItemSelected(item, true)
    reaper.SetEditCurPos(cursor_pos + duration_sec, true, false)

    reaper.PreventUIRefresh(-1)
    reaper.UpdateArrange()
    reaper.Undo_EndBlock("RTVS3: Paste Transcript Selection / Story Clip", -1)
    return true, take_name
end

function RTVS3.parse_range_pair(range_str)
    if type(range_str) ~= "string" or range_str == "" then return nil, nil end
    local s, e = string.match(range_str, "^([%-%d%.]+):([%-%d%.]+)$")
    if s and e then
        return tonumber(s), tonumber(e)
    end
    return nil, nil
end

function RTVS3.sync_trimmed_or_split_items(index_data, force_all)
    if not reaper or type(index_data) ~= "table" or type(index_data.segments) ~= "table" then
        return 0
    end

    local item_count = reaper.CountMediaItems(0)
    if item_count <= 0 then return 0 end

    local index_media_norm = RTVS3.normalize_path(index_data.source_media_path or "")
    local updated_count = 0

    for i = 0, item_count - 1 do
        local item = reaper.GetMediaItem(0, i)
        local take = item and reaper.GetActiveTake(item) or nil
        if take then
            local _, is_managed = reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_MANAGED", "", false)
            local matches_source = (is_managed == "1")

            if not matches_source and index_media_norm ~= "" and reaper.GetMediaItemTake_Source and reaper.GetMediaSourceFileName then
                local src = reaper.GetMediaItemTake_Source(take)
                if src then
                    local src_file = reaper.GetMediaSourceFileName(src, "")
                    if RTVS3.normalize_path(src_file) == index_media_norm then
                        matches_source = true
                    end
                end
            end

            if matches_source then
                local start_offs = tonumber(reaper.GetMediaItemTakeInfo_Value(take, "D_STARTOFFS")) or 0.0
                local item_len = tonumber(reaper.GetMediaItemInfo_Value(item, "D_LENGTH")) or 0.0
                local playrate = tonumber(reaper.GetMediaItemTakeInfo_Value(take, "D_PLAYRATE")) or 1.0
                if playrate <= 0 then playrate = 1.0 end

                local new_start = math.max(0.0, start_offs)
                local new_end = new_start + (item_len / playrate)

                local _, last_range = reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_LAST_RANGE", "", false)
                local old_start, old_end = RTVS3.parse_range_pair(last_range)

                local needs_sync = false
                if force_all then
                    needs_sync = true
                elseif old_start and old_end then
                    if math.abs(new_start - old_start) > 0.005 or math.abs(new_end - old_end) > 0.005 then
                        needs_sync = true
                    end
                elseif is_managed == "1" then
                    needs_sync = true
                end

                if needs_sync then
                    local _, marker_style = reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_MARKER_STYLE", "", false)
                    if not marker_style or marker_style == "" then
                        marker_style = "speakers"
                    end
                    local _, base_title = reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_BASE_TITLE", "", false)
                    if not base_title or base_title == "" then
                        local _, cur_name = reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", "", false)
                        base_title = string.gsub(tostring(cur_name or "RTVS3 Clip"), "%s*%[%d+:%d+%.%d+%s*%-%s*%d+:%d+%.%d+%]$", "")
                    end

                    local sliced = RTVS3.slice_transcript_for_range(index_data, new_start, new_end, marker_style)
                    local new_range_label = string.format("[%s - %s]", RTVS3.format_clock(new_start), RTVS3.format_clock(new_end))
                    local new_take_name = base_title .. " " .. new_range_label

                    reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", new_take_name, true)
                    reaper.GetSetMediaItemInfo_String(item, "P_NOTES", sliced.plain_text or "", true)
                    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_MANAGED", "1", true)
                    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_BASE_TITLE", base_title, true)
                    reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_LAST_RANGE", string.format("%.4f:%.4f", new_start, new_end), true)

                    -- Check color setting
                    local _, apply_col_str = reaper.GetSetMediaItemInfo_String(item, "P_EXT:RTVS3_APPLY_COLOR", "", false)
                    local item_apply_color = (apply_col_str == "1")
                    if item_apply_color and sliced.primary_color_hex then
                        local cr, cg, cb = RTVS3.hex_to_rgb(sliced.primary_color_hex)
                        local nat_col = RTVS3.rgb_to_reaper_native(cr, cg, cb)
                        if nat_col ~= 0 then
                            reaper.SetMediaItemInfo_Value(item, "I_CUSTOMCOLOR", nat_col)
                            reaper.SetMediaItemTakeInfo_Value(take, "I_CUSTOMCOLOR", nat_col)
                        end
                    else
                        reaper.SetMediaItemInfo_Value(item, "I_CUSTOMCOLOR", 0)
                        reaper.SetMediaItemTakeInfo_Value(take, "I_CUSTOMCOLOR", 0)
                    end

                    local sync_notes_crlf = string.gsub(string.gsub(sliced.plain_text or "", "\r\n", "\n"), "\n", "\r\n")
                    reaper.GetSetMediaItemInfo_String(item, "P_NOTES", sync_notes_crlf, true)

                    RTVS3.apply_markers_to_take(
                        take,
                        new_start,
                        new_end,
                        false,
                        marker_style,
                        sliced.speakers,
                        sliced.sentence_cues,
                        nil,
                        sliced.primary_color_hex,
                        item_apply_color
                    )
                    updated_count = updated_count + 1
                end
            end
        end
    end

    if updated_count > 0 and reaper.UpdateArrange then
        reaper.UpdateArrange()
    end
    return updated_count
end

local function auto_sync_watcher_loop()
    if not reaper then return end
    local cur_token = reaper.GetExtState("RTVS3", "WATCHER_TOKEN")
    if cur_token == "" or cur_token ~= RTVS3._watcher_token then
        return
    end

    local cur_time = reaper.time_precise()
    if not _G.RTVS3_LAST_AUTO_CHECK or (cur_time - _G.RTVS3_LAST_AUTO_CHECK) >= 0.35 then
        _G.RTVS3_LAST_AUTO_CHECK = cur_time
        local index_data = RTVS3.load_latest_index_payload()
        if index_data then
            RTVS3.sync_trimmed_or_split_items(index_data, false)
        end
    end

    reaper.defer(auto_sync_watcher_loop)
end

function RTVS3.start_background_watcher()
    if not reaper then return end
    -- Terminate any legacy AUTO_SYNC_ACTIVE loop from older sessions
    reaper.SetExtState("RTVS3", "AUTO_SYNC_ACTIVE", "0", false)
    local new_token = tostring(reaper.time_precise and reaper.time_precise() or os.clock())
    RTVS3._watcher_token = new_token
    reaper.SetExtState("RTVS3", "WATCHER_TOKEN", new_token, false)
    reaper.defer(auto_sync_watcher_loop)
end

function RTVS3.main()
    if not reaper then return end
    local payload, path_or_err = RTVS3.load_latest_cue_payload()
    local pasted = false
    if payload then
        local ok, msg = RTVS3.insert_cue_payload(payload)
        if ok then
            pasted = true
        else
            reaper.ShowMessageBox(tostring(msg), "RTVS3 REAPER Companion", 0)
        end
    end

    local index_data, _ = RTVS3.load_latest_index_payload()
    if index_data then
        RTVS3.sync_trimmed_or_split_items(index_data, true)
        RTVS3.start_background_watcher()
    elseif pasted then
        RTVS3.start_background_watcher()
    else
        reaper.ShowMessageBox(tostring(path_or_err), "RTVS3 REAPER Companion", 0)
    end
end

_G.RTVS3_Companion = RTVS3

if reaper and not _G.RTVS3_COMPANION_LIBRARY_MODE then
    RTVS3.main()
end

return RTVS3
