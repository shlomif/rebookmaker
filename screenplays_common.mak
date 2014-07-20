DOCS_SCREENPLAY_TEXT = $(patsubst %,%.screenplay-text.txt,$(DOCS_BASE))
DOCS_SCREENPLAY_XML = $(patsubst %,%.screenplay-xml.xml,$(DOCS_BASE))
DOCS_SCREENPLAY_XHTML = $(patsubst %,%.screenplay-text.xhtml,$(DOCS_BASE))
DOCS_SCREENPLAY_XHTML_AS_HTML = $(patsubst %,%.final.html,$(DOCS_BASE))
DOCS_SCREENPLAY_FO = $(patsubst %,%.screenplay-text.fo,$(DOCS_BASE))
DOCS_SCREENPLAY_RTF = $(patsubst %,%.screenplay-text.rtf,$(DOCS_BASE))

DOCBOOK5_XSL_STYLESHEETS_PATH := $(HOME)/Download/unpack/file/docbook/docbook-xsl-ns-snapshot

HOMEPAGE := $(HOME)/Docs/homepage/homepage/trunk
DOCBOOK5_XSL_STYLESHEETS_XHTML_PATH := $(DOCBOOK5_XSL_STYLESHEETS_PATH)/xhtml
DOCBOOK5_XSL_STYLESHEETS_FO_PATH := $(DOCBOOK5_XSL_STYLESHEETS_PATH)/fo
DOCBOOK5_XSL_CUSTOM_XSLT_STYLESHEET := $(HOMEPAGE)/lib/sgml/shlomif-docbook/xsl-5-stylesheets/shlomif-essays-5-xhtml-onechunk.xsl
DOCBOOK5_XSL_CUSTOM_FO_XSLT_STYLESHEET := $(HOMEPAGE)/lib/sgml/shlomif-docbook/xsl-5-stylesheets/shlomif-essays-5-fo.xsl

ENG_EPUB = $(patsubst %,%.epub,$(DOCS_BASE))

EPUB_SCRIPT = scripts/prepare-epub.pl

FILES = Makefile $(DOCS_SCREENPLAY_XHTML) \
		$(DOCS_SCREENPLAY_TEXT) \
		style.css style-heb.css \
		README.html

