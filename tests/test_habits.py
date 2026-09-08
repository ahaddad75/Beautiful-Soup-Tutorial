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

REPO_CONFIG = Path(__file__).resolve().parent.parent / "habits.json"

MINUTES_HABIT = {
    "id": "shabbat",
    "name": "Mode Shabbat",
    "unit": "minutes",
    "target_hours": 20,
    "burst_minutes": 20,
    "subskills": [],
    "tools": [],
    "checklist": [],
}
DAYS_HABIT = {
    "id": "nofap",
    "name": "No fap",
    "unit": "days",
    "target_days": 90,
    "subskills": [],
    "tools": [],
    "checklist": [],
}


class HabitsTest(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TMP, ignore_errors=True)
        TMP.mkdir()
        habits.save_habits([MINUTES_HABIT, DAYS_HABIT])
        habits.save_sessions([])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TMP, ignore_errors=True)

    def test_add_session_persists(self):
        habits.add_session("shabbat", 25, 5, True, "banc du parc")
        stored = json.loads(habits.SESSIONS_FILE.read_text(encoding="utf-8"))
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["minutes"], 25)
        self.assertEqual(stored[0]["clean"], True)
        self.assertEqual(stored[0]["note"], "banc du parc")

    def test_real_session_requires_clean_and_quality(self):
        self.assertTrue(habits.is_real({"clean": True, "quality": 4}, MINUTES_HABIT))
        self.assertFalse(habits.is_real({"clean": False, "quality": 5}, MINUTES_HABIT))
        self.assertFalse(habits.is_real({"clean": True, "quality": 3}, MINUTES_HABIT))
        # En mode jours, seule la contrainte compte.
        self.assertTrue(habits.is_real({"clean": True, "quality": 2}, DAYS_HABIT))
        self.assertFalse(habits.is_real({"clean": False, "quality": 5}, DAYS_HABIT))

    def test_stats_progress_and_streak(self):
        today = date(2026, 9, 8)  # un mardi
        for offset, quality in ((0, 5), (1, 2), (2, 4)):
            when = datetime.combine(today - timedelta(days=offset), datetime.min.time())
            habits.add_session("shabbat", 30, quality, True, when=when)
        st = habits.compute_stats(MINUTES_HABIT, habits.load_sessions(), today=today)
        self.assertEqual(st["unit"], "minutes")
        self.assertEqual(st["sessions"], 3)
        self.assertEqual(st["real_sessions"], 2)
        self.assertEqual(st["total"], 90)
        self.assertEqual(st["remaining"], 20 * 60 - 90)
        self.assertEqual(st["streak"], 3)
        self.assertEqual(st["week_sessions"], 2)  # lundi et mardi
        self.assertEqual(st["week_grid"][0], "○")  # lundi : session mais pas « vraiment réussie »
        self.assertEqual(st["week_grid"][1], "●")  # mardi : vraiment réussie
        self.assertIsNotNone(st["eta"])

    def test_streak_breaks_after_a_missed_day(self):
        today = date(2026, 9, 8)
        when = datetime.combine(today - timedelta(days=2), datetime.min.time())
        habits.add_session("shabbat", 20, 5, True, when=when)
        st = habits.compute_stats(MINUTES_HABIT, habits.load_sessions(), today=today)
        self.assertEqual(st["streak"], 0)

    def test_days_habit_counts_kept_days(self):
        today = date(2026, 9, 8)
        for offset, kept in ((0, True), (1, True), (2, False), (3, True)):
            when = datetime.combine(today - timedelta(days=offset), datetime.min.time())
            habits.add_session("nofap", 0, 5 if kept else 1, kept, when=when)
        st = habits.compute_stats(DAYS_HABIT, habits.load_sessions(), today=today)
        self.assertEqual(st["unit"], "days")
        self.assertEqual(st["total"], 3)  # trois jours tenus
        self.assertEqual(st["target"], 90)
        self.assertEqual(st["remaining"], 87)
        self.assertEqual(st["streak"], 2)  # l'écart d'avant-hier casse la série
        self.assertEqual(st["real_sessions"], 3)
        self.assertEqual(st["week_grid"][0], "●")  # lundi tenu
        self.assertEqual(st["week_grid"][1], "●")  # mardi tenu

    def test_days_habit_does_not_double_count_a_day(self):
        today = date(2026, 9, 8)
        when = datetime.combine(today, datetime.min.time())
        habits.add_session("nofap", 0, 5, True, when=when)
        habits.add_session("nofap", 0, 5, True, when=when)
        st = habits.compute_stats(DAYS_HABIT, habits.load_sessions(), today=today)
        self.assertEqual(st["total"], 1)

    def test_no_sessions_gives_no_eta(self):
        st = habits.compute_stats(MINUTES_HABIT, [], today=date(2026, 9, 8))
        self.assertIsNone(st["eta"])
        self.assertEqual(st["percent"], 0.0)

    def test_fmt_hours(self):
        self.assertEqual(habits.fmt_hours(0), "0 min")
        self.assertEqual(habits.fmt_hours(45), "45 min")
        self.assertEqual(habits.fmt_hours(60), "1h")
        self.assertEqual(habits.fmt_hours(125), "2h05")

    def test_repo_config_is_well_formed(self):
        config = json.loads(REPO_CONFIG.read_text(encoding="utf-8"))
        ids = [h["id"] for h in config["habits"]]
        self.assertEqual(len(ids), len(set(ids)), "identifiants en double")
        for habit in config["habits"]:
            self.assertIn(habit.get("unit", "minutes"), ("minutes", "days"))
            if habit.get("unit") == "days":
                self.assertIn("target_days", habit)
            else:
                self.assertIn("target_hours", habit)
                self.assertIn("burst_minutes", habit)
            for entry in habit.get("science", []):
                self.assertTrue(entry["finding"] and entry["source"])
        self.assertTrue(config["method_science"])


if __name__ == "__main__":
    unittest.main()
