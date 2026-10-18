# Validation · v1.0.0

2026-10-18：Windows / Python 3.12，NumPy、SciPy、SoundFile。

- Codex skill frontmatter/name/scaffold validator: pass.
- `python scripts/test_tools.py`: 7 behavioral tests pass.
- Cue rounding uses original music absolute time with a nonzero input offset and rational frame rate; long event sequences do not accumulate rounded beat intervals.
- Continuous source times are monotone; contact and multi-frame protection anchors are exact; reverse/conflicting/out-of-range plans are rejected.
- Dry contact samples are retained exactly in the float processing pipeline; derived layers begin at the reported onset. Dry/body/sub plus master difference reconstruct the mix.
- Silent input remains silent, different source contacts produce different derived waveforms, antiphase stereo input has a usable mono derivation, hot input remains under the configured 4x estimated peak ceiling.
- Both CLIs are copied to and executed from a new temporary directory using only an anonymous example and temporary synthetic test WAV. No production media used.

The example timing values are invented. This release contains no rendered reference artwork or licensed anime sound. Tests do not demonstrate aesthetic quality, reliable automatic beat detection, denoising, a certified true-peak meter, or subjective listening approval. Final media still requires the visual/audio checks described in the skill.
