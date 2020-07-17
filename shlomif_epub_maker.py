#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the MIT license.

def _my_amend_epub(filename):
    from zipfile import ZipFile, ZIP_STORED
    z = ZipFile(filename, 'a')
    z.writestr("mimetype", "application/epub+zip", ZIP_STORED)
    z.close()
