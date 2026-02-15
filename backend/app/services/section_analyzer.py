from __future__ import annotations


def detect_sections(audio_path: str) -> list[dict]:
    """Detect song sections using All-In-One analyzer.

    Returns list of {"start": float, "end": float, "label": str}.
    Falls back to simple energy-based segmentation if allin1 is not available.
    """
    try:
        return _detect_with_allinone(audio_path)
    except ImportError:
        return _detect_fallback(audio_path)


def _detect_with_allinone(audio_path: str) -> list[dict]:
    import allin1

    result = allin1.analyze(audio_path)
    sections = []
    for seg in result.segments:
        sections.append({
            "start": float(seg.start),
            "end": float(seg.end),
            "label": seg.label.lower(),
        })
    return sections


def _detect_fallback(audio_path: str) -> list[dict]:
    """Section detection using self-similarity novelty with checkerboard kernel."""
    import librosa
    import numpy as np
    from scipy.ndimage import median_filter

    y, sr = librosa.load(audio_path, sr=22050, mono=True)
    duration = float(len(y) / sr)

    hop_length = 512
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, hop_length=hop_length, n_mfcc=13)

    # Build self-similarity via recurrence matrix
    features = np.vstack([chroma, mfcc])
    rec = librosa.segment.recurrence_matrix(features, mode="affinity", sym=True)

    # Compute novelty using checkerboard kernel convolution
    novelty = _checkerboard_novelty(rec, kernel_size=64)
    novelty = median_filter(novelty, size=9)
    # Normalize
    if novelty.max() > 0:
        novelty = novelty / novelty.max()

    peaks = librosa.util.peak_pick(
        novelty, pre_max=7, post_max=7, pre_avg=7, post_avg=7, delta=0.05, wait=30
    )

    boundary_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
    boundary_times = [0.0] + list(boundary_times) + [duration]

    label_cycle = ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"]
    sections = []
    for i in range(len(boundary_times) - 1):
        label = label_cycle[i] if i < len(label_cycle) else "verse"
        sections.append({
            "start": float(boundary_times[i]),
            "end": float(boundary_times[i + 1]),
            "label": label,
        })

    return sections


def _checkerboard_novelty(rec: "np.ndarray", kernel_size: int = 64) -> "np.ndarray":
    """Compute novelty curve from a recurrence matrix using a checkerboard kernel."""
    import numpy as np

    n = rec.shape[0]
    half = kernel_size // 2
    novelty = np.zeros(n)

    # Build checkerboard kernel
    kern = np.ones((kernel_size, kernel_size))
    kern[:half, :half] = -1
    kern[half:, half:] = -1

    for i in range(half, n - half):
        patch = rec[i - half : i + half, i - half : i + half]
        novelty[i] = np.sum(patch * kern)

    # Rectify (only positive = boundary)
    novelty = np.maximum(novelty, 0)
    return novelty
