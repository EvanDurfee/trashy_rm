import unittest
import trashy_rm


class TestHarness(unittest.TestCase):
    def test_harness(self):
        app_config = trashy_rm.AppConfig()
        exec_config = trashy_rm.ExecutionConfig()
        self.assertEqual(0, trashy_rm.run(app_config, exec_config))


if __name__ == '__main__':
    unittest.main()
