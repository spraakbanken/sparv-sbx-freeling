#!/bin/bash

echo Downloading FreeLing models
mkdir freeling
v=4.0
cd freeling
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ca.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/de.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/en.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/es.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/fr.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/gl.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/it.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/no.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/pt.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ru.cfg
wget -q https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/sl.cfg

echo Done.
