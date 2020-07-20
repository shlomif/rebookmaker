#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_rebook
----------------------------------

Tests for `rebookmaker` module.
"""

import pytest  # noqa: F401


def test_bhs():
    """Sample pytest test function with the pytest fixture as an argument.
    """
    import rebookmaker
    assert rebookmaker.EbookMaker()
