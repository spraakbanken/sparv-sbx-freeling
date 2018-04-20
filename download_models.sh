#!/bin/bash

echo Downloading FreeLing models
mkdir freeling
v=4.0
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ca.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/de.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/en.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/es.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/fr.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/gl.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/it.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/no.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/pt.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ru.cfg -P freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/sl.cfg -P freeling

echo Done.
