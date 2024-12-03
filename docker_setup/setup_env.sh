chmod +x chromium/setup_env.sh endpoint/setup_env.sh mvfst/setup_env.sh
cd endpoint
./setup_env.sh

cd ../chromium && ./setup_env.sh &
# cd ../mvfst && ./setup_env.sh &
cd ../proxygen && ./setup_env.sh &
echo "Waiting..."
wait

cd ../chromium
chk_image="quic:cn"
docker_run="docker run -it --entrypoint=/bin/bash -u root --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged"
image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
if [ "$image_name" != "$chk_image" ]; then
  volume='-v ./chromium:/chromium -v ./depot_tools:/depot_tools'
  $docker_run $volume --name quic_s $chk_image
  $docker_run $volume --name quic_c $chk_image
else
  echo "chromium already setup"
fi
# cd ../mvfst
# chk_image="mvfst:cn"
# image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
# if [ "$image_name" != "$chk_image" ]; then
#   volume='-v ./mvfst:/mvfst'
#   $docker_run $volume --name mvfst_s $chk_image
#   $docker_run $volume --name mvfst_c $chk_image
# else
#   echo "mvfst already setup"
# fi
cd ../proxygen
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
echo "Fin..."
