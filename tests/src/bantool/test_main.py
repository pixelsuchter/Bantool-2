#!/usr/bin/env python3

import unittest
import tempfile
import json

from bantool import main


class ThisTeseCase(unittest.TestCase):
    pass


class Test_ArgumentParser(ThisTeseCase):
    def setUp(self) -> None:
        super().setUp()

        self.temp_config = tempfile.NamedTemporaryFile("w+")
        json.dump({}, self.temp_config)
        self.temp_config.seek(0)

        self.args = [
            "--config",
            self.temp_config.name,
        ]
    def tearDown(self) -> None:
        self.temp_config.close()

    def test_mutex_group(self):
        main.parse_args(self.args)
