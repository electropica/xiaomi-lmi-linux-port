"""Boundary checks: exclude charging, scale drift, reboot and missing counters."""
import copy, unittest
from model import analyze

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

if __name__=='__main__':unittest.main()
