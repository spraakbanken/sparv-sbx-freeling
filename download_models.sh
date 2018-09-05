#!/bin/bash

echo Downloading FreeLing models
mkdir freeling
v=4.0
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ca.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/de.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/en.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/es.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/fr.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/gl.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/it.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/no.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/pt.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ru.cfg -P freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/sl.cfg -P freeling

# Fix bugs in config files for German and Norwegian
sed -i 's#/no/#/nb/#g' freeling/no.cfg
sed -i 's/InputLevel=tagged/InputLevel=text/g' freeling/de.cfg
sed -i 's/OutputLevel=dep/OutputLevel=tagged/g' freeling/de.cfg

echo Done.
