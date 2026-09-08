#!/usr/bin/env python3
"""Traqueur d'habitudes inspiré de « The First 20 Hours » de Josh Kaufman.

Une habitude = une compétence à acquérir en 20 heures de pratique délibérée.
Le script sert à pratiquer par courtes sessions chronométrées, à enregistrer
chaque session honnêtement et à voir la progression vers les 20 heures.

Usage rapide :
    python habits.py start shabbat        # checklist, minuteur, bilan
    python habits.py log shabbat 25       # enregistrer une session après coup
    python habits.py status               # progression vers les 20 heures
    python habits.py --help               # toutes les commandes
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(os.environ.get("HABITS_DIR", Path(__file__).resolve().parent))
HABITS_FILE = ROOT / "habits.json"
SESSIONS_FILE = ROOT / "data" / "sessions.json"

# Une session compte comme « vraiment rien » si le portable est resté hors de
# portée ET que la qualité ressentie est d'au moins 4 sur 5.
REAL_QUALITY_MIN = 4

QUALITY_LABELS = {
    1: "J'ai craqué : portable, écran ou tâche",
    2: "Agité, j'ai surtout attendu que ça passe",
    3: "Moitié rien, moitié occupé dans ma tête",
    4: "Presque rien, quelques réflexes de vouloir faire",
    5: "Vraiment rien : marcher, regarder, laisser divaguer",
}

WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"]


# --------------------------------------------------------------------------- #
# Stockage
# --------------------------------------------------------------------------- #
def load_habits() -> list[dict]:
    if not HABITS_FILE.exists():
        return []
    with open(HABITS_FILE, encoding="utf-8") as f:
        return json.load(f).get("habits", [])


def save_habits(habits: list[dict]) -> None:
    with open(HABITS_FILE, "w", encoding="utf-8") as f:
        json.dump({"habits": habits}, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_sessions() -> list[dict]:
    if not SESSIONS_FILE.exists():
        return []
    with open(SESSIONS_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_sessions(sessions: list[dict]) -> None:
    SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)
        f.write("\n")


def get_habit(habit_id: str) -> dict:
    for habit in load_habits():
        if habit["id"] == habit_id:
            return habit
    ids = ", ".join(h["id"] for h in load_habits()) or "(aucune)"
    sys.exit(f"Habitude inconnue : « {habit_id} ». Habitudes disponibles : {ids}")


def add_session(
    habit_id: str,
    minutes: int,
    quality: int,
    phone_free: bool,
    note: str = "",
    when: datetime | None = None,
) -> dict:
    when = when or datetime.now()
    session = {
        "habit": habit_id,
        "date": when.strftime("%Y-%m-%d"),
        "time": when.strftime("%H:%M"),
        "minutes": int(minutes),
        "quality": int(quality),
        "phone_free": bool(phone_free),
        "note": note.strip(),
    }
    sessions = load_sessions()
    sessions.append(session)
    sessions.sort(key=lambda s: (s["date"], s["time"]))
    save_sessions(sessions)
    return session


# --------------------------------------------------------------------------- #
# Calculs
# --------------------------------------------------------------------------- #
def is_real(session: dict) -> bool:
    return session["phone_free"] and session["quality"] >= REAL_QUALITY_MIN


def compute_stats(habit: dict, sessions: list[dict], today: date | None = None) -> dict:
    today = today or date.today()
    mine = [s for s in sessions if s["habit"] == habit["id"]]
    total_minutes = sum(s["minutes"] for s in mine)
    target_minutes = int(habit.get("target_hours", 20) * 60)
    real = [s for s in mine if is_real(s)]

    days_with_session = {date.fromisoformat(s["date"]) for s in mine}
    streak = 0
    cursor = today if today in days_with_session else today - timedelta(days=1)
    while cursor in days_with_session:
        streak += 1
        cursor -= timedelta(days=1)

    monday = today - timedelta(days=today.weekday())
    week = [s for s in mine if date.fromisoformat(s["date"]) >= monday]
    week_grid = []
    for offset in range(7):
        day = monday + timedelta(days=offset)
        day_sessions = [s for s in mine if s["date"] == day.isoformat()]
        if not day_sessions:
            week_grid.append("·")
        elif any(is_real(s) for s in day_sessions):
            week_grid.append("●")
        else:
            week_grid.append("○")

    window_start = today - timedelta(days=13)
    recent = [s for s in mine if date.fromisoformat(s["date"]) >= window_start]
    pace_per_day = sum(s["minutes"] for s in recent) / 14
    remaining = max(target_minutes - total_minutes, 0)
    if remaining == 0:
        eta = today
    elif pace_per_day > 0:
        eta = today + timedelta(days=round(remaining / pace_per_day))
    else:
        eta = None

    return {
        "sessions": len(mine),
        "real_sessions": len(real),
        "total_minutes": total_minutes,
        "target_minutes": target_minutes,
        "remaining_minutes": remaining,
        "percent": min(100.0, 100.0 * total_minutes / target_minutes) if target_minutes else 0.0,
        "streak": streak,
        "week_sessions": len(week),
        "week_minutes": sum(s["minutes"] for s in week),
        "week_grid": week_grid,
        "pace_per_day": pace_per_day,
        "eta": eta,
        "avg_quality": (sum(s["quality"] for s in mine) / len(mine)) if mine else 0.0,
        "longest": max((s["minutes"] for s in mine), default=0),
        "last": mine[-1] if mine else None,
    }


def fmt_hours(minutes: int) -> str:
    h, m = divmod(int(minutes), 60)
    if h and m:
        return f"{h}h{m:02d}"
    if h:
        return f"{h}h"
    return f"{m} min"


def progress_bar(percent: float, width: int = 40) -> str:
    filled = int(round(width * percent / 100))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def fmt_date(d: date) -> str:
    months = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
              "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    return f"{d.day} {months[d.month - 1]} {d.year}"


# --------------------------------------------------------------------------- #
# Affichage
# --------------------------------------------------------------------------- #
def print_status(habit: dict, sessions: list[dict]) -> None:
    st = compute_stats(habit, sessions)
    print(f"\n{habit['name']}  ({habit['id']})")
    print(f"{progress_bar(st['percent'])} {fmt_hours(st['total_minutes'])} / "
          f"{fmt_hours(st['target_minutes'])}  ({st['percent']:.0f} %)")
    if st["sessions"] == 0:
        print("Aucune session pour l'instant. Lance : python habits.py start", habit["id"])
        return
    real_pct = 100.0 * st["real_sessions"] / st["sessions"]
    print(f"Sessions : {st['sessions']}   dont « vraiment rien » : "
          f"{st['real_sessions']} ({real_pct:.0f} %)")
    grid = " ".join(f"{d}{m}" for d, m in zip(WEEKDAYS, st["week_grid"]))
    print(f"Série : {st['streak']} jour(s)   Cette semaine : {st['week_sessions']} session(s), "
          f"{fmt_hours(st['week_minutes'])}   {grid}")
    if st["remaining_minutes"] == 0:
        print("Objectif des 20 heures atteint. Fixe un nouveau niveau cible avec `deconstruct`.")
    elif st["eta"]:
        print(f"Rythme sur 14 jours : {st['pace_per_day']:.0f} min/jour → "
              f"objectif atteint vers le {fmt_date(st['eta'])}")
    else:
        print("Rythme sur 14 jours : 0 min/jour → pas de projection possible, reprends une session.")
    print(f"Qualité moyenne : {st['avg_quality']:.1f}/5   Plus longue session : "
          f"{fmt_hours(st['longest'])}")


def print_session_feedback(habit: dict, session: dict) -> None:
    st = compute_stats(habit, load_sessions())
    tag = "vraiment rien ✔" if is_real(session) else "session comptée, mais pas « vraiment rien »"
    print(f"\nEnregistré : {session['minutes']} min, qualité {session['quality']}/5, {tag}.")
    print(f"Total : {fmt_hours(st['total_minutes'])} sur {fmt_hours(st['target_minutes'])} "
          f"({st['percent']:.0f} %) · {st['real_sessions']} sessions « vraiment rien » sur "
          f"{st['sessions']} · série de {st['streak']} jour(s).")


# --------------------------------------------------------------------------- #
# Saisie interactive
# --------------------------------------------------------------------------- #
def ask_yes(prompt: str, default: bool = True) -> bool:
    suffix = " [O/n] " if default else " [o/N] "
    answer = input(prompt + suffix).strip().lower()
    if not answer:
        return default
    return answer in ("o", "oui", "y", "yes")


def ask_quality() -> int:
    print("\nHonnêtement, cette session c'était :")
    for k, label in QUALITY_LABELS.items():
        print(f"  {k}  {label}")
    while True:
        answer = input("Qualité (1-5) : ").strip()
        if answer in ("1", "2", "3", "4", "5"):
            return int(answer)
        print("Réponds par un chiffre de 1 à 5.")


def run_timer(minutes: int) -> int:
    """Compte à rebours. Retourne les minutes réellement écoulées (Ctrl+C arrête)."""
    total = minutes * 60
    start = time.monotonic()
    print(f"\nMinuteur lancé pour {minutes} min. Pose le portable ailleurs, ne regarde plus l'écran.")
    print("Ctrl+C pour arrêter plus tôt (la session sera quand même comptée).\n")
    try:
        while True:
            elapsed = time.monotonic() - start
            left = total - elapsed
            if left <= 0:
                break
            m, s = divmod(int(left), 60)
            print(f"\r  {m:02d}:{s:02d} restantes ", end="", flush=True)
            time.sleep(min(1.0, left))
        print("\r  00:00 — c'est fini.      \a")
    except KeyboardInterrupt:
        print("\n  Arrêt anticipé.")
    elapsed_minutes = int(round((time.monotonic() - start) / 60))
    return max(elapsed_minutes, 1)


# --------------------------------------------------------------------------- #
# Commandes
# --------------------------------------------------------------------------- #
def cmd_list(args: argparse.Namespace) -> None:
    habits = load_habits()
    if not habits:
        print("Aucune habitude. Ajoute-en une avec : python habits.py add")
        return
    sessions = load_sessions()
    for habit in habits:
        st = compute_stats(habit, sessions)
        print(f"{habit['id']:<12} {progress_bar(st['percent'], 20)} "
              f"{fmt_hours(st['total_minutes']):>7} / {fmt_hours(st['target_minutes'])}"
              f"   {st['real_sessions']}/{st['sessions']} vraiment rien")


def cmd_status(args: argparse.Namespace) -> None:
    habits = load_habits()
    if args.habit:
        habits = [get_habit(args.habit)]
    if not habits:
        print("Aucune habitude. Ajoute-en une avec : python habits.py add")
        return
    sessions = load_sessions()
    for habit in habits:
        print_status(habit, sessions)


def cmd_deconstruct(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    print(f"\n{habit['name']}")
    print(f"\nPourquoi (projet aimé) :\n  {habit.get('why', '—')}")
    print(f"\nNiveau cible (target performance level) :\n  {habit.get('target_performance', '—')}")
    print(f"\nObjectif : {habit.get('target_hours', 20)} heures, par sessions de "
          f"{habit.get('burst_minutes', 20)} min.")
    print("\nSous-compétences (déconstruction) :")
    for i, item in enumerate(habit.get("subskills", []), 1):
        print(f"  {i}. {item}")
    print("\nOutils critiques :")
    for item in habit.get("tools", []):
        print(f"  - {item}")
    print("\nChecklist avant chaque session (éliminer les barrières) :")
    for item in habit.get("checklist", []):
        print(f"  [ ] {item}")
    print()


def cmd_start(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    minutes = args.minutes or habit.get("burst_minutes", 20)
    print(f"\n{habit['name']}")
    print(f"Cible : {habit.get('target_performance', '')}\n")
    print("Checklist :")
    for item in habit.get("checklist", []):
        print(f"  [ ] {item}")
    if not ask_yes("\nTout est en place ?"):
        print("Ok, règle ce qui manque et relance. Les barrières doivent tomber avant de pratiquer.")
        return
    elapsed = run_timer(minutes)
    quality = ask_quality()
    phone_free = ask_yes("Le portable est resté hors de portée tout le long ?")
    note = input("Une note (facultatif) : ")
    session = add_session(habit["id"], elapsed, quality, phone_free, note)
    print_session_feedback(habit, session)


def cmd_log(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    quality = args.quality if args.quality else ask_quality()
    if args.phone is None:
        phone_free = ask_yes("Le portable est resté hors de portée tout le long ?")
    else:
        phone_free = args.phone
    when = datetime.now()
    if args.date:
        when = datetime.combine(date.fromisoformat(args.date), when.time())
    session = add_session(habit["id"], args.minutes, quality, phone_free, args.note or "", when)
    print_session_feedback(habit, session)


def cmd_history(args: argparse.Namespace) -> None:
    sessions = load_sessions()
    if args.habit:
        get_habit(args.habit)
        sessions = [s for s in sessions if s["habit"] == args.habit]
    sessions = sessions[-args.last:]
    if not sessions:
        print("Aucune session enregistrée.")
        return
    print(f"{'date':<10} {'heure':<5} {'habitude':<10} {'min':>4} {'qual':>4} {'rien':>5}  note")
    for s in sessions:
        mark = "oui" if is_real(s) else "non"
        print(f"{s['date']:<10} {s['time']:<5} {s['habit']:<10} {s['minutes']:>4} "
              f"{s['quality']:>4} {mark:>5}  {s['note']}")


def cmd_plan(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    st = compute_stats(habit, load_sessions())
    remaining = st["remaining_minutes"]
    days = args.weeks * 7
    per_day = remaining / days
    burst = habit.get("burst_minutes", 20)
    print(f"\n{habit['name']}")
    print(f"Il reste {fmt_hours(remaining)} pour atteindre {fmt_hours(st['target_minutes'])}.")
    print(f"Pour finir en {args.weeks} semaine(s) : {per_day:.0f} min/jour, "
          f"soit environ {per_day / burst:.1f} session(s) de {burst} min par jour.")
    print("Kaufman : bloque ce créneau dans l'agenda maintenant, sinon il n'existera pas.\n")


def cmd_add(args: argparse.Namespace) -> None:
    habits = load_habits()
    habit_id = args.id or input("Identifiant court (ex: lecture) : ").strip().lower()
    if any(h["id"] == habit_id for h in habits):
        sys.exit(f"L'habitude « {habit_id} » existe déjà.")
    print("\nPrincipe 1 — un projet qu'on aime. Principe 3 — un niveau cible précis.")
    habit = {
        "id": habit_id,
        "name": args.name or input("Nom complet : ").strip(),
        "why": input("Pourquoi tu y tiens vraiment : ").strip(),
        "target_performance": input("À quoi ressemble « assez bon » pour toi (observable, concret) : ").strip(),
        "target_hours": args.target_hours,
        "burst_minutes": args.burst,
        "subskills": [s.strip() for s in input("Sous-compétences (séparées par ;) : ").split(";") if s.strip()],
        "tools": [s.strip() for s in input("Outils nécessaires (séparés par ;) : ").split(";") if s.strip()],
        "checklist": [s.strip() for s in input("Checklist avant session (séparée par ;) : ").split(";") if s.strip()],
    }
    habits.append(habit)
    save_habits(habits)
    print(f"\nHabitude « {habit_id} » créée. Première session : python habits.py start {habit_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habits.py",
        description="Traqueur d'habitudes façon « The First 20 Hours ».",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="Liste des habitudes et progression").set_defaults(func=cmd_list)

    p = sub.add_parser("status", help="Progression détaillée vers les 20 heures")
    p.add_argument("habit", nargs="?")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("deconstruct", help="Cible, sous-compétences, outils, checklist")
    p.add_argument("habit")
    p.set_defaults(func=cmd_deconstruct)

    p = sub.add_parser("start", help="Checklist puis minuteur puis bilan")
    p.add_argument("habit")
    p.add_argument("-m", "--minutes", type=int, help="Durée du minuteur (défaut : burst de l'habitude)")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("log", help="Enregistrer une session faite sans le minuteur")
    p.add_argument("habit")
    p.add_argument("minutes", type=int)
    p.add_argument("-q", "--quality", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--phone-free", dest="phone", action="store_true", default=None,
                   help="Le portable est resté hors de portée")
    p.add_argument("--phone-used", dest="phone", action="store_false",
                   help="Le portable a été touché")
    p.add_argument("-n", "--note")
    p.add_argument("-d", "--date", help="AAAA-MM-JJ si la session date d'un autre jour")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("history", help="Dernières sessions")
    p.add_argument("habit", nargs="?")
    p.add_argument("-l", "--last", type=int, default=15)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("plan", help="Combien pratiquer par jour pour finir à temps")
    p.add_argument("habit")
    p.add_argument("-w", "--weeks", type=int, default=4)
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("add", help="Créer une nouvelle habitude")
    p.add_argument("id", nargs="?")
    p.add_argument("--name")
    p.add_argument("--target-hours", type=float, default=20)
    p.add_argument("--burst", type=int, default=20)
    p.set_defaults(func=cmd_add)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
