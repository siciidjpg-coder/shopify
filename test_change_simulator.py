import unittest
from change_simulator import Simulator


class RehearsalTests(unittest.TestCase):
    def test_decrease_increase_and_rollback(self):
        s = Simulator({"v": "100"})
        s.apply("one", "v", "100", "80", verified=True)
        self.assertIsNotNone(s.preview_alert())
        s.rollback("one")
        self.assertEqual(str(s.prices["v"]), "100.00")
        self.assertIsNone(s.preview_alert())
        s.apply("two", "v", "100", "110", verified=True)
        self.assertEqual(str(s.prices["v"]), "110.00")

    def test_exact_threshold_and_replay(self):
        s = Simulator({"v": "100", "w": "100"})
        s.apply("a", "v", "100", "85", verified=True)
        self.assertIsNone(s.preview_alert())
        s.apply("b", "w", "100", "84.99", verified=True)
        s.apply("b", "w", "100", "84.99", verified=True)
        self.assertEqual(len(s.audit), 2)
        self.assertEqual(s.preview_alert().get_content().count("84.99"), 1)

    def test_errors_never_produce_alert_or_change(self):
        s = Simulator({"v": "100"})
        with self.assertRaises(RuntimeError):
            s.apply("a", "v", "100", "20", verified=True, fail=True)
        self.assertEqual(str(s.prices["v"]), "100.00")
        self.assertIsNone(s.preview_alert())
        with self.assertRaises(ValueError):
            s.apply("b", "v", "100", "20")

    def test_conflict_stop_and_lock(self):
        s = Simulator({"v": "100"})
        with self.assertRaises(ValueError):
            s.apply("a", "v", "99", "20", verified=True)
        s.locked.add("v")
        with self.assertRaises(ValueError):
            s.apply("a", "v", "100", "20", verified=True)
        s.locked.clear()
        s.stopped = True
        with self.assertRaises(ValueError):
            s.apply("a", "v", "100", "20", verified=True)

    def test_rollback_preserves_later_change(self):
        s = Simulator({"v": "100"})
        s.apply("a", "v", "100", "80", verified=True)
        s.apply("b", "v", "80", "70", verified=True)
        with self.assertRaises(ValueError): s.rollback("a")
        with self.assertRaises(ValueError): s.apply("b", "v", "80", "60", verified=True)
