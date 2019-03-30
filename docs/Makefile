# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = OrgCrawler
SOURCEDIR     = .
BUILDDIR      = _build
APIDOCBUILD      = sphinx-apidoc
APIDOCHEADER     = 'OrgCrawler API'
APIDOCBUILDDIR   = $(SOURCEDIR)/_api
APIDOCSOURCEDIR  = ../orgcrawler

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

apidoc:
	@rm -r $(APIDOCBUILDDIR)
	@$(APIDOCBUILD) -H $(APIDOCHEADER) -M -e -o $(APIDOCBUILDDIR) $(APIDOCSOURCEDIR)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
#%: apidoc Makefile
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
