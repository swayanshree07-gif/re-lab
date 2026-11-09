DIST ?= ../../dist
NAME := 27-cpp-vtables
CXX ?= g++
CXXFLAGS ?= -O0 -g0 -Wall -Wextra

$(DIST)/$(NAME): src/main.cpp src/params.h
	@mkdir -p $(DIST)
	$(CXX) $(CXXFLAGS) -o $@ $<

.PHONY: clean
clean:
	rm -f $(DIST)/$(NAME)
