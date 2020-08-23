PURPOSE
-------

rebookmaker - an open source (MIT-licensed) re-implementation of
Marcelo Lira’s ( @setanta ) ebookmaker.

It converts an EPUB definition inside a JSON file along with
some input HTML and image files into an .epub.

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

Since "ebookmaker" was taken on pypi and it is common courtesy to
change the name, I picked "rebookmaker" since it was available
on pypi and as a pun on `reboots in fiction <https://en.wikipedia.org/wiki/Reboot_%28fiction%29>`
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
