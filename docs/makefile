# This makefile assumes that efficient_rhythms is installed with pip as a
# module (so that py -m efficient_rhythms works)

EFFRHY = $(shell find ../efficient_rhythms -type f -name '*.py')

EXAMPLE_SRC = $(shell fd '^example[0-9]+\.py$$' examples)
EXAMPLE_MID = $(EXAMPLE_SRC:examples/%.py=examples/midi/%.mid)
EXAMPLE_M4A = $(EXAMPLE_SRC:examples/%.py=resources/m4as/%.m4a)
EXAMPLE_SVG = $(EXAMPLE_SRC:examples/%.py=resources/svgs/%.svg)
EXAMPLE_PNG = $(EXAMPLE_SRC:examples/%.py=resources/pngs/%_00001.png)

HARMONY_EXAMPLE_SRC = $(shell fd '^harmony_example[0-9]+\.py$$' examples)
HARMONY_EXAMPLE_MID = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=examples/midi/%.mid)
HARMONY_EXAMPLE_M4A = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=resources/m4as/%.m4a)
HARMONY_EXAMPLE_SVG = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=resources/svgs/%.svg)
HARMONY_EXAMPLE_PNG = \
	$(HARMONY_EXAMPLE_SRC:examples/%.py=resources/pngs/%_00001.png)

RHYTHM_EXAMPLE_SRC = $(shell fd '^rhythm_example[0-9]+.*\.py$$' examples)
RHYTHM_EXAMPLE_MID = \
	$(RHYTHM_EXAMPLE_SRC:examples/%.py=examples/midi/%.mid)
RHYTHM_EXAMPLE_M4A = \
	$(RHYTHM_EXAMPLE_SRC:examples/%.py=resources/m4as/%.m4a)
RHYTHM_EXAMPLE_SVG = \
	$(RHYTHM_EXAMPLE_SRC:examples/%.py=resources/svgs/%.svg)
RHYTHM_EXAMPLE_PNG = \
	$(RHYTHM_EXAMPLE_SRC:examples/%.py=resources/pngs/%_00001.png)

RHYTHM_EXAMPLES_NO_NOTATION =$(filter %example5.py %example6.py \
	%example11.py %example12.py, $(RHYTHM_EXAMPLE_SRC))


CSS_FILES = $(resources/third_party/github-markdown-css/github-markdown.css \
	resources/css/markdown-body.css)

SVG_HEIGHT_1 := 250
SVG_HEIGHT_2 := 450
SVG_HEIGHT_3 := 600
SVG_HEIGHT_4 := 750

.PHONY: all clean clean_m4as clean_pngs clean_svgs clean_midi

all: midi pngs svgs html
	$(info You may wish to run 'make m4as' as well; 'make all' does not build \
		these because they take exceptionally long.)



########
# SVGs #
########

svgs: midi

# svgs: $(EXAMPLE_SVG) $(HARMONY_EXAMPLE_SVG) $(RHYTHM_EXAMPLE_SVG)
#
# resources/svgs/example%.svg: examples/example%.py \
# 		examples/example_base.py $(EFFRHY)
# 	python3 -m efficient_rhythms --settings examples/example_base.py $< \
#         --verovio-arguments "--page-height 450" --no-interface \
#         --output-notation svg
# 	mv examples/midi/example$*.svg resources/svgs/example$*.svg

########
# MIDI #
########

midi: $(EXAMPLE_MID) $(HARMONY_EXAMPLE_MID) $(RHYTHM_EXAMPLE_MID)

# it would be nice to consolidate these rules into one if possible!

# This recipe *also* builds the associated SVG file and moves it into place
# SVG_HEIGHT was 450. TODO verify
examples/midi/example%.mid: examples/example%.py \
		examples/example_base.py $(EFFRHY)
	$(eval SVG_HEIGHT = $(SVG_HEIGHT_$(shell \
			resources/scripts/get_n_voices.sh examples/example_base.py $<)))
	python3 -m efficient_rhythms --settings examples/example_base.py $< \
        --verovio-arguments "--page-height $(SVG_HEIGHT)" --no-interface \
        --output-notation svg
	mv examples/midi/example$*.svg resources/svgs/example$*.svg


# This recipe *also* builds the associated SVG file and moves it into place
# SVG_HEIGHT was 600. TODO verify
examples/midi/harmony_example%.mid: examples/harmony_example%.py \
		examples/harmony_example_base.py $(EFFRHY)
	$(eval SVG_HEIGHT = $(SVG_HEIGHT_$(shell \
			resources/scripts/get_n_voices.sh \
			examples/harmony_example_base.py $<)))
	python3 -m efficient_rhythms --settings \
		examples/harmony_example_base.py $< \
        --verovio-arguments "--page-height $(SVG_HEIGHT)" --no-interface \
        --output-notation svg
	mv examples/midi/harmony_example$*.svg \
		resources/svgs/harmony_example$*.svg

# This recipe *also* builds the associated SVG file and moves it into place
examples/midi/rhythm_example%.mid: examples/rhythm_example%.py \
		examples/rhythm_example_base.py $(EFFRHY)
	$(eval match=$(filter $(<), $(RHYTHM_EXAMPLES_NO_NOTATION)))
	$(eval SVG_HEIGHT = $(SVG_HEIGHT_$(shell \
			resources/scripts/get_n_voices.sh \
			examples/rhythm_example_base.py $<)))
	if ! [[ -z "$(match)" ]] ; \
	then \
		python3 -m efficient_rhythms --settings \
			examples/rhythm_example_base.py $< \
        	--no-interface ; \
	else \
		python3 -m efficient_rhythms --settings \
			examples/rhythm_example_base.py $< \
			--verovio-arguments "--page-height $(SVG_HEIGHT)" --no-interface \
			--output-notation svg ; \
		mv examples/midi/rhythm_example$*.svg \
			resources/svgs/rhythm_example$*.svg ; \
	fi;



########
# PNGs #
########

pngs: $(EXAMPLE_PNG) $(HARMONY_EXAMPLE_PNG) $(RHYTHM_EXAMPLE_PNG)

# expects to find path to midani.py in an environment variable called MIDANI
# filter-out trick from https://stackoverflow.com/a/12284855/10155119
resources/pngs/%_00001.png: examples/midi/%.mid \
		resources/midani/example_midani_settings.py \
		resources/midani/stationary_midani_settings.py \
		resources/midani/%_midani_settings.py
	python3 "$(MIDANI)" --settings $(filter-out $<,$^) --frames 3

########
# M4As #
########

m4as: $(EXAMPLE_M4A) $(HARMONY_EXAMPLE_M4A) $(RHYTHM_EXAMPLE_M4A)

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

html: settings.html index.html constants.html

settings.html : resources/scripts/get_settings_md_and_html.py \
		../efficient_rhythms/er_settings.py $(CSS_FILES)
	python3 $<

constants.html : resources/scripts/get_constants.py ../efficient_rhythms/er_constants.py \
		$(CSS_FILES)
	python3 $<

index.html : resources/scripts/get_index_md_and_html.py \
		resources/markdown/index_pandoc.md $(CSS_FILES)
	python3 $<
	git add $@
	git add index.md
