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
