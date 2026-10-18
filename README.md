# 黑闪冲击帧 · black-flash-impact

Standalone Codex skill for anime-style impact frames in live-action footage: source-derived contact sound, music sync, continuous retiming, morphing lightning, occluded particles, environment response, and portable delivery.

将响指、拳脚或物体接触制作成有蓄力、断然释放和环境后果的黑闪。独立技能，不依赖其他个人技能；不绑定某部动画、某首歌、固定四次动作或特定颜色。

## 安装

将仓库克隆到 Codex skills 目录，已有同名目录先检查本地修改。PowerShell：

```powershell
$impactSkillPath = Join-Path $env:USERPROFILE '.codex/skills/black-flash-impact'
git clone https://github.com/81823650800wzy-sketch/black-flash-impact-skill.git $impactSkillPath
```

也可从 Releases 下载 `black-flash-impact-v1.0.0.zip`，解压后把其中 `black-flash-impact` 文件夹放入 skills 目录。新会话刷新技能列表。技能指令本身不要求特定剪辑软件；FFmpeg/FFprobe 用于媒体处理，有厚度碎片和真实空间需求时再使用 Blender。

## 使用

> 使用 `$black-flash-impact`，把我的实拍接触动作制作成黑闪。按我提供的配乐定位主爆点，保留每个原动作声音的辨识，补强低频和攻击；连续动作采用变速卡点，电弧和粒子要有遮挡与环境反馈。输出完整预览和可编辑工程。

输入可以是一个动作，也可以是多段素材和音乐。说明要保留的配音/字幕、期望时长与循环方式；已在对话中确定的选择不必重填。未提供音乐不强制配乐。没有可用素材或授权音源时，先索取必要输入，不用示意动画冒充实拍成片。

## 内容

- [SKILL.md](SKILL.md)：技能入口与完整执行顺序。
- [节奏](references/timing.md)：原曲绝对时间、静音前导、层级节奏、动作接触卡点、连续变速和曝光保护。
- [声音](references/audio.md)：保留原接触，主体/sub/攻击/尾部分层，配乐让位、相位、峰值、分轨与听审边界。
- [视觉](references/visuals.md)：换形缠绕闪电、快速曝光、追踪粒子、动态遮挡、源像素波动与原片清晰度。
- [交付](references/delivery.md)：编码后检查、收尾、完整工程和实际迁移重建。

## 两个确定性助手

Python 3.10+；安装 `python -m pip install -r requirements.txt`。

```shell
python scripts/plan_timing.py examples/timing.json --out timing-result.json
python scripts/enhance_contact.py contact.wav --onset 0.10 --out enhanced
python scripts/test_tools.py
```

时间助手从明确的音乐事件生成 cue 和连续源时间曲线，不自动识别节拍或动作。声音助手用当前动作录音生成主体与低频分轨，不是降噪器、自动音效替换或完整母带器；测试信号不是效果示范。两个助手都不会自动渲染整片；实际合成由使用技能的 agent 按素材选择工具完成。

输入格式见示例和对应参考。私有素材路径不在示例中。输出 `report.json` 保留起音样本位置，混音时需扣除预卷，不能把整个裁切窗口开头当接触时刻。

## 验证与范围

见 [VALIDATION.md](VALIDATION.md)。自动测试覆盖绝对卡点、无漂移映射、保护曝光、错误拒绝、干声保留、静音防放大、不同原声输出、反相输入、峰值和新目录运行；技术通过不表示已经听审或被用户认可。

技能与代码 MIT 许可。仓库不含用户视频、曲目、原作动画音效、截图、生产工程、字体或模型权重；它们的许可不由本仓库授予。要分发成片，使用者自行保留所用媒体的权利与来源记录。
