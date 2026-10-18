"""Absolute music cues and monotone source-time maps; not a beat detector."""
from pathlib import Path
from fractions import Fraction
import argparse
import json
import math
import numpy as np
from scipy.interpolate import PchipInterpolator


def positive(value, label):
    x = float(Fraction(str(value)))
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f'{label} must be finite and positive')
    return x


def seconds(value, label):
    x = float(value)
    if not math.isfinite(x) or x < 0:
        raise ValueError(f'{label} must be finite and nonnegative')
    return x


def build(plan):
    fps = positive(plan['fps'], 'fps')
    duration = positive(plan['duration'], 'duration')
    total = round(duration * fps)
    if total < 1:
        raise ValueError('duration must include at least one output frame')
    music = plan['music']
    music_in = seconds(music['in'], 'music.in')
    speed = positive(music.get('speed', 1), 'music.speed')
    events = {}
    for e in plan['events']:
        name = e['id']
        if not isinstance(name, str) or not name or name in events:
            raise ValueError('event IDs must be unique nonempty strings')
        source = seconds(e['source_time'], f'{name}.source_time')
        mt = seconds(e['music_time'], f'{name}.music_time')
        t = (mt - music_in) / speed
        frame = round(t * fps)
        if t < 0 or t >= duration or not 0 <= frame < total:
            raise ValueError(f'{name}: music event outside output')
        events[name] = dict(id=name, music_time=mt, requested_output_time=t,
                            frame=frame, output_time=frame/fps,
                            quantisation_ms=(frame/fps-t)*1000, source_time=source)
    takes = []
    ids = set()
    for take in plan.get('continuous_takes', []):
        name = take['id']
        if name in ids:
            raise ValueError('take IDs must be unique')
        ids.add(name)
        sfps = positive(take['source_fps'], 'source_fps')
        start = round(seconds(take['output_start'], 'output_start') * fps)
        end = round(seconds(take['output_end'], 'output_end') * fps)
        if not 0 <= start < end <= total:
            raise ValueError(f'{name}: invalid output range')
        controls = {}

        def anchor(frame, source):
            if not start <= frame <= end or not math.isfinite(source) or source < 0:
                raise ValueError(f'{name}: invalid anchor {frame}, {source}')
            if frame in controls and abs(controls[frame]-source) > 1e-8:
                raise ValueError(f'{name}: conflicting anchors at output frame {frame}')
            controls[frame] = source

        for t, s in take['controls']:
            anchor(round(seconds(t, 'control output')*fps), seconds(s, 'control source'))
        protected = []
        seen = set()
        for window in take.get('protect', []):
            event = events[window['event']]
            if event['id'] in seen:
                raise ValueError(f'{name}: duplicate protected event')
            seen.add(event['id'])
            before, after = window['before_frames'], window['after_frames']
            if any(type(x) is not int or x < 0 for x in [before, after]):
                raise ValueError('protection frame counts must be nonnegative integers')
            v = positive(window.get('speed', 1), 'protected speed')
            first, last = event['frame']-before, event['frame']+after
            if first < start or last >= end:
                raise ValueError(f'{name}: protection outside take')
            for n in range(first, last+1):
                anchor(n, event['source_time']+(n-event['frame'])/fps*v)
            protected.append(dict(event=event['id'], first_frame=first, last_frame=last, speed=v))
        if start not in controls or end not in controls:
            raise ValueError(f'{name}: provide start/end controls')
        pairs = sorted(controls.items())
        x, y = np.array(pairs, float).T
        if np.any(np.diff(y) < -1e-10):
            raise ValueError(f'{name}: backwards source time; split reverse into a separate take')
        curve = PchipInterpolator(x, y)
        n = np.arange(start, end)
        source = curve(n)
        if np.any(np.diff(source) < -1e-10):
            raise ValueError('nonmonotone mapping')
        derivative = curve.derivative()(np.linspace(start, end, max(1000, end-start))) * fps
        native = np.rint(source*sfps).astype(int)
        takes.append(dict(id=name, source_fps=take['source_fps'],
                          output_start_frame=start, output_end_frame_exclusive=end,
                          anchors=pairs, protected_windows=protected,
                          minimum_speed=float(derivative.min()), maximum_speed=float(derivative.max()),
                          repeated_source_frame_steps=int(np.sum(np.diff(native)==0)),
                          maximum_source_frame_step=int(np.max(np.diff(native))) if len(native)>1 else 0,
                          frame_map=[dict(frame=int(i), source_time=float(s), source_frame=int(k))
                                     for i, s, k in zip(n, source, native)]))
    return dict(fps=plan['fps'], total_frames=total, actual_duration=total/fps,
                music_in=music_in, music_speed=speed, events=list(events.values()),
                continuous_takes=takes,
                limitation='CFR source-time plan only. Verify actual source PTS/duration, contact semantics and chosen musical accents.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('plan', type=Path)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    result = build(json.loads(a.plan.read_text(encoding='utf-8-sig')))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf8')
    print(f"{len(result['events'])} cues; {len(result['continuous_takes'])} continuous takes; {result['total_frames']} frames")


if __name__ == '__main__':
    main()
