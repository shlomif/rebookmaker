#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the MIT license.

xmlns1 = "urn:oasis:names:tc:opendocument:xmlns:container"
medtype1 = "application/oebps-package+xml"
EPUB_CONTAINER = ('''<?xml version="1.0"?>
<container version="1.0" xmlns="{xmlns1}">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="{medtype1}"/>
    </rootfiles>
</container>''').format(medtype1=medtype1, xmlns1=xmlns1)


def _my_amend_epub(filename):
    from zipfile import ZipFile, ZIP_STORED
    z = ZipFile(filename, 'a')
    z.writestr("mimetype", "application/epub+zip", ZIP_STORED)
    z.writestr("META-INF/container.xml", EPUB_CONTAINER, ZIP_STORED)
    z.write("style.css", "OEBPS/style.css", ZIP_STORED)
    z.close()
