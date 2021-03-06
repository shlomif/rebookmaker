PURPOSE
-------

rebookmaker - an open source (MIT-licensed) re-implementation of
Marcelo Lira’s ( @setanta ) ebookmaker.

EPUB is a popular and open file format standard for electronic books (see
https://en.wikipedia.org/wiki/EPUB for more information about it). What
rebookmaker (= "re-ebook-maker") does is compile a definition of the
book inside a JSON file along with some input HTML and image files into an
.epub.

See:

* https://github.com/setanta/ebookmaker/ - does not have an explicit
  licence, which prompted this re-implementation.
* https://pypi.org/project/ebookmaker/ - GPLv3 by Project Gutenberg and
  incompatible with @setanta 's .

INSTALLATION
------------

pip3 install rebookmaker

NOTES
-----

Since the name "ebookmaker" was taken on pypi and it is common courtesy to
change the name, I picked "rebookmaker" since it was available
on pypi and as a pun on `reboots in fiction <https://en.wikipedia.org/wiki/Reboot_%28fiction%29>`_
because it was a rewrite.

The issue where I requested an explicit licensing of the original
project is here:
https://github.com/setanta/ebookmaker/issues/8 but I have yet to receive a reply.

You can find some examples for valid input by perusing the code in
https://github.com/shlomif/screenplays-common and
https://github.com/shlomif/shlomi-fish-homepage . Preparing some less
generic examples is on my TODO list.

This project aims for compatibility with setanta's project, but some functionality
may be still missing and I also added some new one.

Samples:
--------

* https://github.com/shlomif/english-humanity-the-movie-rebookmaker-example - under CC-BY-SA.

Similar Projects:
-----------------

* http://docbook.sourceforge.net/release/xsl/current/epub/README - DocBook 5 can be
  converted to EPUB.
* https://github.com/shlomif/cookiecutter--shlomif-latemp-sites - contains some custom XSLT
  stylesheets for reproducible builds and other features.
* https://pypi.org/project/ebookmaker/ - by Project Gutenberg: accepts a different input.
* https://packages.debian.org/source/sid/strip-nondeterminism - allow for reproducible
  builds EPUBs.

