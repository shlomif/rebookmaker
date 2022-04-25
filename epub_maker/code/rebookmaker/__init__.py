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
from markupsafe import Markup
# from jinja2.utils.markupsafe import Markup
# from jinja2.utils import Markup
# from jinja2 import Markup

import pkg_resources

INDENT_STEP = (' ' * 4)


EPUB_COVER = ''''''


def _get_image_type(filename, found_webp):
    if filename.endswith('.jpeg'):
        return 'image/jpeg'
    if filename.endswith('.jpg'):
        return 'image/jpeg'
    if filename.endswith('.png'):
        return 'image/png'
    if filename.endswith('.webp'):
        found_webp[0] = True
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
STRIP_DOCTYPE__REGEX = re.compile(
    "\\A((?:\\s*<\\?[^\\?]*\\?>)*)<!DOCTYPE[^>]*>",
    re.M | re.S
)


class EbookMaker:
    """docstring for EbookMaker"""
    def __init__(self, compression=ZIP_STORED):
        self._compression = compression
        self._templates_dirname = pkg_resources.resource_filename(
            __name__, 'data/templates'
        )
        self._env = Environment(
            autoescape=jinja2.select_autoescape(
                disabled_extensions=('nonenone',),
                default=True,
                default_for_string=True,
            ),
            loader=FileSystemLoader([
                self._templates_dirname
            ]),
        )
        self._cover_template = self._env.get_template('cover.html' + '.jinja')
        self._container_xml_template = self._env.get_template(
            'container.xml' + '.jinja')
        self._content_opf_template = self._env.get_template(
            'content.opf' + '.jinja')
        self._toc_ncx_template = self._env.get_template('toc.ncx' + '.jinja')
        self._toc_html_template = self._env.get_template('toc.html' + '.jinja')
        self._nav_xhtml_template = self._env.get_template(
            'nav.html' + '.jinja'
        )

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

        def _path(fn):
            return 'OEBPS/' + fn
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
        for html_src in ['cover.xhtml']:
            zip_obj.writestr(
                _path(html_src),
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
                soup = BeautifulSoup(text, features='lxml-xml', )
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
        found_webp = [False]
        images0 = [
                {
                    'id': 'coverimage',
                    'href': cover_image_fn,
                    'media_type': _get_image_type(
                        filename=cover_image_fn,
                        found_webp=found_webp,
                     ),
                    },
                ]
        images = sorted(list(images))
        images1 = [
                {'id': 'image' + str(idx), 'href': fn,
                    'media_type': _get_image_type(
                        filename=fn,
                        found_webp=found_webp,
                        )}
                for idx, fn in enumerate(images)
                ]
        for img in images + [cover_image_fn]:
            zip_obj.write(img, _path(img))
        if found_webp[0]:
            imgfn = 'onepixel.png'
            zip_obj.write(
                self._templates_dirname + '/' + imgfn, _path(imgfn)
            )
        for html_src in htmls:
            if html_src.endswith(".xhtml"):
                with open(html_src, 'rt') as file_handle:
                    mytext = file_handle.read()
                mytext = STRIP_DOCTYPE__REGEX.sub(
                    "\\1", mytext, 0
                )
                zip_obj.writestr(_path(html_src), mytext, _compression)
            else:
                zip_obj.write(html_src, _path(html_src), _compression)

        def _writestr(basefn, content_text):
            zip_obj.writestr(
                "OEBPS/" + basefn,
                RE.sub("\n", content_text),
                _compression
            )
        uid_url = json_data['identifier']['value']

        content_text = self._content_opf_template.render(
            author_sorted=json_data['authors'][0]['sort'],
            author_name=json_data['authors'][0]['name'],
            found_webp=found_webp[0],
            images0=images0,
            images1=images1,
            modified_date=(
                json_data['modified_date']
                if ('modified_date' in json_data) else "2021-01-01T00:00:01Z"),
            dc_rights=json_data['rights'],
            language=json_data['language'],
            publisher=json_data['publisher'],
            title=json_data['title'],
            url=uid_url,
            guide=(json_data['guide'] if 'guide' in json_data else None),
            htmls0=[
                {'id': 'item'+str(idx), 'href': fn}
                for idx, fn in enumerate(
                    ['cover.xhtml', 'toc.xhtml', ] + htmls
                )
                ],
        )
        _writestr("content.opf", content_text)

        def get_nav_points(counter, nav_points, start_idx, level):
            idx = start_idx
            ret = Markup('')
            ret_xhtml = Markup('')
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

                temp_ret_idx = counter.get_idx()
                ret += Markup(
                    '{p}<navPoint id="nav{idx}" playOrder="{idx}">\n' +
                    '{p}{indent}<navLabel><text>{label}</text></navLabel>\n' +
                    '{p}{indent}<content src="{href}"/>\n' +
                    ''
                ).format(
                    p=prefix,
                    indent=INDENT_STEP,
                    label=label,
                    href=href, idx=temp_ret_idx)
                ret_xhtml += Markup(
                    '{p}<li>\n' +
                    '{p}<a href="{href}">{label}</a>\n' +
                    ''
                ).format(
                    p=prefix,
                    indent=INDENT_STEP,
                    label=label,
                    href=href, idx=temp_ret_idx)
                next_idx = idx + 1
                if next_idx < len(nav_points):
                    next_level = nav_points[next_idx]['level']
                    if next_level > level:
                        ret_xhtml += Markup('<ol>')
                        sub_ret, sub_xhtml, next_idx = get_nav_points(
                            counter,
                            nav_points,
                            next_idx, next_level)
                        ret += sub_ret
                        ret_xhtml += sub_xhtml
                        ret_xhtml += Markup('</ol>')
                idx = next_idx
                ret += Markup(
                    '{p}</navPoint>\n'
                ).format(p=prefix)
                ret_xhtml += Markup(
                    '{p}</li>\n'
                ).format(p=prefix)
            return ret, ret_xhtml, idx
        nav_points_text = Markup('')
        nav_points_xhtml = Markup('')
        counter = MyCounter()
        for file_nav_points in nav_points:
            counter.toc_html_text += Markup(
                '<div style="margin-top: 1em;">\n'
            )
            if len(file_nav_points):
                min_level = min([x['level'] for x in file_nav_points])
                if min_level > 1:
                    delta = min_level - 1
                    for x in file_nav_points:
                        x['level'] -= delta

            nav_ncx, nav_xhtml, idx = get_nav_points(
                counter, file_nav_points, 0, 1
            )
            nav_points_text += nav_ncx
            nav_points_xhtml += nav_xhtml
            counter.toc_html_text += Markup('</div>\n')
        content_text = self._toc_ncx_template.render(
            author_name=json_data['authors'][0]['name'],
            navPoints_text=nav_points_text,
            title=json_data['title'],
            url=uid_url,
        )
        _writestr("toc.ncx", content_text)
        content_xhtml = self._nav_xhtml_template.render(
            author_name=json_data['authors'][0]['name'],
            nav_html_text=nav_points_xhtml,
            title=json_data['title'],
            url=uid_url,
        )
        _writestr("nav.xhtml", content_xhtml)
        content_text = self._toc_html_template.render(
            toc_html_text=counter.toc_html_text,
        )
        _writestr("toc.xhtml", content_text)
        zip_obj.close()
