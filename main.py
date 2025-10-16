#!/usr/bin/env python3
# Daily exam countdown email: nearest-exam focus + ALL upcoming exams
# Plain-text + HTML (bolded time remaining), 50 "why" quotes, and short closers.

from __future__ import annotations
import os, ssl, smtplib, argparse, random
from email.message import EmailMessage
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ====== CONFIG YOU EDIT ======
LOCAL_TZ = ZoneInfo("America/New_York")

EXAMS = [
    {"name": "CS 251 Midterm 2", "when": "2025-11-19 20:00"},
    {"name": "CS 251 Finals",    "when": "2025-12-15 08:00"},
    {"name": "CS 250 Midterm 2", "when": "2025-10-28 11:30"},
    {"name": "CS 250 Finals",    "when": "2025-12-15 15:30"},
    {"name": "MA 351 Midterm 2", "when": "2025-11-06 16:30"},
    {"name": "MA 351 Finals",    "when": "2025-12-20 10:30"},
]

TO_EMAILS = ["alexyan2309@gmail.com"]

FROM_EMAIL = os.getenv("STUDY_EMAIL")                  # your Gmail
FROM_APP_PASSWORD = os.getenv("STUDY_EMAIL_PASSWORD")  # 16-char Gmail app password

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT_SSL = 465
# ====== END CONFIG ======


# ---------- helpers ----------
def parse_local(dt_str: str) -> datetime:
    dt_naive = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    return dt_naive.replace(tzinfo=LOCAL_TZ)

def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20: s = "th"
    else: s = {1:"st",2:"nd",3:"rd"}.get(n % 10,"th")
    return f"{n}{s}"

def format_delta(delta: timedelta) -> str:
    secs = int(delta.total_seconds())
    if secs <= 0: return "0 days"
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    parts = []
    if d: parts.append(f"{d} day{'s' if d!=1 else ''}")
    if h: parts.append(f"{h} hour{'s' if h!=1 else ''}")
    if d == 0 and m: parts.append(f"{m} min")
    return ", ".join(parts)

def upcoming_exams(now: datetime):
    ups = []
    for e in EXAMS:
        try:
            dt = parse_local(e["when"])
            if dt >= now - timedelta(minutes=1):
                ups.append((dt, e["name"]))
        except Exception:
            continue
    ups.sort(key=lambda x: x[0])
    return ups

def find_next_exam(now: datetime):
    ups = upcoming_exams(now)
    return None if not ups else {"name": ups[0][1], "when": ups[0][0].strftime("%Y-%m-%d %H:%M")}

def days_out_for(exam_dt: datetime, now: datetime) -> int:
    return max(0, (exam_dt.date() - now.date()).days)


# ---------- phase-aware actions ----------
PHASES_ACTIONS = [
    (45, 10**6, [
        "Long game: 60–90 min focused block. Map weightings; prioritize high-yield.",
        "Make 5 flashcards + one mini recall lap. Habit > intensity.",
        "Outline two weak topics; schedule short blocks for each.",
        "Re-derive key formulas from memory; fill gaps immediately.",
        "One tough section with a timer. Log errors in a ‘trap list’.",
    ]),
    (30, 44, [
        "Do 3 mixed problems cold; write corrected solutions after.",
        "Teach one concept out loud in 2 minutes—no notes.",
        "Build a one-page ‘mini cheatsheet’ of must-knows.",
        "Interleave topics A/B/A to boost retention.",
        "Two deep blocks this week. Defend them like appointments.",
    ]),
    (15, 29, [
        "Daily 25-min timed drills. Grade ruthlessly; update trap list.",
        "Write 3 must-know Qs per lecture and answer from memory.",
        "Target weak zones first; stop polishing what’s already smooth.",
        "Definitions → examples → edge cases for high-yield sections.",
        "Every miss becomes a flashcard + fixed solution.",
    ]),
    (7, 14, [
        "Run one full mock under exam timing. Immediate post-mortem.",
        "Stress inoculation: simulate constraints; practice clarity.",
        "Summarize each chapter in 5 bullets, ultra-concise.",
        "Derive core formulas twice this week without peeking.",
        "Refine workflows (notation, layout) for clean partial credit.",
    ]),
    (3, 6, [
        "Pick 2 weakest subtopics, 30 minutes each, timed drills.",
        "Half-mock focused on historically hard sections.",
        "High-yield review lap: definitions → examples → edge cases.",
        "Drill your trap list; fewer new topics, more refinement.",
        "Protect sleep/exercise—performance depends on recovery.",
    ]),
    (1, 2, [
        "Polish, don’t push: light recall + a short confidence set.",
        "Pack logistics now; de-risk the morning. Hydrate.",
        "Skim trap list; visualize correct fixes.",
        "Spaced retrieval sprints > late-night cramming.",
        "Trust your reps. Early lights-out beats one more page.",
    ]),
    (0, 0, [
        "Exam day: breathe, read carefully, front-load points, mark returns.",
        "If stuck, pivot to a sure win and come back—keep moving.",
        "Show work cleanly; partial credit loves clarity.",
        "Slow is smooth, smooth is fast. One line at a time.",
        "You’ve built the engine—now drive with poise.",
    ]),
]

def pick_action(days_out: int, exam_name: str, today_key: str) -> str:
    for lo, hi, msgs in PHASES_ACTIONS:
        if lo <= days_out <= hi:
            random.seed(f"ACTION:{today_key}:{exam_name}:{days_out}")
            return msgs[random.randrange(len(msgs))]
    random.seed(f"ACTION:{today_key}:fallback")
    return "Short, focused session: review errors, then one clean run-through."


# ---------- ONE BIG “WHY” QUOTES ARRAY (50 total) ----------
WHY_QUOTES = [
    "Discipline is remembering what you want most, not what you want now.",
    "Every quiet hour you study plants seeds your future self will harvest.",
    "Excellence is not a mood—it’s a habit that starts with one decision.",
    "You don’t rise to the occasion; you fall to the level of your preparation.",
    "Small efforts done daily become unshakable confidence later.",
    "The best students aren’t the smartest—they’re the most consistent.",
    "Don’t study to pass. Study to understand—and you’ll never forget.",
    "Start now so your future self never has to panic later.",
    "You’re building not just knowledge, but reliability in yourself.",
    "A slow start beats a fast regret.",
    "Studying is a conversation with your future dreams.",
    "The future favors those who start when no one’s watching.",
    "The grind is where greatness grows quietly.",
    "Repetition is the mother of mastery.",
    "Each time you practice recall, you’re building recall power.",
    "Clarity doesn’t come from cramming—it comes from re-teaching yourself.",
    "A mistake made today is one less you’ll make on the exam.",
    "Keep your pace—progress compounds when you show up every day.",
    "Your only real competition is yesterday’s version of you.",
    "Consistency turns average talent into unstoppable skill.",
    "You’ll never regret studying too early; only too late.",
    "Momentum beats motivation—keep moving.",
    "The gap between effort and results is filled with patience.",
    "Today’s discipline builds tomorrow’s freedom.",
    "Pressure is a privilege—it means you care about what you’re doing.",
    "Hard is not bad; hard is how you grow.",
    "Failures in practice are rehearsals for success.",
    "Every time you fix a mistake, you’re becoming bulletproof.",
    "Push through discomfort—it’s proof of progress.",
    "Mastery lives just past the point of frustration.",
    "Don’t avoid what confuses you; chase it until it makes sense.",
    "Study until effort becomes instinct.",
    "You are your own coach—be firm, but fair.",
    "The challenge today is the confidence tomorrow.",
    "No one gets stronger lifting what’s easy.",
    "Sweat in private, shine in public.",
    "Train like it’s the real thing so the real thing feels like training.",
    "Simulate pressure now so calm comes naturally later.",
    "Nerves mean you care—channel them into precision.",
    "You don’t need luck when you’ve rehearsed every outcome.",
    "The test is not the enemy—it’s the stage for your preparation.",
    "Preparation is confidence made visible.",
    "Exams don’t test intelligence—they reveal consistency.",
    "Refinement is the final frontier of mastery.",
    "Sharp tools are made by friction—embrace the grind.",
    "Excellence is deliberate. You’ve built this.",
    "You’re not cramming; you’re tuning your instrument.",
    "Trust the hours that no one saw.",
    "Preparation replaces fear with clarity.",
    "Calm is your competitive advantage.",
]

def pick_why_quote(today_key: str, exam_name: str) -> str:
    random.seed(f"WHY:{today_key}:{exam_name}")
    return WHY_QUOTES[random.randrange(len(WHY_QUOTES))]


# ---------- SHORT “CLOSER” QUOTES (ending boosts) ----------
CLOSERS = [
    "You’ve got this.",
    "Keep going—you’re closer than you think.",
    "Proud of the work you’re doing.",
    "One page at a time.",
    "Show up for future you.",
    "Steady beats flashy.",
    "Trust your prep.",
    "Eyes on the next small step.",
    "Strength is built here.",
    "Win today’s 25 minutes.",
    "You’re building momentum.",
    "Let’s get it.",
]

def pick_closer(today_key: str) -> str:
    random.seed(f"CLOSER:{today_key}")
    return CLOSERS[random.randrange(len(CLOSERS))]


# ---------- email building (plain text + HTML with bold time) ----------
def build_email(now: datetime, next_exam: dict | None):
    date_str = now.strftime("%A, %B ") + ordinal(now.day) + now.strftime(", %Y")

    # ----- Plain text -----
    text_lines = [f"Hello Alex! It’s {date_str}.", ""]
    ups = upcoming_exams(now)
    if ups:
        text_lines.append("All upcoming exams:")
        for dt, name in ups:
            delta = dt - now
            days_out = days_out_for(dt, now)
            when_str = f"{dt.strftime('%A, %B ')}{ordinal(dt.day)}{dt.strftime(', %Y at %-I:%M %p')}"
            text_lines.append(f"- {name}")
            text_lines.append(f"  When: {when_str}")
            text_lines.append(f"  Time left: {format_delta(delta)}  ({days_out} day{'s' if days_out!=1 else ''})")
            text_lines.append("")  # blank line
    else:
        text_lines += ["No upcoming exams found. Add them in the EXAMS list.", ""]

    text_lines.append("—")

    # Subject + nearest exam block
    if not next_exam:
        subject = "Daily Study Check-in: No upcoming exams listed"
        days_out_nearest = 30
        chosen_exam_name = "general"
        text_lines += ["", "Why this matters:", pick_why_quote(now.strftime("%Y-%m-%d"), chosen_exam_name)]
    else:
        exam_dt = parse_local(next_exam["when"])
        delta = exam_dt - now
        days_out_nearest = days_out_for(exam_dt, now)
        chosen_exam_name = next_exam["name"]
        when_str_nearest = f"{exam_dt.strftime('%A, %B ')}{ordinal(exam_dt.day)}{exam_dt.strftime(', %Y at %-I:%M %p')}"
        if delta.total_seconds() <= 0:
            subject = f"Exam Day: {chosen_exam_name} is today"
            text_lines += ["",
                           f"Next exam: {chosen_exam_name}",
                           f"When: {when_str_nearest}",
                           f"Time remaining: 0 days"]
        else:
            subject = f"Countdown: {chosen_exam_name} in {format_delta(delta)}"
            text_lines += ["",
                           f"Next exam: {chosen_exam_name}",
                           f"When: {when_str_nearest}",
                           f"Time remaining: {format_delta(delta)} ({days_out_nearest} day{'s' if days_out_nearest!=1 else ''})"]
        text_lines += ["",
                       "Why this matters:",
                       pick_why_quote(now.strftime("%Y-%m-%d"), chosen_exam_name)]

    text_lines += ["",
                   "Today’s focus:",
                   pick_action(days_out_nearest, chosen_exam_name, now.strftime("%Y-%m-%d")),
                   "",
                   "Tiny first step: 25 focused minutes. Then a 3-minute break. 💪",
                   pick_closer(now.strftime("%Y-%m-%d"))]
    body_text = "\n".join(text_lines)

    # ----- HTML (bold time) -----
    html = []
    html.append(f"""<html><body style="font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height:1.45; font-size:15px; color:#111;">
<p>Hey Alex! It’s {date_str}.</p>
""")

    if ups:
        html.append("<h3 style='margin:10px 0 6px;'>All upcoming exams:</h3><ul style='padding-left:18px; margin-top:6px;'>")
        for dt, name in ups:
            delta = dt - now
            days_out = days_out_for(dt, now)
            when_str = f"{dt.strftime('%A, %B ')}{ordinal(dt.day)}{dt.strftime(', %Y at %-I:%M %p')}"
            html.append(f"""<li style="margin-bottom:10px;">
  <div><strong>{name}</strong></div>
  <div>When: {when_str}</div>
  <div>Time left: <strong>{format_delta(delta)}</strong> ({days_out} day{'s' if days_out!=1 else ''})</div>
</li>""")
        html.append("</ul>")
    else:
        html.append("<p>No upcoming exams found. Add them in the EXAMS list.</p>")

    html.append("<hr style='border:none;height:1px;background:#ddd;margin:12px 0;'/>")

    if not next_exam:
        html.append("<p><em>Daily Study Check-in: No upcoming exams listed</em></p>")
        days_out_nearest = 30
        chosen_exam_name = "general"
    else:
        exam_dt = parse_local(next_exam["when"])
        delta = exam_dt - now
        days_out_nearest = days_out_for(exam_dt, now)
        chosen_exam_name = next_exam["name"]
        when_str_nearest = f"{exam_dt.strftime('%A, %B ')}{ordinal(exam_dt.day)}{exam_dt.strftime(', %Y at %-I:%M %p')}"
        html.append(f"<p><strong>Next exam:</strong> {chosen_exam_name}<br/>When: {when_str_nearest}</p>")
        if delta.total_seconds() <= 0:
            html.append("<p><strong>Time remaining:</strong> <strong>0 days</strong></p>")
        else:
            html.append(f"<p><strong>Time remaining:</strong> <strong>{format_delta(delta)}</strong> ({days_out_nearest} day{'s' if days_out_nearest!=1 else ''})</p>")

    html.append(f"""
<p><strong>Why this matters:</strong><br/>{pick_why_quote(now.strftime("%Y-%m-%d"), chosen_exam_name)}</p>
<p><strong>Today’s focus:</strong><br/>{pick_action(days_out_nearest, chosen_exam_name, now.strftime("%Y-%m-%d"))}</p>
<p>Tiny first step: 25 focused minutes. Then a 3-minute break. 💪<br/>{pick_closer(now.strftime("%Y-%m-%d"))}</p>
</body></html>""")
    body_html = "".join(html)

    return subject, body_text, body_html


# ---------- sending (multipart: text + HTML) ----------
def send_email(subject: str, body_text: str, body_html: str, to_emails: list[str]):
    if not FROM_EMAIL or not FROM_APP_PASSWORD:
        raise RuntimeError("Missing STUDY_EMAIL or STUDY_EMAIL_PASSWORD environment variables.")
    if not to_emails:
        raise RuntimeError("TO_EMAILS is empty—add at least one recipient.")

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject

    # Plain-text fallback
    msg.set_content(body_text)

    # HTML version (bolded time)
    msg.add_alternative(body_html, subtype="html")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL, context=context) as server:
        server.login(FROM_EMAIL, FROM_APP_PASSWORD)
        server.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description="Daily countdown + all exams + quotes + closers (HTML bold time)")
    parser.add_argument("--send", action="store_true", help="Actually send the email")
    parser.add_argument("--dry-run", action="store_true", help="Print the email instead of sending")
    args = parser.parse_args()

    now = datetime.now(LOCAL_TZ)
    nxt = find_next_exam(now)
    subject, body_text, body_html = build_email(now, nxt)

    if args.dry_run or not args.send:
        print("=" * 80); print("SUBJECT:", subject); print("-" * 80)
        print(body_text); print("=" * 80)
        if not args.send:
            print("(Not sending. Use --send to email.)")
        return

    send_email(subject, body_text, body_html, TO_EMAILS)
    print("Email sent.")


if __name__ == "__main__":
    main()
