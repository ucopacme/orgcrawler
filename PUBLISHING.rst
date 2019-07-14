Steps for Publishing this Package to PyPI
=========================================

Follow these steps to build and upload the package to PyPI.  For more info,
visit https://packaging.python.org/tutorials/packaging-projects


Prerequisites
-------------

- You must have access rights to post to both ``test.pypi.org`` and ``pypi.org``
- Your python environment must have the latest updates to the required tools::

  > pip install -U pip setuptools wheel twine


Build the new release
---------------------

After merging a pull request on Github:

1. Pull the new commits into your local master branch::

     > git checkout master
     > git pull ucopacme master

#. Create a git tag for the new release::

     > git tag -ln | tail -1
     1.0.0a4         Alpha Release 1.0.0a4
     > git tag -am'Alpha Release 1.0.0a5'  1.0.0a5


#. Edit ``setup.py`` and update the ``VERSION`` parameter to the new tag::

     > git diff setup.py
      
     -VERSION = '1.0.0a4'
     +VERSION = '1.0.0a5'
   
#. Commit and push to master on github along with the new tag::

     > git commit -am 'release 1.0.1a5'
     [master 04c3946] release 1.0.1a5
     > git push ucopacme master --tags
     To github.com:ucopacme/orgcrawler.git
        0035e5f..04c3946  master -> master
      * [new tag]         1.0.0a5 -> 1.0.0a5

#. Build a distributable package with the ``setup.py`` script::

     > rm -rf dist/*
     > python setup.py sdist bdist_wheel
     > ls -1 dist/
     orgcrawler-1.0.0a5-py3-none-any.whl
     orgcrawler-1.0.0a5.tar.gz


Validate distribution
---------------------

#. Upload the new dist to the test PyPI site::

     > twine upload --repository-url https://test.pypi.org/legacy/ dist/*
     Enter your username: agould
     Enter your password: ************
     Uploading distributions to https://test.pypi.org/legacy/
     Uploading orgcrawler-1.0.0a4-py3-none-any.whl
     Uploading orgcrawler-1.0.0a5-py3-none-any.whl

#. Visit ``test.pypi.org`` and verify your release: https://test.pypi.org/project/orgcrawler/

#. Install the package into a clean python virtual environment::

     > python -m venv package-test
     > source package-test/bin/activate
     > pip install --index-url https://test.pypi.org/simple/ --no-deps orgcrawler
     Looking in indexes: https://test.pypi.org/simple/
     Collecting orgcrawler
     Successfully installed orgcrawler-1.0.0a5

#. Verify the install::

     > pip show orgcrawler 
     Name: orgcrawler
     Version: 1.0.0a5
     Summary: Tools for working with AWS Organizations
     Home-page: https://github.com/ucopacme/orgcrawler


Publish to public PyPI
----------------------

#. Upload to real PyPI site::

     > twine upload dist/*
     Enter your password: 
     Uploading distributions to https://upload.pypi.org/legacy/
     Uploading orgcrawler-1.0.0a5-py3-none-any.whl
     Uploading orgcrawler-1.0.0a5.tar.gz

#. Visit ``pypi.org`` and verify your release: https://pypi.org/project/orgcrawler/
