import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m jobdigest",
        description="Daily ranked job digest",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    onboard = sub.add_parser("onboard", help="Build or refine your profile.json")
    onboard.add_argument(
        "--rebuild", action="store_true", help="Discard and regenerate"
    )
    onboard.add_argument(
        "--refine", action="store_true", help="Merge new draft into existing"
    )

    sub.add_parser("run", help="Run the daily pipeline")

    args = parser.parse_args()

    if args.command == "run":
        _run()
    elif args.command == "onboard":
        _onboard(args)
    else:
        parser.print_help()
        sys.exit(1)


def _run() -> None:
    if not Path("profile.json").exists():
        print("No profile found. Run `python -m jobdigest onboard` to get started.")
        sys.exit(1)

    from jobdigest.config import load_config, load_profile
    from jobdigest.runner import run

    config = load_config()
    profile = load_profile()
    out_path = run(config, profile)
    print(f"Digest written to {out_path}")


def _onboard(args: argparse.Namespace) -> None:
    # Interactive flow implemented in Issue #20.
    print("jobdigest onboard: not yet implemented.")
