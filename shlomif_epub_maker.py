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


def _my_amend_epub(filename, json_fn):
    from glob import glob
    from zipfile import ZipFile, ZIP_STORED
    import json
    z = ZipFile(filename, 'a')
    with open(json_fn, 'rb') as fh:
        j = json.load(fh)
    images = set()
    for item in j['contents']:
        if 'generate' not in item:
            item['generate'] = (item['type'] == 'toc')
        if item['generate']:
            continue
        html_src = item['source']
        if item['type'] == 'text' and '*' in html_src:
            html_sources = sorted(glob(html_src))
        else:
            html_sources = [html_src]
        for html_src in html_sources:
            with open(html_src, 'rt') as fh:
                text = fh.read()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'lxml')
            for img in soup.find_all('img'):
                src = img['src']
                if src:
                    images.add(src)
    z.writestr("mimetype", "application/epub+zip", ZIP_STORED)
    z.writestr("META-INF/container.xml", EPUB_CONTAINER, ZIP_STORED)
    z.write("style.css", "OEBPS/style.css", ZIP_STORED)
    for img in sorted(list(images)):
        z.write(img, 'OEBPS/' + img)
    z.close()
