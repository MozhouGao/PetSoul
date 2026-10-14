"""
Pet sound bank. Real recordings are split on energy, peak-normalized, and labeled
by a person. Labels are bark, whine, pant, and other. Nothing here synthesizes audio.
"""

from __future__ import annotations

import io
import shutil
import subprocess
import wave
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

LABELS = ("bark", "whine", "pant", "other")
MIN_SECONDS = 0.3
MAX_SECONDS = 3.0


def normalize_peak(samples: np.ndarray, peak: float = 0.9) -> np.ndarray:
    samples = np.asarray(samples, dtype=np.float32)
    loudest = float(np.max(np.abs(samples))) if samples.size else 0.0
    if loudest < 1e-8:
        return samples
    return samples * (peak / loudest)


def split_on_energy(samples: np.ndarray, sample_rate: int) -> List[np.ndarray]:
    """Cut silence, keep takes between 0.3 s and 3 s."""
    samples = np.asarray(samples, dtype=np.float32).reshape(-1)
    if samples.size == 0 or sample_rate <= 0:
        return []
    frame = max(int(sample_rate * 0.02), 1)
    usable = samples[: len(samples) - (len(samples) % frame)]
    if usable.size < frame:
        return []
    frames = usable.reshape(-1, frame)
    rms = np.sqrt(np.mean(frames * frames, axis=1))
    thresh = max(float(np.percentile(rms, 55)), 1e-4)
    active = rms >= thresh
    gap_frames = max(int(0.1 * sample_rate / frame), 1)
    regions: List[Tuple[int, int]] = []
    start = None
    silent = 0
    for i, on in enumerate(active):
        if on:
            if start is None:
                start = i
            silent = 0
        elif start is not None:
            silent += 1
            if silent >= gap_frames:
                regions.append((start, i - silent + 1))
                start = None
                silent = 0
    if start is not None:
        regions.append((start, len(active)))

    takes = []
    for a, b in regions:
        clip = usable[a * frame:b * frame]
        duration = len(clip) / sample_rate
        if duration < MIN_SECONDS:
            continue
        if duration > MAX_SECONDS:
            window = int(MAX_SECONDS * sample_rate)
            for offset in range(0, len(clip) - int(MIN_SECONDS * sample_rate), window):
                piece = clip[offset:offset + window]
                if len(piece) >= int(MIN_SECONDS * sample_rate):
                    takes.append(normalize_peak(piece))
        else:
            takes.append(normalize_peak(clip))
    return takes


def write_wav(path: Path, samples: np.ndarray, sample_rate: int) -> None:
    pcm = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    ints = (pcm * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(ints.tobytes())


def read_wav(path: Path) -> Tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as handle:
        rate = handle.getframerate()
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        frames = handle.readframes(handle.getnframes())
    if width == 2:
        data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32767.0
    elif width == 4:
        data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483647.0
    else:
        raise ValueError("only 16-bit and 32-bit PCM wav files are supported")
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    return data, rate


def extract_wav_from_video(video_path: Path, dest: Path) -> None:
    """Pull the audio track off a video into a mono wav. Motion still succeeds if this cannot."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        cmd = [ffmpeg, "-y", "-i", str(video_path), "-vn", "-ac", "1", "-ar", "16000", str(dest)]
    else:
        afconvert = shutil.which("afconvert")
        if afconvert is None:
            raise ValueError("ffmpeg is required to read sound from the video")
        cmd = [afconvert, str(video_path), str(dest), "-f", "WAVE", "-d", "LEI16@16000"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not dest.exists():
        raise ValueError("could not read sound from that video")


def decode_upload(raw: bytes, suffix: str, work_dir: Path) -> Tuple[np.ndarray, int]:
    """Decode wav bytes, or m4a/mp3/caf via afconvert or ffmpeg when present."""
    suffix = suffix.lower()
    work_dir.mkdir(parents=True, exist_ok=True)
    if suffix in (".wav", ".wave"):
        src = work_dir / "upload.wav"
        src.write_bytes(raw)
        return read_wav(src)
    converter = shutil.which("afconvert") or shutil.which("ffmpeg")
    if converter is None:
        raise ValueError("upload a wav file, or install ffmpeg so m4a can be converted")
    src = work_dir / f"upload{suffix}"
    dst = work_dir / "upload.wav"
    src.write_bytes(raw)
    if Path(converter).name == "afconvert":
        cmd = [converter, str(src), str(dst), "-f", "WAVE", "-d", "LEI16"]
    else:
        cmd = [converter, "-y", "-i", str(src), "-ac", "1", str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not dst.exists():
        raise ValueError("could not convert that recording to wav")
    return read_wav(dst)


def validate_label(label: str) -> str:
    cleaned = (label or "").strip().lower()
    if cleaned not in LABELS:
        raise ValueError(f"label must be one of: {', '.join(LABELS)}")
    return cleaned


def wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
    buf = io.BytesIO()
    pcm = np.clip(samples, -1.0, 1.0)
    ints = (pcm * 32767.0).astype(np.int16)
    with wave.open(buf, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(ints.tobytes())
    return buf.getvalue()
