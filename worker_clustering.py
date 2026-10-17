"""worker_clustering.py - Acoustic clustering, VAD pause bridging, and centroid assignments.

Provides:
- normalize_audio_for_diarization: FFmpeg 16kHz mono normalization
- configure_optimal_pytorch_threads: PyTorch CPU thread configuration
- _normalize_expected_speakers: Map speaker hints
- _normalize_speaker_labels: Renumber speaker ids in playback order
- _sensitivity_distance_threshold: Cosine distance threshold lookup
- fast_cluster_ahc: Fast O(N^2) Agglomerative Hierarchical Clustering
- apply_clustering_patches: Globally patch SpectralClustering to AHC
- run_vad_two_pass: Silero VAD with pause bridging (< 100ms)
- assign_short_segments_to_centroids: Acoustic assignment of short turns (< 0.8s)
- _calculate_embedding_for_interval: Interval embedding calculation
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from worker_ipc import emit, _safe_tensor_from_numpy

SHORT_FRAGMENT_MERGE_THRESHOLD = 0.7


def normalize_audio_for_diarization(source_path):
    """Extract a normalized 16 kHz mono WAV using the local FFmpeg binary."""
    ffmpeg = None
    filename = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    candidates = [
        Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "runtime" / "bin" / filename,
        Path(sys.executable).resolve().parent / "runtime" / "bin" / filename,
        Path(__file__).resolve().parent / "runtime" / "bin" / filename,
    ]
    for candidate in candidates:
        if candidate.is_file():
            ffmpeg = str(candidate)
            break
    if ffmpeg is None:
        ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg could not be found on PATH. Speaker Detection requires the "
            "local FFmpeg installation to decode this media file."
        )

    source = Path(source_path).resolve()
    temp_dir = tempfile.TemporaryDirectory(prefix="prs_diarization_")
    wav_path = Path(temp_dir.name) / "audio_16khz_mono.wav"

    emit("progress", percent=18, message="Extracting and normalizing audio with local FFmpeg...")
    command = [
        ffmpeg,
        "-y",
        "-v", "error",
        "-i", str(source),
        "-vn", "-sn", "-dn",
        "-map", "0:a:0?",
        "-af", "highpass=f=85,lowpass=f=7500",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(wav_path),
    ]
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired as exc:
        temp_dir.cleanup()
        raise RuntimeError("FFmpeg audio normalization timed out after 15 minutes.") from exc
    if result.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size == 0:
        detail = result.stderr.strip() or "FFmpeg did not produce an audio file."
        temp_dir.cleanup()
        raise RuntimeError(f"FFmpeg could not extract an audio stream: {detail}")

    emit("progress", percent=32, message="Audio extracted and normalized to 16 kHz mono WAV.")
    return temp_dir, wav_path


def configure_optimal_pytorch_threads():
    """Clamp torch's intra-op/inter-op thread pools to match the
    OMP/ORT clamp set at module import time, for the torch-based Silero VAD
    step.
    """
    try:
        import torch
        threads = max(1, min(int(os.environ.get("OMP_NUM_THREADS", "4")), 8))
        torch.set_num_threads(threads)
        try:
            torch.set_num_interop_threads(threads)
        except RuntimeError:
            pass
    except Exception:
        pass


def _normalize_expected_speakers(value):
    """Map a CLI/UI expected-speakers hint to one of 'auto', '1', '2', '3+'."""
    text = str(value).strip().lower()
    if text in ("1", "solo"):
        return "1"
    if text == "2":
        return "2"
    if text in ("3+", "3", "panel", "group"):
        return "3+"
    return "auto"


def _normalize_speaker_labels(segments):
    """Relabel raw diarize-package speaker ids to 'Speaker 1', 'Speaker 2',
    etc, in order of first appearance so the numbering matches playback
    order rather than the library's internal (often alphabetical) ids.
    """
    order = []
    for seg in segments:
        raw = seg.get("speaker")
        if raw not in order:
            order.append(raw)
    label_map = {raw: f"Speaker {i + 1}" for i, raw in enumerate(order)}
    for seg in segments:
        seg["speaker"] = label_map.get(seg["speaker"], seg["speaker"])
    return segments


def _sensitivity_distance_threshold():
    """Cosine-distance clustering threshold derived from PRS_DIARIZATION_SENSITIVITY.
    Shared by fast_cluster_ahc() and diarize().
    """
    sens_env = os.environ.get("PRS_DIARIZATION_SENSITIVITY", "normal").strip().lower()
    sens_map = {"low": 0.78, "normal": 0.68, "high": 0.58, "very_high": 0.48, "ultra": 0.38}
    return sens_map.get(sens_env, 0.68)


def fast_cluster_ahc(embeddings, k=None, distance_threshold=None):
    """Agglomerative Hierarchical Clustering with cosine metric and average linkage (O(N^2)).
    Supports distance threshold sensitivity control for AHC on unit hypersphere.
    """
    import numpy as np
    n = len(embeddings)
    if n == 0:
        return np.array([], dtype=int)

    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    norm_emb = embeddings / norms

    from sklearn.cluster import AgglomerativeClustering

    if distance_threshold is None:
        distance_threshold = _sensitivity_distance_threshold()

    use_fixed_k = False
    if k is not None and not isinstance(k, str) and int(k) >= 1:
        use_fixed_k = True
        k_val = max(1, min(int(k), n))
    elif isinstance(k, str) and k.isdigit() and int(k) >= 1:
        use_fixed_k = True
        k_val = max(1, min(int(k), n))

    if use_fixed_k:
        if k_val == 1:
            return np.zeros(n, dtype=int)
        try:
            clusterer = AgglomerativeClustering(n_clusters=k_val, metric="cosine", linkage="average")
        except TypeError:
            clusterer = AgglomerativeClustering(n_clusters=k_val, affinity="cosine", linkage="average")
    else:
        try:
            clusterer = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=float(distance_threshold),
                metric="cosine",
                linkage="average",
            )
        except TypeError:
            clusterer = AgglomerativeClustering(
                n_clusters=None,
                distance_threshold=float(distance_threshold),
                affinity="cosine",
                linkage="average",
            )

    labels = clusterer.fit_predict(norm_emb)

    try:
        from diarize.clustering import _refine_labels_spherical
        labels = _refine_labels_spherical(embeddings, labels)
    except Exception:
        pass
    return labels


def apply_clustering_patches():
    """Globally monkey-patch SpectralClustering and diarize.clustering to use O(N^2) AHC."""
    try:
        import sklearn.cluster

        class PatchedSpectralClustering:
            def __init__(self, n_clusters=2, *args, **kwargs):
                self.n_clusters = n_clusters
                self.labels_ = None
                self.affinity = kwargs.get("affinity", "cosine")

            def fit(self, X, y=None):
                self.labels_ = fast_cluster_ahc(X, self.n_clusters)
                return self

            def fit_predict(self, X, y=None):
                self.fit(X, y)
                return self.labels_

        sklearn.cluster.SpectralClustering = PatchedSpectralClustering
    except Exception:
        pass

    try:
        import diarize.clustering
        diarize.clustering.cluster_spectral = fast_cluster_ahc
    except Exception:
        pass

    try:
        import diarize
        diarize.cluster_spectral = fast_cluster_ahc
    except Exception:
        pass


def run_vad_two_pass(
    audio_path,
    threshold=0.60,
    min_speech_duration_ms=250,
    min_silence_duration_ms=300,
    speech_pad_ms=10,
    bridge_pause_threshold_sec=0.10,
):
    """Silero VAD with Pass 1 Pause Bridging (< 100ms).
    Merges adjacent VAD speech intervals separated by pauses under 100ms,
    eliminating micro-slicing while preserving natural phrase boundaries.
    """
    import soundfile as sf
    import torch
    from silero_vad import get_speech_timestamps, load_silero_vad
    from diarize.utils import SpeechSegment

    data, sample_rate = sf.read(str(audio_path), dtype="float32")
    if data.ndim > 1:
        data = data.mean(axis=-1)

    if sample_rate != 16000:
        try:
            from scipy.signal import resample_poly
            from math import gcd
            g = gcd(sample_rate, 16000)
            data = resample_poly(data, 16000 // g, sample_rate // g).astype("float32")
            sample_rate = 16000
        except Exception:
            try:
                import torchaudio
                t_wav = _safe_tensor_from_numpy(data)
                resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                data = resampler(t_wav).detach().cpu().numpy()
                sample_rate = 16000
            except Exception:
                pass

    wav = _safe_tensor_from_numpy(data)

    try:
        vad_model = load_silero_vad(onnx=True)
    except Exception:
        vad_model = load_silero_vad()
    speech_timestamps = get_speech_timestamps(
        wav,
        vad_model,
        sampling_rate=16000,
        threshold=threshold,
        min_speech_duration_ms=min_speech_duration_ms,
        min_silence_duration_ms=min_silence_duration_ms,
        speech_pad_ms=speech_pad_ms,
        return_seconds=True,
    )

    if not speech_timestamps:
        return []

    speech_timestamps.sort(key=lambda ts: float(ts["start"]))

    merged_timestamps = [
        {"start": float(speech_timestamps[0]["start"]), "end": float(speech_timestamps[0]["end"])}
    ]
    for ts in speech_timestamps[1:]:
        curr_start = float(ts["start"])
        curr_end = float(ts["end"])
        prev = merged_timestamps[-1]
        gap = curr_start - prev["end"]
        if gap < bridge_pause_threshold_sec:
            prev["end"] = max(prev["end"], curr_end)
        else:
            merged_timestamps.append({"start": curr_start, "end": curr_end})

    return [SpeechSegment(start=ts["start"], end=ts["end"]) for ts in merged_timestamps]


def assign_short_segments_to_centroids(
    short_segments,
    audio_path,
    centroids,
    label_values,
    raw_segments=None,
    min_confidence=0.45,
    model=None,
):
    """Extract acoustic embeddings for short segments (< 0.8s) with symmetric audio context padding,
    and assign them to the nearest speaker centroid via cosine similarity.
    """
    import numpy as np
    import soundfile as sf
    import torch
    import torchaudio.compliance.kaldi as kaldi

    if len(centroids) == 0:
        return []

    if model is None:
        import wespeakerruntime as wespeaker_rt
        model = wespeaker_rt.Speaker(lang="en")
    session = model.session

    audio_data, sr = sf.read(str(audio_path), dtype="float32")
    if audio_data.ndim > 1:
        audio_data = audio_data.mean(axis=1)

    if sr != 16000:
        import torchaudio
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=16000)
        base_tensor = _safe_tensor_from_numpy(audio_data).unsqueeze(0)
        audio_tensor = resampler(base_tensor).squeeze(0)
        sr = 16000
    else:
        audio_tensor = _safe_tensor_from_numpy(audio_data)

    total_samples = len(audio_tensor)
    assigned = []

    for seg in short_segments:
        start_sec = float(seg.start if hasattr(seg, "start") else seg["start"])
        end_sec = float(seg.end if hasattr(seg, "end") else seg["end"])
        duration = end_sec - start_sec

        target_dur = max(0.4, duration)
        pad_needed = min(0.05, max(0.0, target_dur - duration) / 2.0)
        pad_start = max(0.0, start_sec - pad_needed)
        pad_end = min(float(total_samples) / float(sr), end_sec + pad_needed)

        start_samp = int(pad_start * sr)
        end_samp = int(pad_end * sr)
        chunk = audio_tensor[start_samp:end_samp]

        emb = None
        if len(chunk) >= int(0.15 * sr):
            try:
                chunk_wave = chunk.unsqueeze(0) * (1 << 15)
                mat = kaldi.fbank(
                    chunk_wave,
                    num_mel_bins=80,
                    frame_length=25,
                    frame_shift=10,
                    dither=0.0,
                    sample_frequency=sr,
                    window_type="hamming",
                    use_energy=False,
                )
                mat = mat.numpy()
                mat = mat - np.mean(mat, axis=0)
                single_in = np.expand_dims(mat, 0).astype(np.float32)
                emb = session.run(output_names=["embs"], input_feed={"feats": single_in})[0][0]
            except Exception:
                emb = None

        chosen_speaker = None
        if emb is not None:
            norm = np.linalg.norm(emb)
            if norm > 0:
                norm_emb = emb / norm
                sims = norm_emb @ centroids.T
                best_idx = int(np.argmax(sims))
                if sims[best_idx] >= min_confidence or len(label_values) == 1:
                    chosen_speaker = f"SPEAKER_{label_values[best_idx]:02d}"

        if not chosen_speaker and raw_segments:
            seg_mid = (start_sec + end_sec) / 2.0
            best_dist = float("inf")
            for raw in raw_segments:
                raw_mid = (raw.start + raw.end) / 2.0
                dist = abs(seg_mid - raw_mid)
                if dist < best_dist:
                    best_dist = dist
                    chosen_speaker = raw.speaker

        if not chosen_speaker:
            chosen_speaker = f"SPEAKER_{label_values[0]:02d}" if len(label_values) > 0 else "SPEAKER_00"

        from diarize import _RawSegment
        seg_obj = _RawSegment(start=start_sec, end=end_sec, speaker=chosen_speaker)
        assigned.append(seg_obj)

    return assigned


def _calculate_embedding_for_interval(start, end, subsegments, embeddings):
    """Compute unit-normalized 256-dimensional embedding vector for an interval [start, end]."""
    if embeddings is None or len(embeddings) == 0 or not subsegments:
        return None
    try:
        import numpy as np
        sub_starts = np.array([float(s.start) for s in subsegments])
        sub_ends = np.array([float(s.end) for s in subsegments])
        s_st = float(start)
        s_en = float(end)
        overlap_mask = (sub_ends >= s_st - 0.05) & (sub_starts <= s_en + 0.05)
        if np.any(overlap_mask):
            matched = embeddings[overlap_mask]
            mean_emb = np.mean(matched, axis=0)
        else:
            sub_mids = (sub_starts + sub_ends) / 2.0
            seg_mid = (s_st + s_en) / 2.0
            closest_idx = int(np.argmin(np.abs(sub_mids - seg_mid)))
            mean_emb = embeddings[closest_idx]

        norm = np.linalg.norm(mean_emb)
        if norm > 0:
            mean_emb = mean_emb / norm
        return [round(float(x), 6) for x in mean_emb.tolist()]
    except Exception:
        return None
