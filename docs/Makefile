# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAPI     = sphinx-apidoc
APIEXCLUDES   = ../examples ../uhd_wrapper/3rdparty/ ../uhd_wrapper/build/ ../uhd_wrapper/debug/ ../uhd_wrapper/hardware_tests/ ../uhd_wrapper/include/ ../uhd_wrapper/lib/ ../uhd_wrapper/snippets/ ../uhd_wrapper/tests/ ../usrp_client/tests/ ../*.py
SPHINXPROJ    = UsrpUhdApi
SOURCEDIR     = .
BUILDDIR      = _build
APISOURCE	  = ../
# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

all: api html
.PHONY: all

api:
	$(SPHINXAPI) -f -o "$(SOURCEDIR)" "$(APISOURCE)" "$(APIEXCLUDES)"
.PHONY: api

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
