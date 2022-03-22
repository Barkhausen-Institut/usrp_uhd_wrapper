#########################################################
# add option to run clang-format on all files here
#########################################################

# add glob specifications where to look for files 
# that shall be formatted by clang-format
set(DIRECTORIES_TO_FORMAT "src" "include" "tests")
set(FILE_EXTENSIONS_TO_FORMAT "cpp" "cxx" "c" "hpp" "h")
set(FILE_PATTERNS "")

foreach(dir IN LISTS DIRECTORIES_TO_FORMAT)
    foreach(extension IN LISTS FILE_EXTENSIONS_TO_FORMAT)
        list(APPEND FILE_PATTERNS ${dir}/*.${extension})        
    endforeach()
endforeach()

file(GLOB FILES_TO_FORMAT ${FILE_PATTERNS})
set(CLANG_FORMAT_COMMAND clang-format ${FILES_TO_FORMAT} -i -style=file -assume-filename=clang-format)

# only run clang-format if there are files found to format
if(FILES_TO_FORMAT)
    add_custom_target(format 
        COMMAND ${CLANG_FORMAT_COMMAND} 
        COMMENT "Running clang-format."
        USES_TERMINAL)
else()
    message("format target not created, since no files to format can be found. Consider updating FILE_PATTERNS?")
endif()

#########################################################
# add option to run doxygen on all files here
#########################################################

find_package(Doxygen)
if (DOXYGEN_FOUND)
    set(DOXYGEN_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/docs)

    set(DOXYFILE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/docs/Doxyfile)
    add_custom_target(doxygen
        COMMAND Doxygen::doxygen ${DOXYFILE_PATH}
        WORKING_DIRECTORY ${DOXYGEN_OUTPUT_DIRECTORY}
        COMMENT "Generating API documentation with Doxygen"
        VERBATIM )
else (DOXYGEN_FOUND)
    message("Doxygen is not installed.")
endif (DOXYGEN_FOUND)