# Purpose {#mainpage}

CoRoLa Repository Template for  C++ projects.

It contains:

- `clang-format`: file that contains information necessary to auto-format your code
  - `CMakeLists.txt` can be used to format all files according to `clang-format`, by creating a custom target `fake`
  - `pre-commit` hook for automatically formatting the files to be committed
- a skeleton `README.md`
- the unit-test header-only framework `catch2` and the header-only mocking framework `trompeloeil`
  - the headers can be found in the  `3rdparty` directory
  - a skeleton CMakeLists.txt and a test_skeleton for running a simple unit test can be found in `tests`
- a `Doxyfile` indicating preliminary configurations
  
# Installation

1. Download the `.zip` file of this repository.
2. Unzip
3. rename unzipped repository accordingly
4. `cd <repo>`
5. `git init`
6. `git add . & git commit -m "initial commit"`
7. `git remote add origin <the gitlab project adrdress>`
8. `git push -u master`

# Use

- `mkdir build && cd build && cmake ..`
- `make`
- `make format` to apply clang-format
- `make test` to run the tests
- `make doxygen` to generate doxygen

# Related Documents

- [Documentation on `clang-format`](ClangFormatDoc.md)

# Requirements

- `clang-format version 6.0`
  - Ubuntu 18.04: `sudo apt update && sudo apt install clang-format`
  - Windows: Using Visual Studio 2017 and later, clang-format is automatically installed

**Optional (required for documentation):**
- `doxygen >= 1.8.16` from doxygen homepage
- `graphviz`

# References

- [catch2 documentation](https://github.com/catchorg/Catch2/blob/v2.9.2/docs/tutorial.md)
- [internal mocking framework evaluation](https://barkhauseninstitut.sharepoint.com/sites/BILab/Ablage/Forms/AllItems.aspx?id=%2Fsites%2FBILab%2FAblage%2FHowTos%2F2019%2D07%2D25%20TDD%20Frameworks%2Epdf&parent=%2Fsites%2FBILab%2FAblage%2FHowTos) including the documentation of trompeloeil
- [doxygen documentation](http://www.doxygen.nl/manual/docblocks.html)
