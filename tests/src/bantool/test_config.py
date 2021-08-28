#!/usr/bin/env python3

import unittest
import tempfile
from textwrap import dedent

from bantool import config


class ThisTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempfile = tempfile.NamedTemporaryFile('w+')

        self.mock_config = dedent(
            """
            {
                "twitch_channels": ["foobar"],
                "account_name": "barbaz",
                "Number_of_browser_windows": 1,
                "Firefox_profile": "firefox",
                "Block": true,
                "Unblock": true,
                "Ban": true,
                "Unban": true,
                "Greeting Emote": ":wave:",
                "Chunk size": 1000,
                "namelist": "names.txt"
            }
            """
        ).strip()

        self.example_config = config.ConfigNT(
            twitch_channels=["foobar"],
            account_name="barbaz",
            number_of_browser_windows=1,
            firefox_profile="firefox",
            block=True,
            unblock=True,
            ban=True,
            unban=True,
            greeting_emote=":wave:",
            chunk_size=1000,
            namelist="names.txt",
        )

        self.tempfile.write(self.mock_config)
        self.tempfile.seek(0)

    def tearDown(self) -> None:
        self.tempfile.close()

    def test_load_config_from_file(self):
        found = config.load_config_to_dict(self.tempfile.name)
        self.assertEqual(found, self.example_config._asdict())
