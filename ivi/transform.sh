for F in rt mz ii;
do
    for PF in min max;
    do
        find . -name "*.py"  -exec sed -i .bak  s/$F\_$PF/$F$PF/g {} \;
        find . -name "*.py.bak" | xargs rm
        find . -name "*.pyx" -exec sed -i .bak  s/$F\_$PF/$F$PF/g {} \;
        find . -name "*.pyx.bak" | xargs rm
    done
done
