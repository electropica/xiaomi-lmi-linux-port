"""Boundary checks: exclude charging, scale drift, reboot and missing counters."""
import copy, unittest, tempfile,json
from pathlib import Path
from model import analyze,load,iter_rows

def row(t, counter, event='sample'):
    return {'boottime':t,'monotonic':t,'boot_id':'same','usb':'0','event':event,
            'supplies':{'battery':{'status':'Discharging'},'bms':{
                'charge_counter':counter,'charge_counter_shadow':counter,
                'charge_now_raw':counter,'charge_full':2806000,'charge_full_design':4700000}}}

class Boundaries(unittest.TestCase):
    def test_known_interval(self):
        result=analyze([row(0,2000),row(3600,1000)])
        self.assertEqual(result['methods']['charge_counter']['estimated_ma'],1)
    def test_charging_is_excluded(self):
        b=row(3600,1000);b['usb']='1'
        self.assertIsNone(analyze([row(0,2000),b])['methods']['charge_counter']['estimated_ma'])
    def test_scale_drift_is_excluded(self):
        b=row(3600,1000);b['supplies']['bms']['charge_full']=2700000
        result=analyze([row(0,2000),b])
        self.assertIsNone(result['methods']['charge_counter']['estimated_ma'])
        self.assertEqual(result['methods']['charge_now_raw']['estimated_ma'],1)
    def test_missing_counter_separate_coverage(self):
        b=row(3600,1000);b['supplies']['bms']['charge_now_raw']=None
        result=analyze([row(0,2000),b])
        self.assertEqual(result['methods']['charge_counter']['duration_s'],3600)
        self.assertEqual(result['methods']['charge_now_raw']['duration_s'],0)
    def test_reboot_excluded(self):
        b=row(3600,1000);b['boot_id']='different'
        self.assertIsNone(analyze([row(0,2000),b])['methods']['charge_counter']['estimated_ma'])
    def test_counter_increase_excluded(self):
        self.assertIsNone(analyze([row(0,1000),row(3600,2000)])['methods']['charge_counter']['estimated_ma'])
    def test_sleep_uses_clock_difference(self):
        a=row(0,2000,'prepare-sleep');b=row(180,1900,'resume-signal');b['monotonic']=2
        self.assertEqual(analyze([a,b])['sleep_s'],178)
    def test_invalid_sleep_not_claimed(self):
        a=row(0,2000,'prepare-sleep');b=row(180,1900,'resume-signal');b['monotonic']=200
        self.assertEqual(analyze([a,b])['sleep_s'],0)
        self.assertEqual(analyze([a,b])['valid_sleep_pairs'],0)
    def test_incomplete_sleep_warns(self):
        result=analyze([row(0,2000,'prepare-sleep')])
        self.assertEqual(result['valid_sleep_pairs'],0)
        self.assertTrue(result['warnings'])
    def test_history_view_is_bounded_but_stream_is_complete(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path=Path(folder)/'long.jsonl'
            path.write_text(''.join(json.dumps(row(t,2000-t))+'\n' for t in range(20)))
            self.assertEqual([r['boottime'] for r in load(path,max_rows=3)],[17,18,19])
            self.assertEqual(len(list(iter_rows(path))),20)
    def test_partial_tail_is_not_a_record(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path=Path(folder)/'partial.jsonl'
            path.write_text(json.dumps(row(0,2000))+'\n'+json.dumps(row(1,1999))[:30])
            self.assertEqual(len(load(path)),1)

if __name__=='__main__':unittest.main()
