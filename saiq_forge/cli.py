import argparse
import json
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(prog="saiq_forge")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--config", required=True)

    args = parser.parse_args(argv)

    if args.command == "run":
        from saiq_forge.pipeline.orchestrator import run
        alerts = run(args.config)
        json.dump(alerts, sys.stdout, indent=2)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
