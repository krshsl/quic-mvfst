sudo apt update
export VCPKG_DISABLE_METRICS=true
./bootstrap-vcpkg.sh
./vcpkg integrate install
./vcpkg install proxygen

