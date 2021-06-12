# This makefile is in charge of running tests that are best not run with pytest

EFFRHY = $(shell find ../efficient_rhythms -type f -name '*.py')
TEST_SETTINGS = $(shell find test_settings -type f -name '*.py')

.PHONY: all tests

all: tests

tests: .last_ran_test_interface .last_ran_test_settings

.last_ran_test_settings: test_settings.sh $(EFFRHY)  $(TEST_SETTINGS)
	./test_settings.sh
	touch $@

.last_ran_%: %.py $(EFFRHY)
	python3 $<
	touch $@
