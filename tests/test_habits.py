import json
import os
import shutil
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

TMP = Path(tempfile.mkdtemp())
os.environ["HABITS_DIR"] = str(TMP)

import habits  # noqa: E402  (après HABITS_DIR pour pointer sur le dossier temporaire)


HABIT = {
    "id": "shabbat",
    "name": "Mode Shabbat",
    "target_hours": 20,
    "burst_minutes": 20,
    "subskills": [],
    "tools": [],
    "checklist": [],
}


class HabitsTest(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TMP, ignore_errors=True)
        TMP.mkdir()
        habits.save_habits([HABIT])
        habits.save_sessions([])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP, ignore_errors=True)

    def test_add_session_persists(self):
        habits.add_session("shabbat", 25, 5, True, "banc du parc")
        stored = json.loads(habits.SESSIONS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["minutes"], 25)
        self.assertEqual(stored[0]["note"], "banc du parc")

    def test_real_session_requires_phone_free_and_quality(self):
        self.assertTrue(habits.is_real({"phone_free": True, "quality": 4}))
        self.assertFalse(habits.is_real({"phone_free": False, "quality": 5}))
        self.assertFalse(habits.is_real({"phone_free": True, "quality": 3}))

    def test_stats_progress_and_streak(self):
        today = date(2026, 9, 8)  # un mardi
        for offset, quality in ((0, 5), (1, 2), (2, 4)):
            when = datetime.combine(today - timedelta(days=offset), datetime.min.time())
            habits.add_session("shabbat", 30, quality, True, when=when)
        st = habits.compute_stats(HABIT, habits.load_sessions(), today=today)
        self.assertEqual(st["sessions"], 3)
        self.assertEqual(st["real_sessions"], 2)
        self.assertEqual(st["total_minutes"], 90)
        self.assertEqual(st["remaining_minutes"], 20 * 60 - 90)
        self.assertEqual(st["streak"], 3)
        self.assertEqual(st["week_sessions"], 2)  # lundi et mardi
        self.assertEqual(st["week_grid"][0], "○")  # lundi : session mais pas « vraiment rien »
        self.assertEqual(st["week_grid"][1], "●")  # mardi : vraiment rien
        self.assertIsNotNone(st["eta"])

    def test_streak_breaks_after_a_missed_day(self):
        today = date(2026, 9, 8)
        when = datetime.combine(today - timedelta(days=2), datetime.min.time())
        habits.add_session("shabbat", 20, 5, True, when=when)
        st = habits.compute_stats(HABIT, habits.load_sessions(), today=today)
        self.assertEqual(st["streak"], 0)

    def test_no_sessions_gives_no_eta(self):
        st = habits.compute_stats(HABIT, [], today=date(2026, 9, 8))
        self.assertIsNone(st["eta"])
        self.assertEqual(st["percent"], 0.0)

    def test_fmt_hours(self):
        self.assertEqual(habits.fmt_hours(0), "0 min")
        self.assertEqual(habits.fmt_hours(45), "45 min")
        self.assertEqual(habits.fmt_hours(60), "1h")
        self.assertEqual(habits.fmt_hours(125), "2h05")


if __name__ == "__main__":
    unittest.main()
