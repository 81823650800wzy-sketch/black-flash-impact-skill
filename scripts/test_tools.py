"""Behavior checks using temporary synthetic fixtures; no private media."""
from pathlib import Path
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import numpy as np
import soundfile as sf
from plan_timing import build
from enhance_contact import enhance

ROOT=Path(__file__).resolve().parents[1]


class Timing(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((ROOT/'examples/timing.json').read_text(encoding='utf8'))

    def test_absolute_cues_and_monotone_protected_mapping(self):
        r=build(self.plan);fps=30000/1001
        self.assertEqual([e['frame'] for e in r['events']],[45,120])
        take=r['continuous_takes'][0];fm={z['frame']:z for z in take['frame_map']}
        self.assertTrue(np.all(np.diff([z['source_time'] for z in fm.values()])>=0))
        for event in r['events']:
            self.assertLessEqual(abs(event['quantisation_ms']),500/fps+1e-8)
            self.assertAlmostEqual(fm[event['frame']]['source_time'],event['source_time'])
        for w in take['protected_windows']:
            times=[fm[n]['source_time'] for n in range(w['first_frame'],w['last_frame']+1)]
            np.testing.assert_allclose(np.diff(times),w['speed']/fps,atol=1e-12)

    def test_absolute_clock_does_not_drift(self):
        p=dict(fps='24000/1001',duration=101,music=dict(in_=0))
        p['music']={'in':18.2,'speed':1}
        p['events']=[dict(id=str(i),music_time=18.2+i*.137,source_time=i*.2) for i in range(700)]
        r=build(p)
        self.assertEqual(r['events'][-1]['frame'],round(699*.137*24000/1001))

    def test_conflicts_reverse_and_outside_rejected(self):
        p=copy.deepcopy(self.plan);p['continuous_takes'][0]['controls'].append([1.5,99])
        with self.assertRaises(ValueError):build(p)
        p=copy.deepcopy(self.plan);p['continuous_takes'][0]['controls'][-1][1]=1
        with self.assertRaises(ValueError):build(p)
        p=copy.deepcopy(self.plan);p['events'][0]['music_time']=1
        with self.assertRaises(ValueError):build(p)


class Audio(unittest.TestCase):
    def fixture(self,frequency=780,amplitude=.35):
        sr=48000;x=np.zeros((sr,2));t=np.arange(round(.12*sr))/sr
        # Signal only tests source distinction and placement, not desired sound.
        wave=amplitude*np.exp(-t*70)*(np.cos(2*np.pi*frequency*t)+.25*np.cos(2*np.pi*231*t))
        x[4800:4800+len(t)]=wave[:,None]
        return x,sr

    def test_dry_onset_layers_and_reconstruction(self):
        x,sr=self.fixture();layers,r=enhance(x,sr,.1)
        lo,hi=r['input_window_start_sample'],r['input_window_end_sample']
        np.testing.assert_array_equal(layers['dry_contact'],x[lo:hi])
        self.assertEqual(r['onset_sample'],288)
        self.assertTrue(np.all(layers['body'][:288]==0))
        self.assertTrue(np.all(layers['sub'][:288]==0))
        self.assertGreater(np.max(abs(layers['body'])),0)
        self.assertLessEqual(r['master_4x_peak'],10**(-1.5/20)*1.001)
        np.testing.assert_allclose(layers['dry_contact']+layers['body']+layers['sub']+layers['master_process_difference'],layers['mix'],atol=1e-14)

    def test_silence_and_different_contacts(self):
        zero=np.zeros((48000,1));layers,r=enhance(zero,48000,.1)
        self.assertEqual(np.max(abs(layers['mix'])),0)
        a,sr=self.fixture(420);b,_=self.fixture(1800)
        la,ra=enhance(a,sr,.1);lb,rb=enhance(b,sr,.1)
        self.assertFalse(np.allclose(la['body'],lb['body']))
        self.assertNotEqual(ra['body']['ratio'],rb['body']['ratio'])

    def test_hot_and_antiphase_input(self):
        x,sr=self.fixture(amplitude=1.8);x[:,1]*=-1
        layers,r=enhance(x,sr,.1)
        self.assertGreater(np.max(abs(layers['body'])),0)
        self.assertLessEqual(r['master_4x_peak'],10**(-1.5/20)*1.001)
        with self.assertRaises(ValueError):enhance(x,sr,-.1)

    def test_moved_directory_cli(self):
        with tempfile.TemporaryDirectory(prefix='impact-tools-') as tmp:
            moved=Path(tmp)/'moved';shutil.copytree(ROOT/'scripts',moved/'scripts')
            shutil.copytree(ROOT/'examples',moved/'examples')
            x,sr=self.fixture();sf.write(moved/'contact.wav',x,sr,subtype='FLOAT')
            commands=[
                [sys.executable,str(moved/'scripts/plan_timing.py'),str(moved/'examples/timing.json'),'--out',str(moved/'timing.json')],
                [sys.executable,str(moved/'scripts/enhance_contact.py'),str(moved/'contact.wav'),'--onset','.1','--out',str(moved/'enhanced')]
            ]
            for command in commands:
                subprocess.run(command,cwd=tmp,check=True,capture_output=True,text=True)
            r=json.loads((moved/'enhanced/report.json').read_text(encoding='utf8'))
            dry,_=sf.read(moved/'enhanced/dry_contact.wav',always_2d=True)
            source,_=sf.read(moved/'contact.wav',always_2d=True)
            np.testing.assert_array_equal(dry,source[r['input_window_start_sample']:r['input_window_end_sample']])
            self.assertEqual(len(json.loads((moved/'timing.json').read_text())['events']),2)


if __name__=='__main__':
    unittest.main(verbosity=2)
