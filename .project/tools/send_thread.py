"""Allocate a thread number with threads.py new and fill BOTH copies at once (front matter kept, asks/answers set).

usage: python send_thread.py --project P --to PEER --date D --body FILE [--asks A,B] [--answers C,D]
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--project", required=True)
ap.add_argument("--to", required=True)
ap.add_argument("--date", required=True)
ap.add_argument("--body", required=True)
ap.add_argument("--asks", default="")
ap.add_argument("--answers", default="")
ap.add_argument("--parent", default=r"E:\CodeReview")
a = ap.parse_args()

mine_dir = Path(a.parent) / a.project / "design" / "threads" / a.to
theirs_dir = Path(a.parent) / a.to / "design" / "threads" / a.project
for d in (mine_dir, theirs_dir):
    if not d.is_dir():
        sys.exit(f"no thread folder {d}")
before_m, before_t = set(os.listdir(mine_dir)), set(os.listdir(theirs_dir))

threads = Path(os.environ["USERPROFILE"]) / ".claude" / "skills" / "project" / "assets" / "threads.py"
r = subprocess.run([sys.executable, str(threads), "new", "--project", a.project, "--to", a.to, "--date", a.date],
                   capture_output=True, text=True)
print(r.stdout.strip())
if r.returncode != 0:
    sys.exit(f"threads.py new failed: {r.stderr}")

new_m = sorted(set(os.listdir(mine_dir)) - before_m)
new_t = sorted(set(os.listdir(theirs_dir)) - before_t)
if len(new_m) != 1 or len(new_t) != 1 or new_m != new_t:
    sys.exit(f"unexpected new files: mine={new_m} theirs={new_t}")
name = new_m[0]
mine, theirs = mine_dir / name, theirs_dir / name

raw = mine.read_bytes().decode("utf-8")
nl = "\r\n" if "\r\n" in raw else "\n"
text = raw.replace("\r\n", "\n")
if not text.startswith("---\n"):
    sys.exit("template has no front matter")
end = text.index("\n---\n", 4)
front = text[4:end].split("\n")


def listed(s):
    items = [x.strip() for x in s.split(",") if x.strip()]
    return "[" + ", ".join(items) + "]"


out = []
for line in front:
    if line.startswith("asks:"):
        line = "asks: " + listed(a.asks)
    elif line.startswith("answers:"):
        line = "answers: " + listed(a.answers)
    out.append(line)
number = name.split("_")[0]
body = Path(a.body).read_bytes().decode("utf-8").replace("\r\n", "\n")
first, rest = body.split("\n", 1)
if first.startswith("# "):
    # The body's title carries the number threads.py allocated, whatever the draft said.
    first = "# " + number + " " + first[2:].split(" ", 1)[1] if first[2:].split(" ", 1)[0].isdigit() else first
body = first + "\n" + rest
doc = "---\n" + "\n".join(out) + "\n---\n\n" + body.rstrip("\n") + "\n"
data = doc.replace("\n", nl).encode("utf-8")
mine.write_bytes(data)
theirs.write_bytes(data)
print(f"filled {mine}")
print(f"filled {theirs}")
print("identical:", mine.read_bytes() == theirs.read_bytes())
