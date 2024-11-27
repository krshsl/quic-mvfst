sudo apt update

sudo ./build/fbcode_builder/getdeps.py install-system-deps --recursive --install-prefix=$(pwd)/_build mvfst

python3 ./build/fbcode_builder/getdeps.py clean  --scratch-path $(pwd)/_tmp

python3 ./build/fbcode_builder/getdeps.py --allow-system-packages build mvfst --scratch-path $(pwd)/_tmp --install-prefix=$(pwd)/_build

python3 ./build/fbcode_builder/getdeps.py test mvfst --scratch-path $(pwd)/_tmp --install-prefix=$(pwd)/_build