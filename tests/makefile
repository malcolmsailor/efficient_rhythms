# This makefile is in charge of running tests that are best not run with pytest

EFFRHY_SOURCE_FILES = $(wildcard ../src/er*.py)
EFFRHY = ../efficient_rhythms.py $(EFFRHY_SOURCE_FILES)

.PHONY: all tests

all: tests

tests: .last_ran_test_interface

.last_ran_%: %.py $(EFFRHY)
	python3 $<
	touch $@
