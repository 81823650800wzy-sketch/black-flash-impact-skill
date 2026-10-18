"""Source-derived contact body/sub layers. Does not denoise, detect or audition."""
from pathlib import Path
import argparse
import json
import math
import numpy as np
import soundfile as sf
from scipy import signal


def band(x, low, high, sr):
    high = min(high, sr*.45)
    return signal.sosfilt(signal.butter(3, [low, high], btype='bandpass', fs=sr, output='sos'), x)


def peak4(x):
    return float(np.max(np.abs(signal.resample_poly(x, 4, 1, axis=0))))


def branch(dry, onset, sr, low, high, target_frequency):
    mono = dry.mean(axis=1)
    energy = np.mean(dry*dry, axis=0)
    if float(np.mean(mono*mono)) < .04*float(energy.max()):
        mono = dry[:, int(np.argmax(energy))]  # Avoid cancelling an antiphase source.
    part = mono[onset:min(len(mono), onset+round(.080*sr))]
    result = np.zeros_like(dry)
    if len(part) < 8 or np.max(abs(part)) < 1e-7:
        return result, dict(ratio=None, reason='silent or too short')
    seed = band(part, 120, 4000, sr)
    power = np.abs(np.fft.rfft(seed))**2
    freq = np.fft.rfftfreq(len(seed), 1/sr)
    cumulative = np.cumsum(power*((freq>=120)&(freq<=4000)))
    if cumulative[-1] < 1e-14:
        return result, dict(ratio=None, reason='no usable source energy')
    centre = float(freq[min(len(freq)-1, np.searchsorted(cumulative, cumulative[-1]*.4))])
    ratio = float(np.clip(target_frequency/max(centre,120), 1/32, .65))
    count = min(len(dry)-onset, round(len(seed)/ratio))
    pitched = np.interp(np.arange(count)*ratio, np.arange(len(seed)), seed)
    wet = band(pitched, low, high, sr)
    # Preserve the original attack location and taper only the derived tail.
    fade = min(len(wet)//3, round(.040*sr))
    if fade:
        wet[-fade:] *= np.linspace(1, 0, fade)
    source_rms = math.sqrt(float(np.mean(part**2)))
    wet_rms = math.sqrt(float(np.mean(wet**2)))
    # Cap relative gain: weak or unusable bands do not become arbitrary booms.
    gain = min(8.0, source_rms/max(wet_rms, 1e-9))
    result[onset:onset+count] = (wet*gain)[:, None]
    return result, dict(ratio=ratio, source_centre_hz=centre, bounded_gain=gain,
                        band_hz=[low, high], source_samples=len(part))


def enhance(x, sr, onset_seconds, pre=.006, post=.45, body_db=-6, sub_db=-10, ceiling_db=-1.5):
    if x.ndim == 1:
        x = x[:, None]
    if not np.all(np.isfinite(x)) or len(x)==0 or sr < 16000 or x.shape[1] not in [1,2]:
        raise ValueError('Need nonempty finite mono/stereo audio at >=16000 Hz')
    values = [onset_seconds, pre, post, body_db, sub_db, ceiling_db]
    if not all(math.isfinite(v) for v in values) or not 0 <= onset_seconds < len(x)/sr:
        raise ValueError('Invalid onset or parameters')
    if pre < 0 or post <= 0 or ceiling_db >= 0 or max(body_db,sub_db)>12:
        raise ValueError('Invalid window, ceiling or excessive layer gain')
    onset_input = round(onset_seconds*sr)
    if onset_input >= len(x):
        raise ValueError('Rounded onset lies outside audio')
    first, last = max(0,onset_input-round(pre*sr)), min(len(x),onset_input+round(post*sr))
    dry = x[first:last].astype(np.float64, copy=True)
    onset = onset_input-first
    body, br = branch(dry,onset,sr,80,280,150)
    sub, su = branch(dry,onset,sr,30,90,55)
    body *= 10**(body_db/20)
    sub *= 10**(sub_db/20)
    summed = dry+body+sub
    # Bound only excursions at 4x rate; no cue-wide peak normalisation.
    up = signal.resample_poly(summed,4,1,axis=0)
    ceiling = 10**(ceiling_db/20)
    clipped = np.clip(up,-ceiling,ceiling)
    if np.array_equal(up, clipped):
        master = summed.copy()  # No resampling alteration when no peak exceeds.
    else:
        master = signal.resample_poly(clipped,1,4,axis=0)[:len(dry)]
    # Downsampling can produce tiny overshoot: reserve 0.1 dB and report it.
    p = peak4(master)
    if p > ceiling*1.001:
        master *= ceiling*10**(-.1/20)/p
    rms = lambda a: float(np.sqrt(np.mean(a*a)))
    layers = dict(dry_contact=dry, body=body, sub=sub, pre_master=summed,
                  master_process_difference=master-summed, mix=master)
    report = dict(sample_rate=sr, input_window_start_sample=first, input_window_end_sample=last,
                  onset_sample=onset, onset_input_sample=onset_input, channels=x.shape[1],
                  body=br, sub=su, body_db=body_db, sub_db=sub_db,
                  ceiling_db=ceiling_db, pre_master_4x_peak=peak4(summed), master_4x_peak=peak4(master),
                  dry_rms=rms(dry), body_rms=rms(body), sub_rms=rms(sub),
                  policy='Derived from this contact recording. No denoising, replacement oscillator or generated noise.',
                  processing='4x excursion clipping; small final overshoot guard if needed, reported by measured peaks. Not a transparent mastering limiter or certified true-peak meter.',
                  mix_reconstruction='dry_contact + body + sub + master_process_difference = mix; do not add pre_master again.')
    return layers, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input',type=Path)
    ap.add_argument('--onset',type=float,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--pre',type=float,default=.006)
    ap.add_argument('--post',type=float,default=.45)
    ap.add_argument('--body-db',type=float,default=-6)
    ap.add_argument('--sub-db',type=float,default=-10)
    ap.add_argument('--ceiling-db',type=float,default=-1.5)
    a=ap.parse_args()
    x,sr=sf.read(a.input,always_2d=True,dtype='float64')
    layers,report=enhance(x,sr,a.onset,a.pre,a.post,a.body_db,a.sub_db,a.ceiling_db)
    a.out.mkdir(parents=True,exist_ok=True)
    for name,data in layers.items():
        sf.write(a.out/(name+'.wav'),data,sr,subtype='FLOAT')
    (a.out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
