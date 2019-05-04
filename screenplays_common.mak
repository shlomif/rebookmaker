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

all: $(DOCS_SCREENPLAY_XHTML) $(ENG_XHTML) $(ENG_HTML_FOR_OOO)

upload:
	rsync -v --progress -a $(FILES) $${HOMEPAGE_SSH_PATH}/$(SELINA_UPLOAD_TEMP_DEST)/

$(DOCS_SCREENPLAY_XML): %.screenplay-xml.xml: %.screenplay-text.txt
	perl -MXML::Grammar::Screenplay::App::FromProto -e 'run()' -- \
	-o $@ $<

$(DOCS_SCREENPLAY_XHTML): %.screenplay-text.xhtml: %.screenplay-xml.xml
	perl -MXML::Grammar::Screenplay::App::ToHTML -e 'run()' -- \
		-o $@ $<
	perl -i -lap -e 's/ +$$//' $@
	perl -i -0777 -lp -E 's/(\?>)/$$1\n<!DOCTYPE html>/ if not /<!DOCTYPE/' $@

$(DOCS_SCREENPLAY_XHTML_AS_HTML): $(DOCS_SCREENPLAY_XHTML)
	cp -f $< $@

$(DOCS_SCREENPLAY_FO): %.screenplay-text.fo : %.db5.xml
	xsltproc --stringparam root.filename $@ \
		--stringparam html.stylesheet "style.css" \
		--path $(DOCBOOK5_XSL_STYLESHEETS_FO_PATH) \
		-o $@ \
		$(DOCBOOK5_XSL_CUSTOM_FO_XSLT_STYLESHEET) $<

$(DOCS_SCREENPLAY_RTF): %.rtf: %.fo
	fop -fo $< -rtf $@

rtf: $(DOCS_SCREENPLAY_RTF)

$(ENG_HTML_FOR_OOO): $(ENG_XHTML)
	cat $< | perl -lne 'print unless m{\A<\?xml}' > $@

$(HEB_HTML_FOR_OOO): $(DOCS_SCREENPLAY_XHTML)
	cat $< | perl -lne 's{(</title>)}{$${1}<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />}; print unless m{\A<\?xml}' > $@

oohtml: $(ENG_HTML_FOR_OOO) $(HEB_HTML_FOR_OOO)

openoffice: oohtml
	ooffice3.2 $(ENG_HTML_FOR_OOO)

.PHONY: epub_ff

epub: $(ENG_EPUB)

$(ENG_EPUB): $(patsubst %.epub,%.screenplay-text.xhtml,$(ENG_EPUB)) $(EPUB_SCRIPT)
	for f in $@ ; do perl -I "$(SCREENPLAY_COMMON_INC_DIR)" $(EPUB_SCRIPT) --output "$$f" "$${f%%.epub}.screenplay-text.xhtml" || exit -1 ; done

epub_ff: epub
	firefox $(ENG_EPUB)

epub_ok: epub
	okular $(ENG_EPUB)

clean:
	rm -f $(DOCS_SCREENPLAY_XHTML) $(DOCS_SCREENPLAY_XML)

%.show:
	@echo "$* = $($*)"

linview: $(DOCS_SCREENPLAY_XHTML_AS_HTML)
	xdg-open $<

test: all
	prove tests/*.t

runtest: all
	runprove tests/*.t
