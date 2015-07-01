#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import nose
import os
import json
import copy
from functools import wraps
from pprint import pprint

from xlseries.strategies.discover.parameters import Parameters
from xlseries.strategies.discover.parameters import InvalidParameter
from xlseries.strategies.discover.parameters import CriticalParameterMissing
from xlseries.utils.case_loaders import load_critical_parameters_case


"""
test_parameters

This module tests the parameters object.
"""


def get_orig_params_path(file_name):
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "original", file_name)


def get_exp_params_path(file_name):
    base_dir = os.path.dirname(__file__)
    return os.path.join(base_dir, "expected", file_name)


class ParametersTest(unittest.TestCase):

    def setUp(self):
        self.params = Parameters(get_orig_params_path("test_params.json"))
        self.params_exp = Parameters(get_exp_params_path("test_params.json"))

    def tearDown(self):
        del self.params

    # @unittest.skip("skip")
    def test_load_from_json(self):
        self.assertEqual(self.params.__dict__, self.params_exp.__dict__)

    def test_load_from_dict(self):
        with open(get_orig_params_path("test_params.json")) as f:
            params_dict = json.load(f)
        params = Parameters(params_dict)
        pprint(params.__dict__)
        pprint(self.params_exp.__dict__)
        self.assertEqual(params.__dict__, self.params_exp.__dict__)

    # @unittest.skip("skip")
    def test_get_num_series(self):
        self.assertEqual(self.params._get_num_series(self.params.__dict__), 3)
        self.assertEqual(self.params._get_num_series({"param": None}), None)

    def test_unpack_header_ranges(self):

        exp = ["A5", "A6", "A7", "A8"]
        self.assertEqual(self.params._unpack_header_ranges("a5-A8"), exp)

        exp = ["A5", "B5", "C5"]
        self.assertEqual(self.params._unpack_header_ranges("A5-c5"), exp)

        exp = ["A5"]
        self.assertEqual(self.params._unpack_header_ranges("a5"), exp)

        exp = None
        self.assertEqual(self.params._unpack_header_ranges("None"), exp)

        exp = [["A1", "A2"], ["A1", "A2"]]
        orig = [["A1", "A2"], ["A1", "A2"]]
        self.assertEqual(self.params._unpack_header_ranges(orig), exp)

        exp = [["A1", "A2", "A3"], ["A1", "A2", "A3"]]
        orig = [["A1-A3"], ["A1-A3"]]
        self.assertEqual(self.params._unpack_header_ranges(orig), exp)

    def test_get_series_params(self):
        params = Parameters(get_orig_params_path(
            "test_params_time_multicolumn.json"))

        self.assertEqual(params["time_header_coord"], [["A1", "A2"],
                                                       ["A1", "A2"],
                                                       ["A1", "A2"]])

        self.assertEqual(params[0]["time_header_coord"], ["A1", "A2"])

    def test_valid_param_value(self):
        self.assertTrue(self.params._valid_param_value(True, [True, False]))
        self.assertTrue(self.params._valid_param_value(True, []))
        self.assertFalse(self.params._valid_param_value("A1", [True, False]))
        self.assertFalse(self.params._valid_param_value(None, [True, False]))

    def test_valid_freq(self):
        valid_freqs = ["Y", "Q", "M", "W", "D"]
        self.assertTrue(self.params._valid_freq("YQQQQ", valid_freqs))
        self.assertTrue(self.params._valid_freq("D", valid_freqs))
        self.assertFalse(self.params._valid_freq("YQQX", valid_freqs))

    def test_validate_parameters_exception(self):
        params = {"continuity": "A1"}
        valid_values = {"continuity": [True, False]}
        with self.assertRaises(InvalidParameter):
            self.params._validate_parameters(params, valid_values)

    def test_ensure_critical_parameters_exception(self):
        params = {"data_starts": None}
        critical = ["data_starts"]
        valid_values = {"data_starts": [int]}
        with self.assertRaises(CriticalParameterMissing):
            Parameters._check_has_critical(params, critical,
                                           valid_values)

    def test_get_missings(self):
        params = Parameters({
            "alignment": None,
            "headers_coord": ["B1", "C1"],
            "data_starts": 2,
            "data_ends": 256,
            "frequency": "M",
            "time_header_coord": "A1",
            "time_multicolumn": None,
            "time_composed": None,
            "time_alignment": 0,
            "continuity": None,
            "blank_rows": None,
            "missings": None,
            "missing_value": None,
            "series_names": None
        })
        exp_missings = ["time_composed", "continuity",
                        "blank_rows", "missings"]

        self.assertEqual(set(exp_missings), set(params.get_missings()))

    def test_check_consistency(self):
        params_dict = {"data_starts": 1,
                       "headers_coord": ["A2", "B2", "C2", "D2"]}
        with self.assertRaises(AssertionError):
            Parameters._check_consistency(params_dict)

        params_dict = {"data_starts": 1,
                       "headers_coord": ["B1", "B2", "B3", "B4"]}
        with self.assertRaises(AssertionError):
            Parameters._check_consistency(params_dict)

    def test_guess_alignment(self):
        headers = ["A1", "B1", "C1"]
        self.assertEqual(Parameters._guess_alignment(headers), "vertical")

        headers = ["A1", "B1", "D1", "E1"]
        self.assertEqual(Parameters._guess_alignment(headers), "vertical")

        headers = ["A1", "A2"]
        self.assertEqual(Parameters._guess_alignment(headers), "horizontal")

        headers = ["A1", "A3", "A5", "A7"]
        self.assertEqual(Parameters._guess_alignment(headers), "horizontal")

        headers = ["A1", "A3", "A5"]
        self.assertEqual(Parameters._guess_alignment(headers), None)

        headers = ["A1", "A3", "A5", "B7"]
        self.assertEqual(Parameters._guess_alignment(headers), None)


def load_case_number():
    """Decorate a test loading the case number taken from test name."""

    def fn_decorator(fn):
        case_num = int(fn.__name__.split("_")[1][-1])

        @wraps(fn)
        def fn_decorated(*args, **kwargs):
            kwargs["case_num"] = case_num
            fn(*args, **kwargs)

        return fn_decorated
    return fn_decorator


# @unittest.skip("skip")
class ParametersCriticalDictTestCase(unittest.TestCase):

    """Test Parameters loading dict with only critical parameters."""

    CRITICAL_PARAMS = {

        1: {'data_starts': 2,
            'frequency': u'M',
            'headers_coord': [u'B1', u'C1'],
            'time_header_coord': u'A1'},

        2: {'blank_rows': [False, True],
            'continuity': [True, False],
            'data_starts': [5, 22],
            'frequency': [u'D', u'M'],
            'headers_coord': [u'D4', u'F4'],
            'missing_value': [u'Implicit', None],
            'missings': [True, False],
            'time_alignment': [0, -1],
            'time_header_coord': [u'C4', u'F4']},

        3: {'data_starts': 7,
            'frequency': u'Q',
            'headers_coord': [u'B4', u'C4', u'D4'],
            'time_header_coord': u'A4'},

        4: {'data_starts': [5, 5, 5, 5, 52, 52, 52, 52],
            'frequency': u'Q',
            'headers_coord': [u'B4', u'C4', u'D4', u'E4', u'B51', u'C51',
                              u'D51', u'E51'],
            'time_header_coord': [u'A4', u'A4', u'A4', u'A4', u'A51', u'A51',
                                  u'A51', u'A51']},

        5: {'data_starts': 28,
            'frequency': u'M',
            'headers_coord': [u'G22', u'H22'],
            'time_header_coord': u'A18'},

        6: {'data_starts': 3,
            'frequency': u'YQQQQ',
            'headers_coord': ['B8', 'B9', 'B10', 'B11', 'B12', 'B13', 'B14',
                              'B15', 'B16', 'B17', 'B18', 'B19', 'B20', 'B21',
                              'B22', 'B23', 'B24', 'B25', 'B26', 'B27', 'B28'],
            'time_header_coord': [u'C4', u'C6']},

        7: {'data_starts': 2,
            'frequency': u'Y',
            'headers_coord': [u'A8', 'A10', 'A11', 'A12', 'A14', 'A15', 'A16',
                              'A18', 'A19', 'A20', 'A21', 'A22', 'A24',
                              'A25', 'A26', u'A28', u'A30', u'A32', u'A34',
                              'A36', 'A37', 'A38', 'A39', 'A41', 'A42',
                              'A43', 'A44', u'A46', u'A48', 'A50', 'A51',
                              'A52', u'A55'],
            'time_header_coord': u'A6'}
    }

    def check_critical_dict_params(self, case_num):
        """Check critical dict parameters loading.

        Args:
            case_num (int): The test case number to run.
        """

        params = Parameters(self.CRITICAL_PARAMS[case_num].copy())
        exp_params = load_critical_parameters_case(case_num)

        # override the guessing of Parameters
        params.remove("alignment")

        self.assertEqual(params, exp_params)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case1(self, case_num):
        self.check_critical_dict_params(case_num)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case2(self, case_num):
        self.check_critical_dict_params(case_num)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case3(self, case_num):
        self.check_critical_dict_params(case_num)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case4(self, case_num):
        self.check_critical_dict_params(case_num)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case5(self, case_num):
        self.check_critical_dict_params(case_num)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case6(self, case_num):
        self.check_critical_dict_params(case_num)

    # @unittest.skip("skip")
    @load_case_number()
    def test_case7(self, case_num):
        self.check_critical_dict_params(case_num)


if __name__ == '__main__':
    nose.run(defaultTest=__name__)
