import unittest
from rapport import render


class ReportTests(unittest.TestCase):
    def test_empty_capture_is_reported_without_inventing_a_cause(self):
        result = render([])
        self.assertIn('Échantillons : 0', result)
        self.assertNotIn('Suspensions réussies : 0', result)

    def test_replugged_endpoint_is_not_presented_as_isolated_discharge(self):
        def sample(status, capacity):
            return {'event': 'sample', 'boot_id': 'boot', 'suspend_success': '1',
                    'suspend_fail': '0', 'battery': {'qcom-battery': {'status': status, 'capacity': capacity}}}
        result = render([sample('Discharging', '40'), sample('Charging', '35')])
        self.assertIn('déjà en charge', result)
        self.assertIn('40 % (en décharge)', result)


if __name__ == '__main__':
    unittest.main()
