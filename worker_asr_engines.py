"""worker_asr_engines.py - Faster-Whisper, CTranslate2 & Sherpa-ONNX ASR Engines.

Provides:
- Sherpa-ONNX runtime execution for Parakeet TDT, Spanish FastConformer & Multilingual FastConformer
- Conformer acoustic boundary chunking (< 26s per chunk at low-energy pause points)
- Faster-Whisper / CTranslate2 local execution with word-level timestamps and VAD filtering
- Pure-Python platform application data and model directory resolvers (no PySide6 dependencies)
- Physical CPU core thread pool calculation
- Rapid offline language compatibility probing
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from worker_diarization_engine import normalize_audio_for_diarization

# Callback for IPC message emission; default to stdout JSON
_EMIT_FN: Optional[Callable[..., None]] = None


def set_emit_callback(fn: Callable[..., None]):
    """Set custom IPC emitter function."""
    global _EMIT_FN
    _EMIT_FN = fn


def _emit(message_type: str, **payload):
    if _EMIT_FN is not None:
        _EMIT_FN(message_type, **payload)
    else:
        message = {"type": message_type, **payload}
        sys.stdout.buffer.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
        sys.stdout.buffer.flush()


def _patch_av_open():
    """Monkey-patch PyAV's av.open to strip 'metadata_errors' if passed."""
    try:
        import av
        if hasattr(av, "open") and not getattr(av.open, "_is_patched", False):
            orig_open = av.open

            def patched_open(*args, **kwargs):
                kwargs.pop("metadata_errors", None)
                return orig_open(*args, **kwargs)

            patched_open._is_patched = True
            av.open = patched_open
    except Exception:
        pass


def get_optimal_transcription_threads() -> int:
    """Calculate optimal CPU threads for faster-whisper / CTranslate2 / ONNX.
    Uses physical cores instead of logical hyperthreads to avoid SMT stalls
    and cache thrashing, capped between 1 and 8.
    """
    try:
        import psutil
        count = psutil.cpu_count(logical=False)
        if count and count > 0:
            return max(1, min(int(count), 8))
    except Exception:
        pass
    try:
        count = os.cpu_count()
        if count and count > 0:
            physical = count // 2 if count > 2 else count
            return max(1, min(physical, 8))
    except Exception:
        pass
    return 4


def get_app_data_dir_pure() -> Path:
    """Return platform-specific app data directory in pure Python without PySide6."""
    internal_app_id = "RadioTVStorySegmenter"
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            base = os.path.expanduser("~/AppData/Local")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME")
        if not base:
            base = os.path.expanduser("~/.local/share")
    p = Path(base) / internal_app_id
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


def get_models_storage_dir_pure() -> Path:
    """Return models storage directory in pure Python without PySide6."""
    env_dir = os.environ.get("PRS_MODELS_DIR")
    if env_dir:
        return Path(env_dir)
    p = get_app_data_dir_pure() / "models"
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return p


def is_onnx_model_available(model_name: str) -> bool:
    """Check if sherpa-onnx runtime and target model files exist on disk."""
    try:
        import sherpa_onnx
    except Exception:
        try:
            from bootstrap import ensure_sherpa_onnx_runtime
            if not ensure_sherpa_onnx_runtime():
                return False
            import sherpa_onnx
        except Exception:
            sys.stderr.write("[ONNX CHECK] sherpa_onnx runtime is not installed or loadable\n")
            return False

    try:
        m_str = str(model_name).lower()
        folder_name = "parakeet_onnx"
        if ("fastconformer" in m_str and ("es" in m_str or "spanish" in m_str)) or "fastconformer_es" in m_str or "es-onnx" in m_str or "fastconformer-es" in m_str:
            folder_name = "fastconformer_es_onnx"
        elif "multilingual" in m_str:
            folder_name = "fastconformer_multilingual_onnx"

        search_dirs = []
        env_mdir = os.environ.get("PRS_MODELS_DIR")
        if env_mdir:
            p_env = Path(env_mdir)
            search_dirs.append(p_env / folder_name)
            if p_env.name == folder_name or (p_env / "tokens.txt").is_file():
                search_dirs.append(p_env)
        try:
            msd = get_models_storage_dir_pure()
            search_dirs.append(msd / folder_name)
            if msd.name == folder_name or (msd / "tokens.txt").is_file():
                search_dirs.append(msd)
            appd = get_app_data_dir_pure() / "models" / folder_name
            search_dirs.append(appd)
        except Exception:
            pass
        search_dirs.append(Path(__file__).resolve().parent / "models" / folder_name)

        seen = set()
        for raw in search_dirs:
            try:
                root = Path(raw).resolve()
            except Exception:
                continue
            if str(root) in seen or not root.is_dir():
                continue
            seen.add(str(root))
            candidates = [root] + [p for p in root.rglob("*") if p.is_dir()]
            for candidate in candidates:
                has_tokens = any(f.is_file() and f.name == "tokens.txt" for f in candidate.rglob("*"))
                has_onnx = any(f.is_file() and f.stat().st_size > 1024 and f.name.endswith(".onnx") for f in candidate.rglob("*"))
                if has_tokens and has_onnx:
                    return True
    except Exception:
        pass
    return False


def transcribe_parakeet_onnx(audio_file, model_name="parakeet-onnx", detected_lang=None, detected_confidence=0.0, initial_prompt="", beam_size=5):
    """Run installed ONNX models (Parakeet TDT, Spanish FastConformer, Multilingual FastConformer) through sherpa-onnx."""
    model_key = str(model_name).lower()
    is_spanish_only_model = "fastconformer" in model_key and ("es" in model_key or "spanish" in model_key) and "multi" not in model_key
    if is_spanish_only_model:
        model_lang = "es"
    elif detected_lang:
        model_lang = detected_lang.lower()
    else:
        model_lang = "en"

    _emit("progress", percent=5, message=f"Loading ONNX transcription engine ({model_name})...")
    try:
        import numpy as np
        import sherpa_onnx
    except Exception as exc:
        try:
            from bootstrap import ensure_sherpa_onnx_runtime
            if ensure_sherpa_onnx_runtime():
                import numpy as np
                import sherpa_onnx
            else:
                raise exc
        except Exception:
            _emit("progress", percent=5, message=f"ONNX runtime (sherpa-onnx) is not available ({exc}). Falling back to Whisper Small...")
            return transcribe(audio_file, model_name="small", initial_prompt=initial_prompt, beam_size=beam_size)

    models_dir = os.environ.get("PRS_MODELS_DIR")
    search_dirs = []
    folder_name = "parakeet_onnx"
    if ("fastconformer" in model_key and ("es" in model_key or "spanish" in model_key)) or "fastconformer_es" in model_key or "es-onnx" in model_key or "fastconformer-es" in model_key:
        folder_name = "fastconformer_es_onnx"
    elif "multilingual" in model_key:
        folder_name = "fastconformer_multilingual_onnx"

    if models_dir:
        search_dirs.append(Path(models_dir) / folder_name)
    try:
        search_dirs.extend([
            get_models_storage_dir_pure() / folder_name,
            get_app_data_dir_pure() / "models" / folder_name,
        ])
    except Exception:
        pass
    search_dirs.append(Path(__file__).resolve().parent / "models" / folder_name)

    model_dir = None
    seen = set()
    for raw in search_dirs:
        try:
            root = Path(raw).resolve()
        except Exception:
            continue
        if str(root) in seen or not root.is_dir():
            continue
        seen.add(str(root))
        candidates = [root] + [p for p in root.rglob("*") if p.is_dir()]
        for candidate in candidates:
            has_tokens = any(f.is_file() and f.name == "tokens.txt" for f in candidate.rglob("*"))
            has_onnx = any(f.is_file() and f.stat().st_size > 1024 and f.name.endswith(".onnx") for f in candidate.rglob("*"))
            if has_tokens and has_onnx:
                model_dir = candidate
                break
        if model_dir:
            break

    if model_dir is None:
        _emit("error", message=(f"{model_name} model files are missing or incomplete in {folder_name}. "
                                "Please use Manage Models to repair/reinstall the model."))
        return 4

    temp_dir = None
    try:
        _emit("progress", percent=10, message=f"Preparing 16 kHz mono audio for {model_name}...")
        norm_result = normalize_audio_for_diarization(audio_file)
        if isinstance(norm_result[0], tempfile.TemporaryDirectory):
            temp_dir, norm_wav = norm_result[0], norm_result[1]
        else:
            norm_wav, temp_dir = norm_result[0], norm_result[1]
        import wave
        with wave.open(str(norm_wav), "rb") as wf:
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            audio_bytes = wf.readframes(nframes)
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            duration_sec = max(0.1, nframes / float(framerate))
        if framerate != 16000 or channels != 1 or width != 2:
            raise RuntimeError(f"Normalized audio has unexpected format: {framerate} Hz, {channels} channel(s), {width * 8}-bit.")
        samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

        if "fastconformer-es" in str(model_name).lower():
            display_model_name = "Spanish FastConformer ONNX"
        elif "fastconformer-multilingual" in str(model_name).lower():
            display_model_name = "Multilingual FastConformer ONNX"
        elif "parakeet" in str(model_name).lower():
            display_model_name = "Parakeet ONNX"
        else:
            display_model_name = str(model_name)

        threads = get_optimal_transcription_threads()
        token_matches = list(model_dir.rglob("tokens.txt"))
        tokens_file = str(token_matches[0]) if token_matches else str(model_dir / "tokens.txt")

        encoder_matches = [
            f for f in model_dir.rglob("*.onnx")
            if f.is_file() and f.stat().st_size > 1024 and ("encoder" in f.name.lower() or "parakeet" in f.name.lower())
        ]
        if encoder_matches:
            encoder_file = str(encoder_matches[0])
            parent_dir = encoder_matches[0].parent

            decoder_matches = [f for f in parent_dir.rglob("*.onnx") if f.is_file() and "decoder" in f.name.lower()]
            if not decoder_matches:
                decoder_matches = [f for f in model_dir.rglob("*.onnx") if f.is_file() and "decoder" in f.name.lower()]
            decoder_file = str(decoder_matches[0]) if decoder_matches else str(parent_dir / "decoder.int8.onnx")

            joiner_matches = [f for f in parent_dir.rglob("*.onnx") if f.is_file() and "joiner" in f.name.lower()]
            if not joiner_matches:
                joiner_matches = [f for f in model_dir.rglob("*.onnx") if f.is_file() and "joiner" in f.name.lower()]
            joiner_file = str(joiner_matches[0]) if joiner_matches else str(parent_dir / "joiner.int8.onnx")

            feature_dim = 80
            try:
                import onnxruntime as ort
                probe = ort.InferenceSession(encoder_file, providers=["CPUExecutionProvider"])
                for meta in probe.get_inputs():
                    shape = getattr(meta, "shape", None) or []
                    if meta.name == "audio_signal" and len(shape) >= 2:
                        candidate = shape[1]
                        if isinstance(candidate, int) and candidate in (80, 128):
                            feature_dim = candidate
                        break
            except Exception:
                pass
            _emit("progress", percent=20, message=f"Initializing {display_model_name} engine ({threads} CPU threads, {feature_dim}-bin features)...")
            recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                encoder=encoder_file,
                decoder=decoder_file,
                joiner=joiner_file,
                tokens=tokens_file,
                num_threads=threads, sample_rate=16000, feature_dim=feature_dim,
                decoding_method="greedy_search", provider="cpu", model_type="nemo_transducer")
        else:
            onnx_files = [f for f in model_dir.rglob("*.onnx") if f.is_file() and f.stat().st_size > 1024]
            onnx_model_path = str(onnx_files[0]) if onnx_files else str(model_dir / "model.int8.onnx")
            _emit("progress", percent=20, message=f"Initializing {display_model_name} engine ({threads} CPU threads)...")
            recognizer = sherpa_onnx.OfflineRecognizer.from_nemo_ctc(
                model=onnx_model_path,
                tokens=tokens_file,
                num_threads=threads, sample_rate=16000, feature_dim=80,
                decoding_method="greedy_search", provider="cpu")

        _emit("progress", percent=35, message=f"Transcribing with {display_model_name} ({duration_sec:.1f}s of audio)...")

        total_samples = len(samples)
        target_chunk_samples = int(22.0 * 16000)
        max_chunk_samples = int(26.0 * 16000)
        search_radius = int(1.5 * 16000)
        frame_len = int(0.05 * 16000)  # 50ms search resolution

        start_idx = 0
        chunk_indices = []
        while start_idx < total_samples:
            if total_samples - start_idx <= max_chunk_samples:
                chunk_indices.append((start_idx, total_samples))
                break

            nominal_cut = start_idx + target_chunk_samples
            s_start = max(start_idx, nominal_cut - search_radius)
            s_end = min(total_samples, nominal_cut + search_radius)

            search_region = samples[s_start:s_end]
            usable_len = len(search_region) - (len(search_region) % frame_len)
            if usable_len >= frame_len:
                frames = search_region[:usable_len].reshape(-1, frame_len)
                energies = np.mean(frames ** 2, axis=1)
                best_frame = int(np.argmin(energies))
                cut_point = s_start + (best_frame * frame_len) + (frame_len // 2)
            else:
                cut_point = min(total_samples, nominal_cut)

            chunk_indices.append((start_idx, cut_point))
            start_idx = cut_point

        def is_word_boundary(token_str):
            return str(token_str).startswith(("▁", " ", "\t", "\n"))

        all_segments = []
        all_words = []
        text_parts = []

        for chunk_idx, (c_start, c_end) in enumerate(chunk_indices):
            chunk_samples = samples[c_start:c_end]
            chunk_start_sec = c_start / 16000.0
            chunk_end_sec = c_end / 16000.0

            pct = min(95, int(35 + (c_end / total_samples) * 55))
            _emit("progress", percent=pct,
                  message=f"Transcribing with {display_model_name} ({chunk_end_sec:.1f}s / {duration_sec:.1f}s)...")

            stream = recognizer.create_stream()
            stream.accept_waveform(16000, chunk_samples)
            recognizer.decode_stream(stream)
            res = stream.result

            c_text = str(getattr(res, "text", "") or "").strip()
            c_tokens = list(getattr(res, "tokens", []) or [])
            c_timestamps = list(getattr(res, "timestamps", []) or [])

            if c_text:
                text_parts.append(c_text)

            chunk_words = []
            if c_tokens and c_timestamps and len(c_tokens) == len(c_timestamps):
                if not is_word_boundary(c_tokens[0]):
                    c_tokens[0] = " " + str(c_tokens[0])

                token_groups = []
                current = []
                for tok, ts in zip(c_tokens, c_timestamps):
                    s_tok = str(tok)
                    abs_ts = round(chunk_start_sec + max(0.0, float(ts)), 2)
                    if is_word_boundary(s_tok) and current:
                        token_groups.append(current)
                        current = []
                    current.append((s_tok.lstrip("▁ \t\n"), abs_ts))
                if current:
                    token_groups.append(current)

                for group_idx, group in enumerate(token_groups):
                    word_text = "".join(part for part, _ in group).strip()
                    if not word_text:
                        continue
                    word_start = group[0][1]
                    if group_idx + 1 < len(token_groups):
                        word_end = token_groups[group_idx + 1][0][1]
                    else:
                        word_end = min(duration_sec, min(chunk_end_sec, word_start + 0.35))
                    if word_end <= word_start:
                        word_end = min(duration_sec, word_start + 0.05)
                    chunk_words.append({
                        "word": word_text,
                        "start": round(word_start, 2),
                        "end": round(word_end, 2),
                        "probability": 0.95,
                    })
            elif c_text:
                raw_words = c_text.split()
                step = max(0.05, (chunk_end_sec - chunk_start_sec) / max(1, len(raw_words)))
                for i, w in enumerate(raw_words):
                    w_start = chunk_start_sec + (i * step)
                    w_end = min(duration_sec, chunk_start_sec + ((i + 1) * step))
                    chunk_words.append({
                        "word": w,
                        "start": round(w_start, 2),
                        "end": round(w_end, 2),
                        "probability": 0.95,
                    })

            if chunk_words:
                all_words.extend(chunk_words)
                current_words = []
                for word in chunk_words:
                    gap = (word["start"] - current_words[-1]["end"]) if current_words else 0.0
                    current_words.append(word)
                    sentence_end = word["word"].rstrip().endswith((".", "?", "!"))
                    too_many = len(current_words) >= 12
                    long_gap = gap >= 1.0 and len(current_words) > 1
                    if sentence_end or too_many or long_gap:
                        seg_data = {
                            "start": round(current_words[0]["start"], 2),
                            "end": round(min(duration_sec, max(current_words[-1]["end"], current_words[0]["start"] + 0.05)), 2),
                            "text": " ".join(w["word"] for w in current_words),
                            "words": current_words,
                        }
                        all_segments.append(seg_data)
                        _emit("streaming_segment", segment=seg_data)
                        current_words = []
                if current_words:
                    seg_data = {
                        "start": round(current_words[0]["start"], 2),
                        "end": round(min(duration_sec, max(current_words[-1]["end"], current_words[0]["start"] + 0.05)), 2),
                        "text": " ".join(w["word"] for w in current_words),
                        "words": current_words,
                    }
                    all_segments.append(seg_data)
                    _emit("streaming_segment", segment=seg_data)

        text = " ".join(text_parts).strip() or "(silence)"

        if not all_segments:
            words_raw = text.split()
            step = duration_sec / max(1, len(words_raw)) if words_raw else 1.0
            words = [{"word": w, "start": round(i * step, 2), "end": round(min(duration_sec, (i + 1) * step), 2), "probability": 0.95}
                     for i, w in enumerate(words_raw)]
            if words:
                for off in range(0, len(words), 12):
                    group = words[off:off + 12]
                    seg_data = {
                        "start": group[0]["start"],
                        "end": group[-1]["end"],
                        "text": " ".join(w["word"] for w in group),
                        "words": group,
                    }
                    all_segments.append(seg_data)
                    _emit("streaming_segment", segment=seg_data)
            else:
                seg_data = {
                    "start": 0.0,
                    "end": round(duration_sec, 2),
                    "text": "(silence)",
                    "words": [],
                }
                all_segments.append(seg_data)
                _emit("streaming_segment", segment=seg_data)

        _emit("progress", percent=100, message=f"{model_name} transcription complete.")
        _emit("finished", result={"text": text, "segments": all_segments, "language": model_lang})
        return 0
    except Exception as exc:
        _emit("error", message=f"{model_name} error: {type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")
        return 5
    finally:
        try:
            if temp_dir is not None:
                temp_dir.cleanup()
        except Exception:
            pass


def probe_audio_language(audio_file, sample_duration=30.0, preferred_model=None):
    """Run a fast language detection probe using faster-whisper's mel feature extractor.

    Samples 30 seconds of audio starting 10 seconds into the file (when possible)
    to avoid intro music, jingles, or initial silence that cause false language tags.
    """
    temp_probe_file = None
    target_file = str(audio_file)
    try:
        _patch_av_open()
        from faster_whisper import WhisperModel
        download_root = os.environ.get("PRS_MODELS_DIR") or None
        probe_model = None
        candidates = ["tiny"]
        if preferred_model and str(preferred_model).strip() and not str(preferred_model).endswith("-onnx"):
            candidates.append(str(preferred_model).strip())

        for candidate in candidates:
            try:
                probe_model = WhisperModel(
                    candidate,
                    device="cpu",
                    compute_type="int8",
                    download_root=download_root,
                    local_files_only=True,
                )
                break
            except Exception:
                continue

        if probe_model is None:
            sys.stderr.write("[LANGUAGE PROBE] Notice: No local Whisper model available for offline language probing; skipping probe and defaulting to English.\n")
            sys.stderr.flush()
            return "en", 0.0

        if sample_duration and sample_duration > 0:
            try:
                ffmpeg_bin = None
                filename = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
                for candidate_path in [
                    Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "runtime" / "bin" / filename,
                    Path(sys.executable).resolve().parent / "runtime" / "bin" / filename,
                    Path(__file__).resolve().parent / "runtime" / "bin" / filename,
                ]:
                    if candidate_path.is_file():
                        ffmpeg_bin = str(candidate_path)
                        break
                if not ffmpeg_bin:
                    ffmpeg_bin = shutil.which("ffmpeg")

                if ffmpeg_bin:
                    # Skip initial 10s intro music/silence for files > 1MB; sample 30 seconds
                    file_size = os.path.getsize(str(audio_file)) if os.path.exists(str(audio_file)) else 0
                    start_offset = "10" if file_size > 1000000 else "0"

                    tf = tempfile.NamedTemporaryFile(suffix="_probe.wav", delete=False)
                    temp_probe_file = tf.name
                    tf.close()
                    cmd = [
                        ffmpeg_bin, "-y", "-v", "error",
                        "-ss", start_offset, "-i", str(audio_file),
                        "-t", str(float(sample_duration)),
                        "-vn", "-sn", "-dn",
                        "-ar", "16000", "-ac", "1",
                        temp_probe_file,
                    ]
                    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
                    if res.returncode == 0 and os.path.exists(temp_probe_file) and os.path.getsize(temp_probe_file) > 1000:
                        target_file = temp_probe_file
            except Exception:
                pass

        _, info = probe_model.transcribe(target_file, beam_size=1)
        lang = getattr(info, "language", "en") or "en"
        prob = getattr(info, "language_probability", 0.0) or 0.0

        # Check if English is close in probability
        all_probs = getattr(info, "all_language_probs", None) or []
        prob_dict = dict(all_probs) if all_probs else {}
        en_prob = prob_dict.get("en", 0.0)

        # If detected non-English but English probability is close or non-English is low-confidence, prefer English
        if lang != "en":
            if en_prob > 0.25 or prob < 0.65:
                sys.stderr.write(f"[LANGUAGE PROBE] Non-English detection ({lang}, {prob*100:.1f}%) overridden by English probability/threshold ({en_prob*100:.1f}% en)\n")
                sys.stderr.flush()
                return "en", en_prob

        sys.stderr.write(f"[LANGUAGE PROBE] Probed language: {lang} (probability: {prob*100:.1f}%)\n")
        sys.stderr.flush()
        return lang, prob
    except Exception as exc:
        sys.stderr.write(f"[LANGUAGE PROBE] Warning: Language probing failed ({type(exc).__name__}: {exc}), defaulting to English\n")
        sys.stderr.flush()
        return "en", 0.0
    finally:
        if temp_probe_file and os.path.exists(temp_probe_file):
            try:
                os.remove(temp_probe_file)
            except Exception:
                pass


def transcribe(audio_file, model_name, initial_prompt="", beam_size=5):
    """Transcribe media file using either Sherpa-ONNX or Faster-Whisper."""
    m_lower = str(model_name).lower()
    is_spanish_fastconformer = "fastconformer" in m_lower and ("es" in m_lower or "spanish" in m_lower or "es-onnx" in m_lower)
    is_multilingual_fastconformer = "multilingual" in m_lower or ("fastconformer" in m_lower and "multi" in m_lower)
    is_parakeet = "parakeet" in m_lower
    is_onnx = is_parakeet or is_spanish_fastconformer or is_multilingual_fastconformer or m_lower.endswith("-onnx")

    auto_fallback = os.environ.get("PRS_AUTO_LANGUAGE_FALLBACK", "1").strip().lower() != "0"
    need_spanish_prompt = False

    probed_lang, prob = None, 0.0
    if auto_fallback:
        _emit("progress", percent=2, message="Inspecting audio language compatibility...")
        probed_lang, prob = probe_audio_language(audio_file, preferred_model=model_name)

        if is_spanish_fastconformer:
            _emit("progress", percent=4, message=f"Detected {probed_lang.upper()} speech ({prob*100:.0f}% confidence). Using Spanish FastConformer ONNX...")
        elif is_multilingual_fastconformer:
            _emit("progress", percent=4, message=f"Detected {probed_lang.upper()} speech ({prob*100:.0f}% confidence). Using Multilingual FastConformer ONNX...")
        elif probed_lang and probed_lang.lower() == "es" and prob >= 0.60:
            if is_onnx_model_available("fastconformer-es-onnx"):
                _emit("progress", percent=4, message=f"Detected Spanish speech ({prob*100:.0f}% confidence). Switching to Spanish FastConformer ONNX...")
                model_name = "fastconformer-es-onnx"
                is_onnx = True
            elif is_onnx_model_available("fastconformer-multilingual-onnx"):
                _emit("progress", percent=4, message=f"Detected Spanish speech ({prob*100:.0f}% confidence). Switching to Multilingual FastConformer ONNX...")
                model_name = "fastconformer-multilingual-onnx"
                is_onnx = True
            else:
                if is_parakeet:
                    _emit("progress", percent=4, message=f"Detected Spanish speech ({prob*100:.0f}% confidence). English Parakeet TDT cannot transcribe Spanish; switching to Whisper Small...")
                    model_name = "small"
                    is_onnx = False
                    need_spanish_prompt = True
                else:
                    _emit("progress", percent=4, message=f"Detected Spanish speech ({prob*100:.0f}% confidence). Continuing with {model_name}...")
        elif probed_lang and probed_lang.lower() != "en" and prob >= 0.65:
            if is_parakeet:
                if is_onnx_model_available("fastconformer-multilingual-onnx"):
                    _emit("progress", percent=4, message=f"Detected non-English speech ({probed_lang.upper()}, {prob*100:.0f}% confidence). Switching to Multilingual FastConformer ONNX...")
                    model_name = "fastconformer-multilingual-onnx"
                    is_onnx = True
                else:
                    _emit("progress", percent=4, message=f"Detected non-English speech ({probed_lang.upper()}, {prob*100:.0f}% confidence). Automatically switching to Whisper Small...")
                    model_name = "small"
                    is_onnx = False
        elif is_parakeet and probed_lang and probed_lang.lower() != "en":
            _emit("progress", percent=4, message=f"Probed language {probed_lang.upper()} below confidence threshold ({prob*100:.0f}% < 65%); retaining default Parakeet ONNX model...")

    if is_onnx:
        if is_onnx_model_available(model_name):
            return transcribe_parakeet_onnx(audio_file, model_name=model_name, detected_lang=probed_lang, detected_confidence=prob, initial_prompt=initial_prompt, beam_size=beam_size)
        else:
            _emit("progress", percent=4, message=f"ONNX model '{model_name}' or sherpa-onnx runtime is unavailable. Falling back to Whisper Small...")
            model_name = "small"
            is_onnx = False

    _emit("progress", percent=5, message=f"Loading local Whisper {model_name} model...")
    try:
        _patch_av_open()
        from faster_whisper import WhisperModel
    except Exception as exc:
        _emit("error", message=f"Could not load faster-whisper locally: {type(exc).__name__}: {exc}")
        return 3

    try:
        threads = get_optimal_transcription_threads()
        download_root = os.environ.get("PRS_MODELS_DIR") or None

        resolved_model_name = model_name
        if model_name == "distil-medium.en":
            resolved_model_name = "Systran/faster-distil-whisper-medium.en"
        elif model_name == "distil-large-v3":
            resolved_model_name = "Systran/faster-distil-whisper-large-v3"
        elif model_name.startswith("distil-"):
            resolved_model_name = f"Systran/faster-{model_name}"

        model_to_load = resolved_model_name
        try:
            env_dir = os.environ.get("PRS_MODELS_DIR")
            env_path = Path(env_dir) if env_dir else None

            slugs = []
            if model_name == "distil-large-v3":
                slugs.extend([
                    "models--Systran--faster-distil-whisper-large-v3",
                    "models--Systran--faster-whisper-distil-large-v3",
                    "models--distil-large-v3",
                ])
            elif model_name in ("distil-medium.en", "distil-medium"):
                slugs.extend([
                    "models--Systran--faster-distil-whisper-medium.en",
                    "models--Systran--faster-whisper-distil-medium.en",
                    "models--distil-medium.en",
                ])
            elif model_name.startswith("distil-"):
                slugs.extend([
                    f"models--Systran--faster-{model_name}",
                    f"models--{model_name}",
                ])
            else:
                slugs.extend([
                    f"models--guillaumekcln--faster-whisper-{model_name}",
                    f"models--Systran--faster-whisper-{model_name}",
                    f"models--openai--whisper-{model_name}",
                    f"models--faster-whisper-{model_name}",
                    f"models--{model_name}",
                    f"models--{resolved_model_name.replace('/', '--')}",
                ])

            cache_roots = []
            if env_path:
                cache_roots.extend([env_path / "huggingface" / "hub", env_path / "hub", env_path])
            try:
                mdir = get_models_storage_dir_pure()
                cache_roots.extend([mdir / "huggingface" / "hub", mdir / "hub", mdir])
            except Exception:
                pass
            try:
                appd = get_app_data_dir_pure() / "models"
                cache_roots.extend([appd / "huggingface" / "hub", appd / "hub", appd])
            except Exception:
                pass
            cache_roots.extend([
                Path.home() / ".cache" / "huggingface" / "hub",
                Path(__file__).resolve().parent / "models",
            ])

            for cr in cache_roots:
                for slug in slugs:
                    cd = cr / slug
                    if cd.exists():
                        bin_files = list(cd.rglob("model.bin")) or list(cd.rglob("*.bin")) or list(cd.rglob("*.safetensors"))
                        if bin_files:
                            snap_dir = bin_files[0].parent
                            model_to_load = str(snap_dir)
                            break
                if model_to_load != resolved_model_name:
                    break
        except Exception:
            pass

        preferred_device = os.environ.get("PRS_WHISPER_DEVICE", "cpu").strip().lower() or "cpu"
        preferred_compute = os.environ.get("PRS_WHISPER_COMPUTE_TYPE", "int8").strip() or "int8"
        if model_to_load == resolved_model_name:
            _emit("progress", percent=6, message=f"Downloading/loading Whisper {model_name} model from Hugging Face...")
        try:
            model = WhisperModel(
                model_to_load,
                device=preferred_device,
                compute_type=preferred_compute,
                cpu_threads=threads,
                download_root=download_root,
            )
            backend = f"{preferred_device}/{preferred_compute} ({threads} threads)"
        except Exception as accel_exc:
            if preferred_device != "cpu" or preferred_compute != "int8":
                _emit("progress", percent=8, message="Accelerated Whisper initialization failed; falling back to CPU INT8...")
            try:
                model = WhisperModel(
                    model_to_load,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=threads,
                    download_root=download_root,
                )
                backend = f"cpu/int8 ({threads} threads)"
            except Exception:
                raise accel_exc
        _emit("progress", percent=15, message=f"Whisper {model_name} model loaded ({backend}, beam={beam_size}). Transcribing...")

        clean_prompt = initial_prompt.strip() if initial_prompt and initial_prompt.strip() else None

        segments, info = model.transcribe(
            str(audio_file),
            beam_size=int(beam_size),
            word_timestamps=True,
            vad_filter=True,
            initial_prompt=clean_prompt,
        )

        formatted_segments = []
        total_duration = max(0.1, float(info.duration)) if hasattr(info, "duration") and info.duration else 1.0

        for seg in segments:
            pct = min(95, int(15 + (seg.end / total_duration) * 80))
            _emit("progress", percent=pct, message=f"Transcribing ({seg.end:.1f}s / {total_duration:.1f}s)...")

            words = []
            if getattr(seg, "words", None):
                for w in seg.words:
                    words.append({
                        "word": w.word,
                        "start": float(w.start),
                        "end": float(w.end),
                        "probability": float(w.probability),
                    })

            seg_data = {
                "start": float(seg.start),
                "end": float(seg.end),
                "text": seg.text.strip(),
                "words": words,
            }
            formatted_segments.append(seg_data)
            _emit("streaming_segment", segment=seg_data)

        try:
            from transcript_cleaner import scrub_transcript_segments
            formatted_segments = scrub_transcript_segments(formatted_segments)
        except Exception:
            pass

        output = {
            "text": " ".join([s["text"] for s in formatted_segments if s.get("text", "").strip()]),
            "segments": formatted_segments,
            "language": getattr(info, "language", "en"),
            "need_spanish_model_prompt": need_spanish_prompt,
        }

        _emit("progress", percent=100, message="Transcription complete.")
        _emit("finished", result=output)
        return 0

    except Exception as exc:
        _emit("error", message=f"{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}")
        return 4
