#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the MIT license.
"""
rebookmaker - an open source (MIT-licensed) re-implementation of
Marcelo Lira’s ( @setanta ) ebookmaker.

It converts an EPUB definition inside a JSON file along with
some input HTML and image files into an .epub.

See:

* https://github.com/setanta/ebookmaker/ - does not have an explicit
licence, which prompted this re-implementation.

* https://pypi.org/project/ebookmaker/ - GPLv3 by Project Gutenberg and
incompatible with @setanta 's .

"""

import json
import re
from glob import glob
from zipfile import ZIP_STORED, ZipFile

from bs4 import BeautifulSoup

import jinja2
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Markup

import pkg_resources

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
    """
    Utility class
    """
    def __init__(self):
        self.counter = 0
        self.toc_html_text = Markup('')

    def get_idx(self):
        """docstring for get_idx"""
        self.counter += 1
        return self.counter


RE = re.compile("[\\n\\r]*\\Z")


class EbookMaker:
    """docstring for EbookMaker"""
    def __init__(self, compression=ZIP_STORED):
        self._compression = compression
        self._env = Environment(
            autoescape=jinja2.select_autoescape(
                disabled_extensions=('nonenone',),
                default=True,
                default_for_string=True,
            ),
            loader=FileSystemLoader([
                pkg_resources.resource_filename(__name__, 'data/templates'),
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
        """
        Prepare an EPUB inside output_filename from the
        JSON file json_fn
        """
        with open(json_fn, 'rb') as file_handle:
            json_data = json.load(file_handle)
        return self.make_epub_from_data(json_data, output_filename)

    def make_epub_from_data(self, json_data, output_filename):
        """
        Prepare an EPUB inside output_filename from the
        raw JSON-like data json_data.

        (Added at version 0.6.0 .)
        """
        _compression = self._compression

        def _write_mimetype_file_first(zip_obj):
            """docstring for _write_mimetype_file_first"""
            zip_obj.writestr("mimetype", "application/epub+zip", ZIP_STORED)
        zip_obj = ZipFile(output_filename, 'w')
        _write_mimetype_file_first(zip_obj)
        images = set()
        cover_image_fn = json_data['cover']
        # images.add(cover_image_fn)
        h_tags = []
        for i in range(1, min(6, json_data['toc']['depth'])+1):
            h_tags.append("h"+str(i))
        h_tags = tuple(h_tags)
        htmls = []
        for html_src in ['cover.html']:
            zip_obj.writestr(
                'OEBPS/' + html_src,
                (self._cover_template.render(
                    tab="\t",
                    cover_image_fn=cover_image_fn,
                    esc_title=json_data['title']) + "\n"),
                _compression)
        nav_points = []
        for item in json_data['contents']:
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
        zip_obj.writestr(
            "META-INF/container.xml",
            self._container_xml_template.render(), ZIP_STORED)
        zip_obj.write("style.css", "OEBPS/style.css", _compression)
        images = sorted(list(images))
        for img in images + [cover_image_fn]:
            zip_obj.write(img, 'OEBPS/' + img)
        for html_src in htmls:
            zip_obj.write(html_src, 'OEBPS/' + html_src, _compression)

        def _writestr(basefn, content_text):
            zip_obj.writestr(
                "OEBPS/" + basefn,
                RE.sub("\n", content_text),
                _compression
            )

        content_text = self._content_opf_template.render(
            author_sorted=json_data['authors'][0]['sort'],
            author_name=json_data['authors'][0]['name'],
            dc_rights=json_data['rights'],
            language=json_data['language'],
            publisher=json_data['publisher'],
            title=json_data['title'],
            url=json_data['identifier']['value'],
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
            guide=(json_data['guide'] if 'guide' in json_data else None),
            htmls0=[
                {'id': 'item'+str(idx), 'href': fn}
                for idx, fn in enumerate(['cover.html', 'toc.html', ] + htmls)
                ],
        )
        _writestr("content.opf", content_text)

        def get_nav_points(counter, nav_points, start_idx, level):
            idx = start_idx
            ret = Markup('')
            prefix = (INDENT_STEP * (level-1))
            while idx < len(nav_points):
                rec = nav_points[idx]
                if rec['level'] < level:
                    return ret, idx
                href = rec['href']
                label = rec['label']
                counter.toc_html_text += Markup(
                    '<p style="text-indent: {level}em;">' +
                    '<a href="{href}">{label}</a></p>\n' +
                    '').format(
                        level=level,
                        label=label,
                        href=href
                    )

                ret += Markup(
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
                ret += Markup(
                    '{p}</navPoint>\n'
                ).format(p=prefix)
            return ret, idx
        nav_points_text = Markup('')
        counter = MyCounter()
        for file_nav_points in nav_points:
            counter.toc_html_text += Markup(
                '<div style="margin-top: 1em;">\n'
            )
            nav_points_text += get_nav_points(
                counter, file_nav_points, 0, 1
            )[0]
            counter.toc_html_text += Markup('</div>\n')
        content_text = self._toc_ncx_template.render(
            author_name=json_data['authors'][0]['name'],
            title=json_data['title'],
            navPoints_text=nav_points_text
        )
        _writestr("toc.ncx", content_text)
        content_text = self._toc_html_template.render(
            toc_html_text=counter.toc_html_text,
        )
        _writestr("toc.html", content_text)
        zip_obj.close()
