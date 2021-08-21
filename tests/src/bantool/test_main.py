#!/usr/bin/env python3

import unittest

from bantool import main


class ThisTeseCase(unittest.TestCase):
    pass


class Test_ArgumentParser(ThisTeseCase):
    def setUp(self) -> None:
        super().setUp()

        self.args = [
            "--config",
            "foobar.json",
        ]

    def test_mutex_group(self):
        args = ["--config", "foobar.json"]
        main.parse_args(args)
