#!/bin/bash
TMP_FLDR=/filer/tmp1
test_envs="mvfst quic"
docker_run="docker run -it --entrypoint=/bin/bash -u root --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged -v ./../../sim:/sim -v $TMP_FLDR/$USER/mvfst:/sim/mvfst  -v $TMP_FLDR/$USER/quic:/sim/quic"

function quic {
    cd chromium
    chk_image="quic:cn"
    image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
    if [ "$image_name" != "$chk_image" ]; then
        volume="-v ./chromium:/chromium -v ./depot_tools:/depot_tools"
        $docker_run $volume --name quic_s $chk_image
        $docker_run $volume --name quic_c $chk_image
    else
        echo "chromium already setup"
    fi
    cd ..
}

function mvfst {
    cd proxygen
    chk_image="proxygen:cn"
    image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
    if [ "$image_name" != "$chk_image" ]; then
        volume="-v ./vcpkg:/vcpkg"
        $docker_run $volume --name proxygen_s $chk_image
        $docker_run $volume --name proxygen_c $chk_image
    else
        echo "proxygen already setup"
    fi
    cd ..
}

chmod +x chromium/setup_env.sh endpoint/setup_env.sh
cd endpoint
./setup_env.sh

cd ../chromium && ./setup_env.sh &
cd ../proxygen && ./setup_env.sh &
echo "Waiting..."
wait

cd ..
for test_env in $test_envs; do
    cd ../sim
    mkdir -p $TMP_FLDR/$USER/$test_env
    if [ ! -d "$test_env" ]; then
        ln -s $TMP_FLDR/$USER/$test_env $test_env
    else
        echo "sym link already setup for $test_env"
    fi

    cd ../docker_setup
    while true
    do
        echo -n "Do you want to generate interactive $test_env docker containers?"
        read -r -p '' choice
        case "$choice" in
        n|N) break;;
        y|Y) $test_env; break;;
        *) echo 'Response not valid';;
        esac
    done
done

echo "Fin..."
