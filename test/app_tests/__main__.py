import logging
import os
import unittest

from argparse import ArgumentParser
from pathlib import Path

from .services import matchFunction
from .logger import LOGGER


def main(**kwargs):
    log_level = max(1, min(kwargs.get("log_level"), 50))
    logger = LOGGER
    logger.setLevel(log_level)
    if 0 < log_level <= logging.INFO:
        logger.addHandler(logging.StreamHandler())

    if env := kwargs.get("env"):
        env_path = Path(env)
        if env_path.exists():
            env_contents = env_path.read_text(encoding="utf-8", errors="ignore")
            for line in env_contents.splitlines(keepends=False):
                parts = line.split("=", maxsplit=1)
                if len(parts) != 2:
                    continue
                key, value = parts[0], parts[1]
                if (
                    (value.startswith('"') and value.endswith('"'))
                    or value.startswith("'")
                    and value.endswith("'")
                ):
                    value = value[1:-1]
                os.environ[key] = value

    loader = unittest.TestLoader()
    runner = None

    if (fmt := kwargs.get("format")) and fmt == "tap":
        try:
            import tap  # pip install tap.py

            runner = tap.TAPTestRunner()
            runner.set_stream(True)
        except ImportError:
            pass

    if runner is None:
        runner = unittest.TextTestRunner()

    suite = unittest.TestSuite(
        [
            loader.loadTestsFromModule(matchFunction),
        ]
    )
    result = runner.run(suite)

    if not result.wasSuccessful():
        exit(1)


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        "-f",
        "--format",
        default="tap",
        choices=("default", "tap"),
    )

    parser.add_argument("-v", "--verbose", action="count", default=1)

    parser.add_argument("--env")

    result = vars(parser.parse_args())

    result["log_level"] = 70 - (10 * result["verbose"]) if result["verbose"] > 0 else 0

    return result


if __name__ == "__main__":
    main(**parse_args())
