# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAPI     = sphinx-apidoc
APIEXCLUDES   = ../usrp_client/tests/
SPHINXPROJ    = UsrpUhdApi
SOURCEDIR     = .
BUILDDIR      = _build
APISOURCE	  = ../usrp_client ../uhd_wrapper/utils/
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
