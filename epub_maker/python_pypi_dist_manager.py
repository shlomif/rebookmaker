#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2020 Shlomi Fish <shlomif@cpan.org>
#
# Distributed under terms of the MIT license.

import glob
import os
import os.path
import platform
import re
import shutil
import sys
from subprocess import check_call

import attr
import cookiecutter.main


@attr.s
class DistGenerator(object):
    dist_name = attr.ib()
    dist_version = attr.ib()
    project_name = attr.ib()
    project_short_description = attr.ib()

    """docstring for DistGenerator"""
    def __attrs_post_init__(self):
        dist_name = self.dist_name
        self.base_dir = ("python-" + dist_name)
        self.src_dir = "code"
        self.src_modules_dir = self.src_dir + "/" + dist_name
        self.dest_dir = 'dest'
        self.dest_modules_dir = self.dest_dir + "/" + dist_name
        system = platform.system().lower()
        self.tox_cmd = (
            "py -3.8 -m tox"
            if (('windows' in system) or ('cygwin' in system)) else 'tox')

    def _slurp(self, fn):
        with open(fn, "rt") as ifh:
            ret = ifh.read()
        return ret

    def _fmt_slurp(self, fn_proto):
        return self._slurp(self._myformat(fn_proto))

    def _myformat(self, mystring):
        return mystring.format(
            base_dir=self.base_dir,
            dest_dir=self.dest_dir,
            dest_modules_dir=self.dest_modules_dir,
            dist_name=self.dist_name,
            src_dir=self.src_dir,
            src_modules_dir=self.src_modules_dir,
            tox_cmd=self.tox_cmd
        )

    def _fmt_rmtree(self, fn_proto):
        """rmtree the formatted fn_proto if it exists."""
        fn = self._myformat(fn_proto)
        if os.path.exists(fn):
            shutil.rmtree(fn)

    def command__build(self):
        self.command__build_only()
        self.command__test()

    def _append(self, to_proto, from_, make_exe=False):
        to = self._myformat(to_proto)
        os.makedirs(os.path.dirname(to), exist_ok=True)
        with open(to, "at") as ofh:
            ofh.write(self._fmt_slurp(from_))
        if make_exe:
            os.chmod(to, 0o755)

    def _dest_append(self, bn_proto, make_exe=False):
        return self._append(
            "{dest_dir}/"+bn_proto,
            "{src_dir}/"+bn_proto,
            make_exe
        )

    def _re_mutate(self, fn_proto, pattern, repl_fn_proto,
                   prefix='', suffix=''):
        fn = self._myformat(fn_proto)
        replacement_string = \
            (prefix +
             self._fmt_slurp(repl_fn_proto) +
             suffix)
        txt = self._slurp(fn)
        txt, count = re.subn(
            pattern,
            replacement_string.replace('\\', '\\\\'),
            txt,
            1,
            re.M | re.S
        )
        assert count == 1
        with open(fn, "wt") as ofh:
            ofh.write(txt)

    def _src_glob(self, proto_expr):
        prefix = self.src_dir + "/"
        glob_expr = prefix + proto_expr
        prefix_len = len(prefix)
        for fn in glob.glob(glob_expr):
            assert fn.startswith(prefix)
            yield fn[prefix_len:]

    def command__build_only(self):
        self._fmt_rmtree("{dest_dir}")
        self._fmt_rmtree("{dist_name}")
        cookiecutter.main.cookiecutter(
            'gh:Kwpolska/python-project-template',
            no_input=True,
            overwrite_if_exists=True,
            extra_context={
                "entry_point": ["none", "cli", "gui", ],
                "project_name": self.project_name,
                "project_short_description": self.project_short_description,
                "release_date": "2020-08-29",
                "repo_name": self.dist_name,
                "version": self.dist_version,
                "year": "2020",
                'aur_email': "shlomif@cpan.org",
                'email': "shlomif@cpan.org",
                'full_name': 'Shlomi Fish',
                'github_username': "shlomif",
                },
            )
        os.rename(self.dist_name, self.dest_dir)

        self._append(
            "{dest_modules_dir}/__init__.py",
            "{src_modules_dir}/__init__.py")

        def _re_mutate2(fn_proto, pattern, prefix='', suffix=''):
            fn = self._myformat(fn_proto)
            replacement_string = \
                (prefix +
                 suffix)
            txt = self._slurp(fn)
            txt, count = re.subn(
                pattern,
                replacement_string.replace('\\', '\\\\'),
                txt,
                1,
                re.M | re.S
            )
            assert count == 1
            with open(fn, "wt") as ofh:
                ofh.write(txt)

        self._re_mutate(
            "{dest_dir}/CHANGELOG.rst",
            "\n0\\.1\\.0\n.*",
            "{src_dir}/CHANGELOG.rst.base.txt", "\n")
        s = "COPYRIGHT\n"
        for fn in ["{dest_dir}/README", "{dest_dir}/README.rst",
                   "{dest_dir}/docs/README.rst", ]:
            self._re_mutate(
                fn, "^PURPOSE\n.*?\n" + s, "{src_dir}/README.part.rst", '', s)
        for fn in ["{dest_dir}/setup.py", ]:
            _re_mutate2(
                fn, "include_package_data=True,",
                prefix="include_package_data=True,\n    " +
                "package_data={'': ['data/templates/*.jinja']}," +
                "\n    scripts=['rebookmaker/rebookmaker'],"
                )

        req_bn = "requirements.txt"
        req_fn = "{src_dir}/" + req_bn
        dest_req_fn = "{dest_dir}/" + req_bn
        self._dest_append(req_bn)
        self._dest_append("MANIFEST.in")
        for fn in self._src_glob("rebookmaker/data/templates/*.jinja"):
            self._dest_append(fn)

        def _reqs_mutate(fn_proto):
            fn = self._myformat(fn_proto)
            txt = self._slurp(fn)
            d = {}
            for line in txt.split("\n"):
                if 0 == len(line):
                    continue
                m = re.match("\\A([A-Za-z0-9_\\-]+)>=([0-9\\.]+)\\Z", line)
                if m:
                    req = m.group(1)
                    ver = m.group(2)
                else:
                    req = line
                    ver = '0'
                if ver == '0':
                    if req not in d:
                        d[req] = '0'
                else:
                    if req not in d or d[req] == '0':
                        d[req] = ver
                    else:
                        raise BaseException(
                            "mismatch reqs: {} {} {}".format(req, ver, d[req]))
            txt = "".join(sorted([
                x + ('' if v == '0' else '>='+v) + "\n"
                for x, v in d.items()]))
            with open(fn, "wt") as ofh:
                ofh.write(txt)
        _reqs_mutate(dest_req_fn)

        for fn in self._src_glob("tests/test*.py"):
            self._dest_append(fn, make_exe=True)
        self._dest_append("rebookmaker/rebookmaker", make_exe=True)
        with open(self._myformat("{dest_dir}/tox.ini"), "wt") as ofh:
            ofh.write(
                "[tox]\nenvlist = py38\n\n" +
                "[testenv]\ndeps =" + "".join(
                    ["\n\t" + x for x in
                     self._fmt_slurp(req_fn).split("\n")]) + "\n" +
                "\ncommands = pytest\n")

    def command__test(self):
        check_call(["bash", "-c",
                    self._myformat("cd {dest_dir} && {tox_cmd}")])

    def command__install(self):
        self.command__build()
        check_call(["bash", "-c", self._myformat(
            "cd {dest_dir} && pip install --user --upgrade ."
        )])

    def command__release(self):
        self.command__build()
        check_call(["bash", "-c", self._myformat(
            "cd {dest_dir} && python3 setup.py sdist " +
            " && twine check dist/{dist_name}*.tar.gz " +
            " && twine upload --verbose dist/{dist_name}*.tar.gz")])

    def command__gen_travis_yaml(self):
        import yaml

        with open("travis.yml", "wt") as f:
            f.write(yaml.dump({
                'install':
                [
                    'pip install -U pip',
                    'pip install cookiecutter',
                    'pip --version',
                    self._myformat(
                        '( cd {base_dir} && ' +
                        'python3 python_pypi_dist_manager.py build_only )'),
                    self._myformat(
                        '( cd {base_dir} && ' +
                        'cat {dest_dir}/requirements.txt )'),
                    self._myformat(
                        '( cd {base_dir} && cd {dest_dir} && ' +
                        'pip install -r requirements.txt && pip install . )')
                ],
                'script': [
                    self._myformat(
                        '( cd {base_dir} && cd {dest_dir} && ' +
                        'py.test --cov {dist_name} ' +
                        '--cov-report term-missing tests/ )')
                ],
                'language': 'python',
                'python': ['3.5', '3.6', '3.7', '3.8', 'pypy3', ],
                }))

    def run_command(self, cmd, args):
        if cmd == 'travis':
            obj.command__gen_travis_yaml()
        elif cmd == 'build':
            obj.command__build()
        elif cmd == 'build_only':
            obj.command__build_only()
        elif cmd == 'install':
            obj.command__install()
        elif cmd == 'release':
            obj.command__release()
        elif cmd == 'test':
            obj.command__build()
        else:
            raise BaseException("Unknown sub-command")


try:
    cmd = sys.argv.pop(1)
except IndexError:
    cmd = 'build'

dist_name = "rebookmaker"

obj = DistGenerator(
    dist_name=dist_name,
    dist_version="0.8.0",
    project_name="rebookmaker",
    project_short_description="EPUB generator",
)
obj.run_command(cmd=cmd, args=[])
