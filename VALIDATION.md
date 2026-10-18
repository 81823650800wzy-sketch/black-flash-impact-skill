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

## v1.0.1 · 首页与展示资源

2026-10-18：加入四张经明确授权用于首页展示的实际成片截图，裁切与压缩后移除 EXIF；展示图单独许可，完整媒体不分发。重排首页，补充工具职责、必需/可选依赖、安装验证命令与官方入口；按当前官方说明修正个人技能安装目录。Python 助手无行为变更。
