#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the terms of the MIT license.

import sys

from pydistman import DistManager


class Derived(DistManager):
    def _build_only_command_custom_steps(self):
        self._dest_append("rebookmaker/rebookmaker", make_exe=True)
        for fn in ["{dest_dir}/setup.py", ]:
            self._re_mutate(
                fn_proto=fn,
                pattern="include_package_data=True,",
                repl_fn_proto=None,
                prefix="include_package_data=True,\n    " +
                "package_data={'': ['data/templates/*.jinja']}," +
                "\n    scripts=['rebookmaker/rebookmaker'],",
                )
        self._dest_append("MANIFEST.in")
        for fn in self._src_glob("rebookmaker/data/templates/*.jinja"):
            self._dest_append(fn)


try:
    cmd = sys.argv.pop(1)
except IndexError:
    cmd = 'build'

dist_name = "rebookmaker"

obj = Derived(
    dist_name=dist_name,
    dist_version="0.8.4",
    project_name="rebookmaker",
    project_short_description="EPUB generator",
    release_date="2021-03-20",
    project_year="2020",
    aur_email="shlomif@cpan.org",
    project_email="shlomif@cpan.org",
    full_name="Shlomi Fish",
    github_username="shlomif",
)
obj.run_command(cmd=cmd, args=[])
