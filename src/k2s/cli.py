import sys
import argparse

from k2s.bootstrap import from_url
from k2s.exceptions import CLIError


class CLI:
    def __init__(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("command")
        args = parser.parse_args(sys.argv[1:2])

        if not hasattr(self, args.command):
            sys.exit(f"Unrecognized command {args.command!r}")
        else:
            cmd = getattr(self, args.command)

            try:
                cmd()
            except CLIError as e:
                sys.exit(e)

            sys.exit(0)

    def get(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("url")
        parser.add_argument("--no-jupyter", action="store_true")
        args = parser.parse_args(sys.argv[2:])
        from_url(args.url, open_jupyter=not args.no_jupyter)
