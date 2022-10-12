import logging
import unittest

from argparse import ArgumentParser

import app_tests.services
import app_tests.logger


def main(**kwargs):
    log_level = max(1, min(kwargs.get("log_level"), 50))
    logger = app_tests.logger.LOGGER
    logger.setLevel(log_level)
    if 0 < log_level <= logging.INFO:
        logger.addHandler(logging.StreamHandler())

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

    suite = loader.loadTestsFromModule(app_tests.services)
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

    result = vars(parser.parse_args())

    result["log_level"] = 70 - (10 * result["verbose"]) if result["verbose"] > 0 else 0

    return result


if __name__ == "__main__":
    main(**parse_args())
