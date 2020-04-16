#!/bin/bash

echo Downloading FreeLing models
mkdir sparv-model/freeling
v=4.1
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ca.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/de.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/en.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/es.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/fr.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/gl.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/it.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/nb.cfg -P sparv-model/freeling -O sparv-model/freeling/no.cfg
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/pt.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/ru.cfg -P sparv-model/freeling
wget -qN https://github.com/TALP-UPC/FreeLing/raw/$v/data/config/sl.cfg -P sparv-model/freeling

echo Done.
