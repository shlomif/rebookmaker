#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the MIT license.

import html
import json
import os
import re
from glob import glob
from zipfile import ZIP_STORED, ZipFile

from bs4 import BeautifulSoup

from jinja2 import Environment
from jinja2 import FileSystemLoader

xmlns1 = "urn:oasis:names:tc:opendocument:xmlns:container"
medtype1 = "application/oebps-package+xml"
EPUB_CONTAINER = ('''<?xml version="1.0"?>
<container version="1.0" xmlns="{xmlns1}">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="{medtype1}"/>
    </rootfiles>
</container>''').format(medtype1=medtype1, xmlns1=xmlns1)


doctype = \
    ('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"' +
     ' "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')
htmlstart = \
    ('<html xmlns="http://www.w3.org/1999/xhtml" xmlns:xsi=' +
     '"http://www.w3.org/2001/XMLSchema-instance" xml:lang="en" >')
imgpref = '''<p class="center"><img id="coverimage" src="'''

EPUB_COVER = '''<?xml version="1.0" encoding="UTF-8"?>
{doctype}
{htmlstart}
<head>
<title>{esc_title}</title>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<link rel="stylesheet" type="text/css" href="style.css" />
<style type="text/css">
body {{
{tab}margin: 0;
{tab}padding: 0;
}}
img#coverimage {{
{tab}max-width: 100%;
{tab}padding: 0;
{tab}margin: 0;
}}
</style>
</head>
<body>

<!-- Generated file, modifying it is futile. -->

{imgpref}{cover_image_fn}" alt="{esc_title}" /></p>

</body>
</html>
'''


def _get_image_type(fn):
    if fn.endswith('.jpeg'):
        return 'image/jpeg'
    if fn.endswith('.jpg'):
        return 'image/jpeg'
    if fn.endswith('.png'):
        return 'image/png'
    if fn.endswith('.webp'):
        return 'image/webp'
    assert 0


def _my_amend_epub(filename, json_fn):
    z = ZipFile(filename, 'w')
    with open(json_fn, 'rb') as fh:
        j = json.load(fh)
    images = set()
    cover_image_fn = j['cover']
    # images.add(cover_image_fn)
    h_tags = []
    for i in range(1, min(6, j['toc']['depth'])+1):
        h_tags.append("h"+str(i))
    h_tags = tuple(h_tags)
    htmls = []
    for html_src in ['cover.html']:
        z.writestr(
            'OEBPS/' + html_src,
            EPUB_COVER.format(
                imgpref=imgpref, tab="\t", htmlstart=htmlstart,
                cover_image_fn=cover_image_fn,
                doctype=doctype,
                esc_title=html.escape(j['title'])),
            ZIP_STORED)
    nav_points = []
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
            page_nav = []
            htmls.append(html_src)
            with open(html_src, 'rt') as fh:
                text = fh.read()
            soup = BeautifulSoup(text, 'lxml')
            for img in soup.find_all('img'):
                src = img['src']
                if src:
                    images.add(src)
            for h in soup.find_all(h_tags):
                if h.has_attr('id'):
                    href = html_src+"#"+h['id']
                else:
                    href = None
                page_nav.append(
                    {
                        'level': int(h.name[-1]),
                        'href': href,
                        'label': h.get_text(),
                    }
                    )
            nav_points.append(page_nav)
    z.writestr("mimetype", "application/epub+zip", ZIP_STORED)
    z.writestr("META-INF/container.xml", EPUB_CONTAINER, ZIP_STORED)
    z.write("style.css", "OEBPS/style.css", ZIP_STORED)
    images = sorted(list(images))
    for img in (images + [cover_image_fn]):
        z.write(img, 'OEBPS/' + img)
    for html_src in htmls:
        z.write(html_src, 'OEBPS/' + html_src, ZIP_STORED)

    env = Environment(
            loader=FileSystemLoader([os.getenv("SCREENPLAY_COMMON_INC_DIR")])
            )

    def _writestr(basefn, content_text):
        z.writestr(
            "OEBPS/" + basefn,
            re.sub("[\\n\\r]*\\Z", "\n", content_text), ZIP_STORED)

    template = env.get_template('content-opf' + '.jinja')
    content_text = template.render(
        author_sorted=j['authors'][0]['sort'],
        author_name=j['authors'][0]['name'],
        dc_rights=j['rights'],
        language=j['language'],
        publisher=j['publisher'],
        title=j['title'],
        url=j['identifier']['value'],
        images0=[
            {
                'id': 'coverimage',
                'href': cover_image_fn,
                'media_type': _get_image_type(cover_image_fn),
            },
        ],
        images1=[
            {'id': 'image' + str(idx), 'href': fn,
             'media_type': _get_image_type(fn)}
            for idx, fn in enumerate(images)
                ],
        guide=(j['guide'] if 'guide' in j else None),
        htmls0=[
            {'id': 'item'+str(idx), 'href': fn}
            for idx, fn in enumerate(['cover.html', 'toc.html', ] + htmls)
            ],
    )
    _writestr("content.opf", content_text)
    template = env.get_template('toc-ncx' + '.jinja')

    counter = 1
    toc_html_text = ''

    def get_nav_points(nav_points, start_idx, level):
        nonlocal counter
        idx = start_idx
        ret = ''
        prefix = (' '*4*(level-1))
        while idx < len(nav_points):
            rec = nav_points[idx]
            if rec['level'] < level:
                return ret, idx
            nonlocal toc_html_text
            if rec['href']:
                toc_html_text += (
                    '<p style="text-indent: {level}em;">' +
                    '<a href="{href}">{text}</a></p>\n' +
                    '').format(
                    level=level,
                    text=rec['label'],
                    href=rec['href'])

            ret += (
                '{p}<navPoint id="nav{idx}" playOrder="{idx}">\n' +
                '{p}{indent}<navLabel><text>{text}</text></navLabel>\n' +
                '{p}{indent}<content src="{href}"/>\n' +
                ''
            ).format(
                p=prefix,
                indent=(' '*4), text=rec['label'],
                href=rec['href'], idx=counter)
            counter += 1
            next_idx = idx + 1
            if next_idx < len(nav_points):
                next_level = nav_points[next_idx]['level']
                if next_level > level:
                    sub_ret, next_idx = get_nav_points(
                        nav_points,
                        next_idx, next_level)
                    ret += sub_ret
            idx = next_idx
            ret += (
                '{p}</navPoint>\n'
            ).format(p=prefix)
        return ret, idx
    nav_points_text = ''
    for n in nav_points:
        toc_html_text += '<div style="margin-top: 1em;">\n'
        nav_points_text += get_nav_points(n, 0, 1)[0]
        toc_html_text += '</div>\n'
    content_text = template.render(
        author_name=j['authors'][0]['name'],
        title=j['title'],
        navPoints_text=nav_points_text
    )
    _writestr("toc.ncx", content_text)
    template = env.get_template('toc-html' + '.jinja')
    content_text = template.render(
        toc_html_text=toc_html_text,
    )
    _writestr("toc.html", content_text)
    z.close()
