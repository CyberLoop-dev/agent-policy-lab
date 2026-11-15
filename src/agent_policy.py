#!/usr/bin/env python3
"""Evaluate an agent tool action against a small, auditable JSON policy."""
import argparse, fnmatch, json, sys
from datetime import datetime, timezone
from pathlib import Path

def decide(policy, action, tool):
    rules = policy.get("rules", [])
    for rule in rules:
        if fnmatch.fnmatch(action, rule.get("action", "*")) and fnmatch.fnmatch(tool, rule.get("tool", "*")):
            return rule.get("effect", "deny").lower(), rule.get("reason", "matched rule")
    return policy.get("default", "deny").lower(), "default policy"

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--policy", required=True)
    p.add_argument("--action", required=True)
    p.add_argument("--tool", default="unknown")
    p.add_argument("--audit", help="Append decisions to this JSONL file")
    args = p.parse_args()
    try:
        policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
        request = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (OSError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    effect, reason = decide(policy, args.action, args.tool)
    result = {"action": args.action, "tool": args.tool, "effect": effect,
              "reason": reason, "request": request,
              "timestamp": datetime.now(timezone.utc).isoformat()}
    line = json.dumps(result, ensure_ascii=False)
    print(line)
    if args.audit:
        with open(args.audit, "a", encoding="utf-8") as stream:
            stream.write(line + "\n")
    sys.exit(0 if effect == "allow" else 3 if effect == "review" else 2)

if __name__ == "__main__":
    main()
