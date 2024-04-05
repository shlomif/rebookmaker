#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_rebook
----------------------------------

Tests for `rebookmaker` module.
"""

import pytest  # noqa: F401


def test_rebookmaker():
    import rebookmaker
    assert rebookmaker.EbookMaker()
