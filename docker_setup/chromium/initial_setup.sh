./build/install-build-deps.sh

for dir in /chromium/src/third_party/*; do
    if [ -d "$dir" ]; then
        git config --global --add safe.directory "$dir"
    fi
done

gclient runhooks

gn gen out/Default
echo blink_symbol_level=0 >> out/Default/args.gn
echo v8_symbol_level=0 >> out/Default/args.gn
echo symbol_level=1 >> out/Default/args.gn
gn args out/Default --list --short --overrides-only
gn gen out/Debug
echo blink_symbol_level=0 >> out/Debug/args.gn
echo v8_symbol_level=0 >> out/Debug/args.gn
echo symbol_level=1 >> out/Debug/args.gn
gn args out/Debug --list --short --overrides-only

autoninja -C out/Default chrome
ninja -C out/Debug quic_server quic_client epoll_quic_server epoll_quic_client
