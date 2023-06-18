#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under the terms of the MIT license.

import os

from pydistman import DistManager


class Derived(DistManager):
    def _bin_slurp(self, fn):
        with open(fn, "rb") as ifh:
            ret = ifh.read()
        return ret

    def _bin_fmt_slurp(self, fn_proto):
        return self._bin_slurp(self._myformat(fn_proto))

    def _bin_write(self, to_proto, from_, make_exe=False):
        to = self._myformat(to_proto)
        os.makedirs(os.path.dirname(to), exist_ok=True)
        with open(to, "wb") as ofh:
            ofh.write(self._bin_fmt_slurp(from_))
        if make_exe:
            os.chmod(to, 0o755)

    def _bin_dest_write(self, bn_proto, make_exe=False):
        return self._bin_write(
            "{dest_dir}/"+bn_proto,
            "{src_dir}/"+bn_proto,
            make_exe
        )

    def _build_only_command_custom_steps(self):
        self._dest_append("rebookmaker/rebookmaker", make_exe=True)
        globs = [[ext, "data/templates/*.{}".format(ext)] for
                 ext in ['jinja', 'png', 'xcf', ]]
        for fn in ["{dest_dir}/setup.py", ]:
            self._re_mutate(
                fn_proto=fn,
                pattern="include_package_data=True,",
                repl_fn_proto=None,
                prefix="include_package_data=True,\n    " +
                "package_data={'': [" +
                (",".join(["'" + x[1] + "'" for x in globs])) +
                "],}," +
                "\n    scripts=['rebookmaker/rebookmaker'],",
                )
        self._dest_append("MANIFEST.in")
        for g in globs:
            for fn in self._src_glob("rebookmaker/" + g[1]):
                if g[0] == 'jinja':
                    self._dest_append(fn)
                else:
                    self._bin_dest_write(fn)


dist_name = "rebookmaker"

obj = Derived(
    dist_name=dist_name,
    dist_version="0.8.9",
    project_name="rebookmaker",
    project_short_description="EPUB generator",
    release_date="2023-06-18",
    project_year="2020",
    aur_email="shlomif@cpan.org",
    project_email="shlomif@cpan.org",
    full_name="Shlomi Fish",
    github_username="shlomif",
)
obj.cli_run()
