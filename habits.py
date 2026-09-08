#!/usr/bin/env python3
"""Traqueur d'habitudes inspiré de « The First 20 Hours » de Josh Kaufman.

Une habitude = une compétence à acquérir en 20 heures de pratique délibérée
(ou, pour les habitudes d'abstinence comme le no fap, en N jours tenus).
Le script sert à pratiquer par courtes sessions chronométrées, à enregistrer
chaque session honnêtement et à voir la progression vers l'objectif.

Usage rapide :
    python habits.py start shabbat        # checklist, minuteur, bilan
    python habits.py log shabbat 25       # enregistrer une session après coup
    python habits.py log nofap --ok       # cocher la journée d'une habitude en jours
    python habits.py status               # progression de toutes les habitudes
    python habits.py science shabbat      # ce que disent les études
    python habits.py --help               # toutes les commandes

La page web (index.html) utilise exactement le même format de données.
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

# Une session compte comme « vraiment réussie » si la contrainte de l'habitude
# a été respectée (clean) ET que la qualité ressentie est d'au moins 4 sur 5.
# Pour une habitude en jours (no fap), seule la contrainte compte.
REAL_QUALITY_MIN = 4

DEFAULT_QUALITY_LABELS = {
    1: "J'ai craqué ou abandonné",
    2: "Difficile, surtout attendu que ça passe",
    3: "Moitié présent, moitié ailleurs",
    4: "Bien, quelques dérives vite rattrapées",
    5: "Pleinement dans l'activité",
}
DEFAULT_CLEAN_QUESTION = "La contrainte de l'habitude a été respectée tout le long ?"

WEEKDAYS = ["L", "M", "M", "J", "V", "S", "D"]


# --------------------------------------------------------------------------- #
# Stockage
# --------------------------------------------------------------------------- #
def load_config() -> dict:
    if not HABITS_FILE.exists():
        return {"habits": [], "method_science": []}
    with open(HABITS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_habits() -> list[dict]:
    return load_config().get("habits", [])


def save_habits(habits: list[dict]) -> None:
    config = load_config()
    config["habits"] = habits
    with open(HABITS_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
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


def is_days(habit: dict) -> bool:
    return habit.get("unit", "minutes") == "days"


def quality_labels(habit: dict) -> dict[int, str]:
    custom = habit.get("quality_labels")
    if custom:
        return {int(k): v for k, v in custom.items()}
    return DEFAULT_QUALITY_LABELS


def add_session(
    habit_id: str,
    minutes: int,
    quality: int,
    clean: bool,
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
        "clean": bool(clean),
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
def is_real(session: dict, habit: dict | None = None) -> bool:
    if habit is not None and is_days(habit):
        return bool(session["clean"])
    return bool(session["clean"]) and session["quality"] >= REAL_QUALITY_MIN


def compute_stats(habit: dict, sessions: list[dict], today: date | None = None) -> dict:
    today = today or date.today()
    days_mode = is_days(habit)
    mine = [s for s in sessions if s["habit"] == habit["id"]]
    real = [s for s in mine if is_real(s, habit)]

    if days_mode:
        # Un jour compte une seule fois, et compte comme tenu si toutes ses
        # entrées sont « clean ».
        by_day: dict[date, bool] = {}
        for s in mine:
            d = date.fromisoformat(s["date"])
            by_day[d] = by_day.get(d, True) and bool(s["clean"])
        kept_days = {d for d, ok in by_day.items() if ok}
        total = len(kept_days)
        target = int(habit.get("target_days", 90))
        streak_days = kept_days
    else:
        total = sum(s["minutes"] for s in mine)
        target = int(habit.get("target_hours", 20) * 60)
        streak_days = {date.fromisoformat(s["date"]) for s in mine}

    streak = 0
    cursor = today if today in streak_days else today - timedelta(days=1)
    while cursor in streak_days:
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
        elif days_mode:
            week_grid.append("●" if all(s["clean"] for s in day_sessions) else "○")
        elif any(is_real(s, habit) for s in day_sessions):
            week_grid.append("●")
        else:
            week_grid.append("○")

    window_start = today - timedelta(days=13)
    if days_mode:
        recent_total = len({d for d in streak_days if d >= window_start})
    else:
        recent_total = sum(s["minutes"] for s in mine if date.fromisoformat(s["date"]) >= window_start)
    pace_per_day = recent_total / 14
    remaining = max(target - total, 0)
    if remaining == 0:
        eta = today
    elif pace_per_day > 0:
        eta = today + timedelta(days=round(remaining / pace_per_day))
    else:
        eta = None

    return {
        "unit": "days" if days_mode else "minutes",
        "sessions": len(mine),
        "real_sessions": len(real),
        "total": total,
        "target": target,
        "remaining": remaining,
        "percent": min(100.0, 100.0 * total / target) if target else 0.0,
        "streak": streak,
        "week_sessions": len(week),
        "week_total": len({s["date"] for s in week if s["clean"]}) if days_mode
        else sum(s["minutes"] for s in week),
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


def fmt_amount(value: int, unit: str) -> str:
    if unit == "days":
        return f"{value} jour{'s' if value != 1 else ''}"
    return fmt_hours(value)


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
def real_label(habit: dict) -> str:
    return "jours tenus" if is_days(habit) else "« vraiment réussies »"


def print_status(habit: dict, sessions: list[dict]) -> None:
    st = compute_stats(habit, sessions)
    unit = st["unit"]
    print(f"\n{habit['name']}  ({habit['id']})")
    print(f"{progress_bar(st['percent'])} {fmt_amount(st['total'], unit)} / "
          f"{fmt_amount(st['target'], unit)}  ({st['percent']:.0f} %)")
    if st["sessions"] == 0:
        verb = "log" if is_days(habit) else "start"
        print(f"Aucune entrée pour l'instant. Lance : python habits.py {verb} {habit['id']}")
        return
    grid = " ".join(f"{d}{m}" for d, m in zip(WEEKDAYS, st["week_grid"]))
    if is_days(habit):
        print(f"Journées cochées : {st['sessions']}   tenues : {st['real_sessions']}")
        print(f"Série : {st['streak']} jour(s) tenus d'affilée   Cette semaine : "
              f"{st['week_total']} jour(s) tenus   {grid}")
    else:
        real_pct = 100.0 * st["real_sessions"] / st["sessions"]
        print(f"Sessions : {st['sessions']}   dont {real_label(habit)} : "
              f"{st['real_sessions']} ({real_pct:.0f} %)")
        print(f"Série : {st['streak']} jour(s)   Cette semaine : {st['week_sessions']} session(s), "
              f"{fmt_hours(st['week_total'])}   {grid}")
    if st["remaining"] == 0:
        print("Objectif atteint. Fixe un nouveau niveau cible dans habits.json.")
    elif st["eta"]:
        pace = (f"{st['pace_per_day'] * 7:.1f} jours tenus/semaine" if is_days(habit)
                else f"{st['pace_per_day']:.0f} min/jour")
        print(f"Rythme sur 14 jours : {pace} → objectif atteint vers le {fmt_date(st['eta'])}")
    else:
        print("Rythme sur 14 jours : rien → pas de projection possible, reprends une session.")
    extra = "" if is_days(habit) else f"   Plus longue session : {fmt_hours(st['longest'])}"
    print(f"Qualité moyenne : {st['avg_quality']:.1f}/5{extra}")


def print_session_feedback(habit: dict, session: dict) -> None:
    st = compute_stats(habit, load_sessions())
    unit = st["unit"]
    if is_days(habit):
        tag = "journée tenue ✔" if session["clean"] else "journée notée comme non tenue"
        print(f"\nEnregistré : {session['date']}, qualité {session['quality']}/5, {tag}.")
    else:
        tag = "vraiment réussie ✔" if is_real(session, habit) else "comptée, mais pas « vraiment réussie »"
        print(f"\nEnregistré : {session['minutes']} min, qualité {session['quality']}/5, {tag}.")
    print(f"Total : {fmt_amount(st['total'], unit)} sur {fmt_amount(st['target'], unit)} "
          f"({st['percent']:.0f} %) · {st['real_sessions']} {real_label(habit)} sur "
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


def ask_quality(habit: dict) -> int:
    print("\nHonnêtement, c'était :")
    for k, label in quality_labels(habit).items():
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
              f"{fmt_amount(st['total'], st['unit']):>8} / {fmt_amount(st['target'], st['unit']):<8}"
              f"  {st['real_sessions']}/{st['sessions']} {real_label(habit)}")


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
    if is_days(habit):
        print(f"\nObjectif : {habit.get('target_days', 90)} jours tenus, cochés un par un.")
    else:
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
    print(f"\nCe que disent les études : python habits.py science {habit['id']}\n")


def cmd_science(args: argparse.Namespace) -> None:
    if args.habit:
        habit = get_habit(args.habit)
        entries = habit.get("science", [])
        title = habit["name"]
    else:
        entries = load_config().get("method_science", [])
        title = "La méthode (pratique délibérée, espacement, formation des habitudes)"
    print(f"\n{title}\n")
    if not entries:
        print("Aucune référence enregistrée pour cette habitude.")
        return
    for i, entry in enumerate(entries, 1):
        print(f"{i}. {entry['finding']}")
        print(f"   Source : {entry['source']}\n")


def cmd_start(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    if is_days(habit):
        print(f"« {habit['id']} » se suit en jours : coche la journée avec "
              f"python habits.py log {habit['id']} --ok (ou --ko).")
        return
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
    quality = ask_quality(habit)
    clean = ask_yes(habit.get("clean_question", DEFAULT_CLEAN_QUESTION))
    note = input("Une note (facultatif) : ")
    session = add_session(habit["id"], elapsed, quality, clean, note)
    print_session_feedback(habit, session)


def cmd_log(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    if is_days(habit):
        minutes = 0
    elif args.minutes is None:
        sys.exit(f"Indique la durée en minutes : python habits.py log {habit['id']} 25")
    else:
        minutes = args.minutes
    clean = args.clean
    if clean is None:
        clean = ask_yes(habit.get("clean_question", DEFAULT_CLEAN_QUESTION))
    if args.quality:
        quality = args.quality
    elif is_days(habit) and not clean:
        quality = 1
    else:
        quality = ask_quality(habit)
    when = datetime.now()
    if args.date:
        when = datetime.combine(date.fromisoformat(args.date), when.time())
    session = add_session(habit["id"], minutes, quality, clean, args.note or "", when)
    print_session_feedback(habit, session)


def cmd_history(args: argparse.Namespace) -> None:
    sessions = load_sessions()
    habits = {h["id"]: h for h in load_habits()}
    if args.habit:
        get_habit(args.habit)
        sessions = [s for s in sessions if s["habit"] == args.habit]
    sessions = sessions[-args.last:]
    if not sessions:
        print("Aucune session enregistrée.")
        return
    print(f"{'date':<10} {'heure':<5} {'habitude':<11} {'min':>4} {'qual':>4} {'ok':>4}  note")
    for s in sessions:
        habit = habits.get(s["habit"])
        mark = "oui" if is_real(s, habit) else "non"
        print(f"{s['date']:<10} {s['time']:<5} {s['habit']:<11} {s['minutes']:>4} "
              f"{s['quality']:>4} {mark:>4}  {s['note']}")


def cmd_plan(args: argparse.Namespace) -> None:
    habit = get_habit(args.habit)
    st = compute_stats(habit, load_sessions())
    remaining = st["remaining"]
    days = args.weeks * 7
    print(f"\n{habit['name']}")
    if is_days(habit):
        print(f"Il reste {remaining} jour(s) tenus pour atteindre {st['target']} jours.")
        print(f"Au mieux, sans aucun écart, c'est le {fmt_date(date.today() + timedelta(days=remaining))}.")
    else:
        per_day = remaining / days
        burst = habit.get("burst_minutes", 20)
        print(f"Il reste {fmt_hours(remaining)} pour atteindre {fmt_hours(st['target'])}.")
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
        "unit": "days" if args.days else "minutes",
        "why": input("Pourquoi tu y tiens vraiment : ").strip(),
        "target_performance": input("À quoi ressemble « assez bon » pour toi (observable, concret) : ").strip(),
        "clean_question": input("Question oui/non posée après chaque session (la contrainte à respecter) : ").strip()
        or DEFAULT_CLEAN_QUESTION,
        "subskills": [s.strip() for s in input("Sous-compétences (séparées par ;) : ").split(";") if s.strip()],
        "tools": [s.strip() for s in input("Outils nécessaires (séparés par ;) : ").split(";") if s.strip()],
        "checklist": [s.strip() for s in input("Checklist avant session (séparée par ;) : ").split(";") if s.strip()],
        "science": [],
    }
    if args.days:
        habit["target_days"] = args.days
    else:
        habit["target_hours"] = args.target_hours
        habit["burst_minutes"] = args.burst
    habits.append(habit)
    save_habits(habits)
    verb = "log" if args.days else "start"
    print(f"\nHabitude « {habit_id} » créée. Première session : python habits.py {verb} {habit_id}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="habits.py",
        description="Traqueur d'habitudes façon « The First 20 Hours ».",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="Liste des habitudes et progression").set_defaults(func=cmd_list)

    p = sub.add_parser("status", help="Progression détaillée")
    p.add_argument("habit", nargs="?")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("deconstruct", help="Cible, sous-compétences, outils, checklist")
    p.add_argument("habit")
    p.set_defaults(func=cmd_deconstruct)

    p = sub.add_parser("science", help="Études sur l'habitude (sans argument : sur la méthode)")
    p.add_argument("habit", nargs="?")
    p.set_defaults(func=cmd_science)

    p = sub.add_parser("start", help="Checklist puis minuteur puis bilan")
    p.add_argument("habit")
    p.add_argument("-m", "--minutes", type=int, help="Durée du minuteur (défaut : burst de l'habitude)")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("log", help="Enregistrer une session (ou cocher une journée)")
    p.add_argument("habit")
    p.add_argument("minutes", type=int, nargs="?", help="Durée en minutes (inutile pour une habitude en jours)")
    p.add_argument("-q", "--quality", type=int, choices=[1, 2, 3, 4, 5])
    p.add_argument("--ok", dest="clean", action="store_true", default=None,
                   help="Contrainte respectée (portable loin, journée tenue…)")
    p.add_argument("--ko", dest="clean", action="store_false",
                   help="Contrainte non respectée")
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
    p.add_argument("--days", type=int, help="Habitude suivie en jours tenus (ex: --days 90)")
    p.set_defaults(func=cmd_add)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
