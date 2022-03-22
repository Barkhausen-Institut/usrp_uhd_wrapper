# Purpose of `clang-format`

[`clang-format`](https://dev.to/sandordargo/how-to-automatically-format-your-c-code-regardless-the-ide-you-use-2pm2) is a tool to automatically apply a set of rules to auto-format your code. The rules are defined in the `clang-format` file. It can be found in this repository.

If you want to "change the rules", open the `clang-format` file and click on the respective links in the first comment.

# Use

## Recommended: Format from Command-Line

The toplevel `CMakeLists.txt` defines via `add_custom_target()` a target that is callable by `make format`. **It can only be created, if there are files that can actually be formatted.** By default, it formats these files:

- `${CMAKE_SOURCE_DIR}/src/*.cpp`
- `${CMAKE_SOURCE_DIR}/include/*.hpp`
- `${CMAKE_SOURCE_DIR}/include/*.h`
- `${CMAKE_SOURCE_DIR}/tests/*.cpp`
- `${CMAKE_SOURCE_DIR}/tests/*.h`

Further files may be added.

Use (on Ubuntu): 

1. `mkdir build && cd build`
2. `cmake .. `
3. `make format`

Use (on Windows):

1. `mkdir build && cd build `
2. `cmake -G "NMake Makefiles" ..`
3. `nmake format`
   
## Use from command-line

- `clang-format -i <file> -style=file -assume-filename=<path/to/clang-format-file>`, cf. [here](https://clang.llvm.org/docs/ClangFormat.html) or simply call `clang-format -h`
- for recursive updates, the bash command is `find <parent_dir>/ -iname *.hpp -o -iname *.cpp | xargs clang-format -i -assume-filename=<apth_to_clang_format>`

## Later: Incorporate the formatting into each `git commit`

As soon as we agreed on a general formatting style, we can think of incorporating the formatting into each commit. That mean, before git commits the changes, it performs the formatting based on the rules defined in `clang-format`.
  
This can be achieved by using [git hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks).
An example file, `pre-commit`, can be found in the folder `hooks`. 

1. Add `pre-commit` to your local `.git/hooks` folder.
2. Make it executable by calling `chmod +x pre-commit`.
