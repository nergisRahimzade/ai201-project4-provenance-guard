"""
Provenance Guard — terminal demo script.

Run with the server already up:
    python -m provenance_guard.app

Then in a second terminal:
    python demo.py

For a step-by-step live demo, use the PowerShell commands printed by each section
(or copy them from the DEMO_COMMANDS block at the bottom of this file).
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:5000"

DEMO_SUBMISSIONS = [
    {
        "title": "1. Clearly AI-generated",
        "creator_id": "demo-ai",
        "text": (
            "Artificial intelligence represents a transformative paradigm shift in modern society. "
            "It is important to note that while the benefits of AI are numerous, it is equally essential "
            "to consider the ethical implications. Furthermore, stakeholders across various sectors must "
            "collaborate to ensure responsible deployment."
        ),
        "expected_label": "Clearly AI-generated",
    },
    {
        "title": "2. Clearly human-written",
        "creator_id": "demo-human",
        "text": (
            "ughhh why does my roommate ALWAYS leave dishes in the sink??? like dude we talked about "
            "this last week!!! im not your mom lol. anyway im making pasta rn and yes i washed MY bowl "
            "already so dont @ me"
        ),
        "expected_label": "Clearly human-written",
    },
    {
        "title": "3. Uncertain",
        "creator_id": "demo-uncertain",
        "text": (
            "Remote work has changed how teams collaborate. On one hand, employees enjoy flexibility; "
            "on the other, managers worry about engagement. I think the answer depends on the role - "
            "some jobs need in-person brainstorming, others do not."
        ),
        "expected_label": "Uncertain",
    },
]

APPEAL_REASONING = (
    "I wrote this myself for a blog post. The formal tone is intentional, not AI-generated."
)


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read())


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE_URL}{path}") as response:
        return json.loads(response.read())


def print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def print_json(data: dict) -> None:
    print(json.dumps(data, indent=2))


def print_powershell(label: str, command: str) -> None:
    print()
    print(f"PowerShell ({label}):")
    print(command)


def run_demo() -> int:
    uncertain_content_id: str | None = None

    print_section("Provenance Guard demo")
    print(f"API base URL: {BASE_URL}")
    print("Submitting three example texts...")

    for submission in DEMO_SUBMISSIONS:
        print_section(submission["title"])
        print(f"Expected label: {submission['expected_label']}")
        print()
        print("Text:")
        print(submission["text"])
        print()

        try:
            result = post_json(
                "/submit",
                {"text": submission["text"], "creator_id": submission["creator_id"]},
            )
        except urllib.error.URLError as exc:
            print(f"Could not reach the server at {BASE_URL}.")
            print(f"Start it first with: python -m provenance_guard.app")
            print(f"Error: {exc}")
            return 1

        print_json(result)

        if submission["creator_id"] == "demo-uncertain":
            uncertain_content_id = result["content_id"]

        print_powershell(
            "submit",
            (
                "Invoke-RestMethod -Uri http://127.0.0.1:5000/submit -Method POST "
                '-ContentType "application/json" '
                f"-Body '{{\"text\":\"{submission['text']}\",\"creator_id\":\"{submission['creator_id']}\"}}' "
                "| ConvertTo-Json"
            ),
        )

    if uncertain_content_id is None:
        print("Uncertain submission did not return a content_id; skipping appeal.")
        return 1

    print_section("4. Appeal the Uncertain classification")
    print("A creator disputes the Uncertain label and requests human review.")
    print()

    appeal_payload = {
        "content_id": uncertain_content_id,
        "creator_reasoning": APPEAL_REASONING,
    }

    try:
        appeal_result = post_json("/appeal", appeal_payload)
    except urllib.error.HTTPError as exc:
        print(f"Appeal failed ({exc.code}):")
        print(exc.read().decode())
        return 1

    print_json(appeal_result)

    print_powershell(
        "appeal",
        (
            "Invoke-RestMethod -Uri http://127.0.0.1:5000/appeal -Method POST "
            '-ContentType "application/json" '
            f"-Body '{{\"content_id\":\"{uncertain_content_id}\",\"creator_reasoning\":\"{APPEAL_REASONING}\"}}' "
            "| ConvertTo-Json"
        ),
    )

    print_section("5. Audit log")
    print("Structured JSON log of all decisions and appeals this session.")
    print()

    log_result = get_json("/log")
    print_json(log_result)

    print_powershell(
        "audit log",
        "Invoke-RestMethod -Uri http://127.0.0.1:5000/log | ConvertTo-Json -Depth 5",
    )

    print()
    print("Demo complete.")
    return 0


DEMO_COMMANDS = """
# --- Start server (terminal 1) ---
python -m provenance_guard.app

# --- Or run the full scripted demo (terminal 2) ---
python demo.py

# --- Step-by-step PowerShell commands (terminal 2) ---

# 1. Clearly AI-generated
Invoke-RestMethod -Uri http://127.0.0.1:5000/submit -Method POST -ContentType "application/json" -Body '{"text":"Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.","creator_id":"demo-ai"}' | ConvertTo-Json

# 2. Clearly human-written
Invoke-RestMethod -Uri http://127.0.0.1:5000/submit -Method POST -ContentType "application/json" -Body '{"text":"ughhh why does my roommate ALWAYS leave dishes in the sink??? like dude we talked about this last week!!! im not your mom lol. anyway im making pasta rn and yes i washed MY bowl already so dont @ me","creator_id":"demo-human"}' | ConvertTo-Json

# 3. Uncertain — copy content_id from this response for the appeal step
Invoke-RestMethod -Uri http://127.0.0.1:5000/submit -Method POST -ContentType "application/json" -Body '{"text":"Remote work has changed how teams collaborate. On one hand, employees enjoy flexibility; on the other, managers worry about engagement. I think the answer depends on the role - some jobs need in-person brainstorming, others do not.","creator_id":"demo-uncertain"}' | ConvertTo-Json

# 4. Appeal — replace CONTENT_ID_HERE with the content_id from step 3
Invoke-RestMethod -Uri http://127.0.0.1:5000/appeal -Method POST -ContentType "application/json" -Body '{"content_id":"CONTENT_ID_HERE","creator_reasoning":"I wrote this myself for a blog post. The formal tone is intentional, not AI-generated."}' | ConvertTo-Json

# 5. Audit log
Invoke-RestMethod -Uri http://127.0.0.1:5000/log | ConvertTo-Json -Depth 5
"""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--commands":
        print(DEMO_COMMANDS.strip())
        raise SystemExit(0)

    raise SystemExit(run_demo())
