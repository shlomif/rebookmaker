#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the MIT license.

import json
import os
import re
from glob import glob
from zipfile import ZIP_STORED, ZipFile

from bs4 import BeautifulSoup

import jinja2
from jinja2 import Environment
from jinja2 import FileSystemLoader

INDENT_STEP = (' ' * 4)


EPUB_COVER = ''''''


def _get_image_type(filename):
    if filename.endswith('.jpeg'):
        return 'image/jpeg'
    if filename.endswith('.jpg'):
        return 'image/jpeg'
    if filename.endswith('.png'):
        return 'image/png'
    if filename.endswith('.webp'):
        return 'image/webp'
    raise IOError("unknown image extension for '{}'".format(filename))


class MyCounter:
    def __init__(self):
        self.counter = 0
        self.toc_html_text = jinja2.Markup('')

    def get_idx(self):
        """docstring for get_idx"""
        self.counter += 1
        return self.counter


RE = re.compile("[\\n\\r]*\\Z")


class EbookMaker:
    """docstring for EbookMaker"""
    def __init__(self):
        self._env = Environment(
            autoescape=jinja2.select_autoescape(
                disabled_extensions=('nonenone',),
                default=True,
                default_for_string=True,
            ),
            loader=FileSystemLoader([
                os.getenv("SCREENPLAY_COMMON_INC_DIR") + "/templates"
            ])
        )
        self._cover_template = self._env.get_template('cover.html' + '.jinja')
        self._container_xml_template = self._env.get_template(
            'container.xml' + '.jinja')
        self._content_opf_template = self._env.get_template(
            'content.opf' + '.jinja')
        self._toc_ncx_template = self._env.get_template('toc.ncx' + '.jinja')
        self._toc_html_template = self._env.get_template('toc.html' + '.jinja')

    def make_epub(self, json_fn, output_filename):
        zip_obj = ZipFile(output_filename, 'w')
        with open(json_fn, 'rb') as file_handle:
            j = json.load(file_handle)
        images = set()
        cover_image_fn = j['cover']
        # images.add(cover_image_fn)
        h_tags = []
        for i in range(1, min(6, j['toc']['depth'])+1):
            h_tags.append("h"+str(i))
        h_tags = tuple(h_tags)
        htmls = []
        for html_src in ['cover.html']:
            zip_obj.writestr(
                'OEBPS/' + html_src,
                (self._cover_template.render(
                    tab="\t",
                    cover_image_fn=cover_image_fn,
                    esc_title=j['title']) + "\n"),
                ZIP_STORED)
        nav_points = []
        for item in j['contents']:
            if 'generate' not in item:
                item['generate'] = (item['type'] == 'toc')
            if item['generate']:
                continue
            source_spec = item['source']
            if item['type'] == 'text' and '*' in source_spec:
                html_sources = sorted(glob(source_spec))
            else:
                html_sources = [source_spec]
            for html_src in html_sources:
                page_nav = []
                htmls.append(html_src)
                with open(html_src, 'rt') as file_handle:
                    text = file_handle.read()
                soup = BeautifulSoup(text, 'lxml')
                for img in soup.find_all('img'):
                    src = img['src']
                    if src:
                        images.add(src)
                for h_elem in soup.find_all(h_tags):
                    if h_elem.has_attr('id'):
                        href = html_src+"#"+h_elem['id']
                    else:
                        href = None
                    page_nav.append(
                        {
                            'level': int(h_elem.name[-1]),
                            'href': href,
                            'label': h_elem.get_text(),
                        }
                    )
                nav_points.append(page_nav)
        zip_obj.writestr("mimetype", "application/epub+zip", ZIP_STORED)
        zip_obj.writestr(
            "META-INF/container.xml",
            self._container_xml_template.render(), ZIP_STORED)
        zip_obj.write("style.css", "OEBPS/style.css", ZIP_STORED)
        images = sorted(list(images))
        for img in (images + [cover_image_fn]):
            zip_obj.write(img, 'OEBPS/' + img)
        for html_src in htmls:
            zip_obj.write(html_src, 'OEBPS/' + html_src, ZIP_STORED)

        def _writestr(basefn, content_text):
            zip_obj.writestr(
                "OEBPS/" + basefn,
                RE.sub("\n", content_text),
                ZIP_STORED
            )

        content_text = self._content_opf_template.render(
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

        def get_nav_points(counter, nav_points, start_idx, level):
            idx = start_idx
            ret = jinja2.Markup('')
            prefix = (INDENT_STEP * (level-1))
            while idx < len(nav_points):
                rec = nav_points[idx]
                if rec['level'] < level:
                    return ret, idx
                href = rec['href']
                label = rec['label']
                counter.toc_html_text += jinja2.Markup(
                    '<p style="text-indent: {level}em;">' +
                    '<a href="{href}">{label}</a></p>\n' +
                    '').format(
                    level=level,
                    label=label,
                    href=href)

                ret += jinja2.Markup(
                    '{p}<navPoint id="nav{idx}" playOrder="{idx}">\n' +
                    '{p}{indent}<navLabel><text>{label}</text></navLabel>\n' +
                    '{p}{indent}<content src="{href}"/>\n' +
                    ''
                ).format(
                    p=prefix,
                    indent=INDENT_STEP,
                    label=label,
                    href=href, idx=counter.get_idx())
                next_idx = idx + 1
                if next_idx < len(nav_points):
                    next_level = nav_points[next_idx]['level']
                    if next_level > level:
                        sub_ret, next_idx = get_nav_points(
                            counter,
                            nav_points,
                            next_idx, next_level)
                        ret += sub_ret
                idx = next_idx
                ret += jinja2.Markup(
                    '{p}</navPoint>\n'
                ).format(p=prefix)
            return ret, idx
        nav_points_text = jinja2.Markup('')
        counter = MyCounter()
        for file_nav_points in nav_points:
            counter.toc_html_text += jinja2.Markup(
                '<div style="margin-top: 1em;">\n'
            )
            nav_points_text += get_nav_points(
                counter, file_nav_points, 0, 1
            )[0]
            counter.toc_html_text += jinja2.Markup('</div>\n')
        content_text = self._toc_ncx_template.render(
            author_name=j['authors'][0]['name'],
            title=j['title'],
            navPoints_text=nav_points_text
        )
        _writestr("toc.ncx", content_text)
        content_text = self._toc_html_template.render(
            toc_html_text=counter.toc_html_text,
        )
        _writestr("toc.html", content_text)
        zip_obj.close()
