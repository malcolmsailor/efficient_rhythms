EFFRHY_SOURCE_FILES = $(wildcard ../src/er*.py)
EFFRHY = ../efficient_rhythms.py $(EFFRHY_SOURCE_FILES)

# TODO these patterns will not match more than one digit.
EXAMPLE_SRC = $(wildcard examples/example[0-9].py)
EXAMPLE_MID = $(EXAMPLE_SRC:examples/%.py=examples/midi/%.mid)
EXAMPLE_M4A = $(EXAMPLE_SRC:examples/%.py=resources/m4as/%.m4a)
EXAMPLE_SVG = $(EXAMPLE_SRC:examples/%.py=resources/svgs/%.svg)
EXAMPLE_PNG = $(EXAMPLE_SRC:examples/%.py=resources/pngs/%_00001.png)

HARMONY_EXAMPLE_SRC = $(wildcard examples/harmony_example[0-9].py)
HARMONY_EXAMPLE_MID = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=examples/midi/%.mid)
HARMONY_EXAMPLE_SVG = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=resources/svgs/%.svg)
HARMONY_EXAMPLE_PNG = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=resources/pngs/%_00001.png)

CSS_FILES = $(resources/third_party/github-markdown-css/github-markdown.css \
	resources/markdown-body.css)

.PHONY: all clean clean_m4as clean_pngs clean_svgs clean_midi

all: midi pngs svgs html
	$(info You may wish to run 'make m4as' as well; 'make all' does not build \
		these because they take exceptionally long.)



########
# SVGs #
########

svgs: $(EXAMPLE_SVG) $(HARMONY_EXAMPLE_SVG)

resources/svgs/example%.svg: examples/example%.py \
		examples/example_base.py $(EFFRHY)
	python3 ../efficient_rhythms.py --settings examples/example_base.py $< \
        --verovio-arguments "--page-height 450" --no-interface \
        --output-notation svg
	mv examples/midi/example$*.svg resources/svgs/example$*.svg

########
# MIDI #
########

midi: $(EXAMPLE_MID) $(HARMONY_EXAMPLE_MID)

# This recipe *also* builds the associated SVG file and moves it into place
examples/midi/example%.mid: examples/example%.py \
		examples/example_base.py $(EFFRHY)
	python3 ../efficient_rhythms.py --settings examples/example_base.py $< \
        --verovio-arguments "--page-height 450" --no-interface \
        --output-notation svg
	mv examples/midi/example$*.svg resources/svgs/example$*.svg


# This recipe *also* builds the associated SVG file and moves it into place
examples/midi/harmony_example%.mid: examples/harmony_example%.py \
		examples/harmony_example_base.py $(EFFRHY)
	python3 ../efficient_rhythms.py --settings \
		examples/harmony_example_base.py $< \
        --verovio-arguments "--page-height 600" --no-interface \
        --output-notation svg
	mv examples/midi/harmony_example$*.svg \
		resources/svgs/harmony_example$*.svg

########
# PNGs #
########

pngs: $(EXAMPLE_PNG) $(HARMONY_EXAMPLE_PNG)

# expects to find path to midani.py in an environment variable called MIDANI
# filter-out trick from https://stackoverflow.com/a/12284855/10155119
resources/pngs/%_00001.png: examples/midi/%.mid \
		resources/midani/example_midani_settings.py \
		resources/midani/stationary_midani_settings.py \
		resources/midani/%_midani_settings.py
	python3 "$(MIDANI)" --settings $(filter-out $<,$^) --frames 2

########
# M4As #
########

m4as: $(EXAMPLE_M4A)

# next recipe expects to find pygmid2aud.py in the path
resources/m4as/%.m4a: examples/midi/%.mid
	pygmid2aud.py $< --overwrite --output-path $@


#########
# CLEAN #
#########

clean_svgs:
	trash resources/svgs/*.svg

clean_m4as:
	trash resources/m4as/*.m4a

clean_pngs:
	trash resources/pngs/*.png

clean_midi:
	trash examples/midi/*.mid

clean: clean_pngs clean_svgs clean_midi # clean_m4as

########
# HTML #
########

# Also builds associated markdown files

html: settings.html general.html

settings.html : resources/get_settings_md_and_html.py ../src/er_settings.py \
		$(CSS_FILES)
	python3 $<

general.html : resources/get_general_md_and_html.py \
		resources/general_pandoc.md $(CSS_FILES)
	python3 $<
