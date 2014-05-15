    find . -name "*.py"  -exec sed -i .bak  s/ident_viewer/ivi/g {} \;
    find . -name "*.py.bak" | xargs rm
    find . -name "*.pyx" -exec sed -i .bak  s/ident_viewer/ivi/g {} \;
    find . -name "*.pyx.bak" | xargs rm
