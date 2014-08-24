FILES = Makefile $(DOCS_FICTION_XHTML) \
		$(DOCS_FICTION_TEXT) $(DOCS_FICTION_DB5) \
		$(ENG_DB_PROCESSED) $(ENG_DB_SOURCE) \
		style.css style-heb.css \
		README.html

ENG_EPUB = $(ENG_STORY).epub

STORY_LANGUAGE_BASES = $(HEB_STORY) $(ENG_STORY)

FICTION_TEXTS ?= $(STORY_LANGUAGE_BASES)

DOCS_FICTION_TEXT = $(patsubst %,%.fiction-text.txt,$(FICTION_TEXTS))
DOCS_FICTION_XML = $(patsubst %,%.fiction-xml.xml,$(FICTION_TEXTS))
DOCS_FICTION_DB5 = $(patsubst %,%.db5.xml,$(STORY_LANGUAGE_BASES))
DOCS_FICTION_XHTML = $(patsubst %,%.fiction-text.xhtml,$(STORY_LANGUAGE_BASES))
DOCS_FICTION_FO = $(patsubst %,%.fiction-text.fo,$(STORY_LANGUAGE_BASES))
DOCS_FICTION_RTF = $(patsubst %,%.fiction-text.rtf,$(STORY_LANGUAGE_BASES))
DOCS_FICTION_ODT = $(patsubst %,%.odt,$(STORY_LANGUAGE_BASES))
DOCS_FICTION_HTML_FOR_OOO = $(patsubst %,%.for-openoffice.html,$(STORY_LANGUAGE_BASES))

ENG_DB_PROCESSED = $(ENG_STORY).db5.xml

ENG_DB_XSLT = docbook-epub-preproc.xslt
ENG_DB_SOURCE = $(ENG_STORY).db5.xml

ENG_EPUB_XSLT = $(ENG_DB_XSLT)

DOCBOOK5_XSL_STYLESHEETS_PATH := $(HOME)/Download/unpack/file/docbook/docbook-xsl-ns-snapshot

HOMEPAGE := $(HOME)/Docs/homepage/homepage/trunk
DOCBOOK5_XSL_STYLESHEETS_XHTML_PATH := $(DOCBOOK5_XSL_STYLESHEETS_PATH)/xhtml
DOCBOOK5_XSL_STYLESHEETS_FO_PATH := $(DOCBOOK5_XSL_STYLESHEETS_PATH)/fo
DOCBOOK5_XSL_CUSTOM_XSLT_STYLESHEET := $(HOMEPAGE)/lib/sgml/shlomif-docbook/xsl-5-stylesheets/shlomif-essays-5-xhtml-onechunk.xsl
DOCBOOK5_XSL_CUSTOM_FO_XSLT_STYLESHEET := $(HOMEPAGE)/lib/sgml/shlomif-docbook/xsl-5-stylesheets/shlomif-essays-5-fo.xsl

all: $(DOCS_FICTION_XHTML) $(ENG_EPUB) $(ENG_HTML_FOR_OOO)

odt: $(DOCS_FICTION_ODT)

upload:
	rsync -v --progress -a $(FILES) $${HOMEPAGE_SSH_PATH}/$(THE_ENEMY_DEST)/

$(DOCS_FICTION_XML): %.fiction-xml.xml: %.fiction-text.txt
	perl -MXML::Grammar::Fiction::App::FromProto -e 'run()' -- \
	-o $@ $< && \
	perl -i -lape 's/\s+$$//' $@

DOCS_FICTION_XHTML__HEB = $(filter %-hebrew.fiction-text.xhtml,$(DOCS_FICTION_XHTML))
DOCS_FICTION_XHTML__ENG = $(filter %-english.fiction-text.xhtml,$(DOCS_FICTION_XHTML))

$(DOCS_FICTION_XHTML__HEB): %.fiction-text.xhtml: %.db5.xml
	xsltproc --stringparam root.filename $@ \
		--stringparam html.stylesheet "style-heb.css" \
		--path $(DOCBOOK5_XSL_STYLESHEETS_XHTML_PATH) \
		-o $@ \
		$(DOCBOOK5_XSL_CUSTOM_XSLT_STYLESHEET) $< && \
	mv -f $@.html $@ && \
	perl -i -lape 's/\s+$$//' $@

$(DOCS_FICTION_XHTML__ENG): %.fiction-text.xhtml: %.db5.xml
	xsltproc --stringparam root.filename $@ \
		$(TO_XHTML_XSLT_COMMON_PARAMS) \
		--path $(DOCBOOK5_XSL_STYLESHEETS_XHTML_PATH) \
		-o $@ \
		$(DOCBOOK5_XSL_CUSTOM_XSLT_STYLESHEET) $< && \
	mv -f $@.html $@ && \
	perl -i -lape 's/\s+$$//' $@

$(DOCS_FICTION_FO): %.fiction-text.fo : %.db5.xml
	xsltproc --stringparam root.filename $@ \
		--stringparam html.stylesheet "style-heb.css" \
		--path $(DOCBOOK5_XSL_STYLESHEETS_FO_PATH) \
		-o $@ \
		$(DOCBOOK5_XSL_CUSTOM_FO_XSLT_STYLESHEET) $<

$(DOCS_FICTION_RTF): %.rtf: %.fo
	fop -fo $< -rtf $@

rtf: $(DOCS_FICTION_RTF)

$(DOCS_FICTION_ODT): $(DOCS_FICTION_DB5)
	docbook2odf $< -o $@

# DOCBOOK_RNG = http://www.docbook.org/xml/5.0/rng/docbook.rng

DOCBOOK_RNG = ./rng/docbook.rng

JING = jing $(DOCBOOK_RNG)

# XSL_SNAPSHOT_HOME = $(HOME)/Download/unpack/file/docbook/docbook-xsl-ns-snapshot
XSL_SNAPSHOT_HOME = $(HOME)/Download/unpack/file/docbook/docbook-xsl-snapshot/

EPUB_SCRIPT = $(XSL_SNAPSHOT_HOME)/epub/bin/dbtoepub


