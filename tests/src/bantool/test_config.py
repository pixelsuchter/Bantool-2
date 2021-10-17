#!/usr/bin/env python3

import unittest
import os.path
from unittest import mock
from tempfile import NamedTemporaryFile, TemporaryDirectory

from bantool import config as MOD

HERE = os.path.dirname(__file__)

class ThisTestCase(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()


class Test_download_banlist(ThisTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.faux_dir = TemporaryDirectory()
        self.requests_mock = mock.patch(
            'bantool.config.requests', spec_set=MOD.requests
        )
        self.patcher = self.requests_mock.start()

        self.mock_response_content = b"banlist"
        self.mock_response = mock.MagicMock(
            MOD.requests.Response, spec_set=MOD.requests.Response
        )
        type(self.mock_response).content = mock.PropertyMock(
            return_value=self.mock_response_content
        )
        self.patcher.get.return_value = self.mock_response

    def tearDown(self) -> None:
        super().tearDown()
        self.requests_mock.stop()

    def test_new_path_returned_as_expected(self):

        expected = os.path.join(self.faux_dir.name, 'namelist.txt')
        found = MOD.download_banlist(self.faux_dir.name)

        self.assertEqual(expected, found)
        self.patcher.get.assert_called_once_with(MOD.NAMELIST_URL)

    def test_namelist_has_expected_content(self):

        found = MOD.download_banlist(self.faux_dir.name)

        with open(found, 'br') as fh:
            self.assertEqual(self.mock_response_content, fh.read())

    def test_raises_ValueError_when_non_directory_given(self):
        with NamedTemporaryFile() as temp:
            with self.assertRaisesRegex(ValueError, f"{temp.name} is not a directory"):
                MOD.download_banlist(temp.name)


class Test_init_config(ThisTestCase):
    def setUp(self) -> None:
        super().setUp()

    def tearDown(self) -> None:
        super().tearDown()

    def test_config_written_as_expected(self):
        with NamedTemporaryFile('r+') as temp_file:
            MOD.init_config(temp_file.name)

            temp_file.seek(0)
            file_obj = MOD.json.load(temp_file)
        self.assertEqual(MOD.default_config._asdict(), file_obj)

class Test_load_config(ThisTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.config_file = os.path.join(HERE, "test_config.json")

    def tearDown(self) -> None:
        super().tearDown()
    
    def test_ValueError_raised_if_config_DNE(self):

        faux_config_file = "fake_config_file.json"
        with self.assertRaisesRegex(ValueError, f"{faux_config_file}"):
            MOD.load_config(faux_config_file)
    
    @mock.patch("bantool.config.json")
    def test_ValueError_raised_on_json_load_exception(self, json_patch):

        faux_error_msg = "Fake error!"
        json_patch.load.side_effect = TypeError(faux_error_msg)
        with self.assertRaisesRegex(ValueError, faux_error_msg):
            MOD.load_config(self.config_file)
    
    def test_ValueError_raised_on_json_load_exception_nomock(self):
        faux_data = "{'fake': 'foobar',}"
        with NamedTemporaryFile('r+') as faux_config:
            faux_config.write(faux_data)
            faux_config.seek(0)

            with self.assertRaises(ValueError):
                MOD.load_config(faux_config.name)
    
    def test_load_config_file_returns_named_tuple(self):
        expected = MOD.default_config
        found = MOD.load_config(self.config_file)

        self.assertEqual(found, expected)




# __END__
