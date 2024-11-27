chmod +x chromium/setup_env.sh endpoint/setup_env.sh mvfst/setup_env.sh 
cd endpoint
./setup_env.sh

cd ../chromium && ./setup_env.sh &
cd ../mvfst && ./setup_env.sh &
cd ../proxygen && ./setup_env.sh &
echo "Waiting..."
wait

cd ../chromium
chk_image="quic:cn"
image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
if [ "$image_name" != "$chk_image" ]; then
  docker run -it --name quic_s -v ./chromium:/chromium -v ./depot_tools:/depot_tools --entrypoint="/bin/bash" -u root -u root quic:cn
  docker run -it --name quic_c -v ./chromium:/chromium -v ./depot_tools:/depot_tools --entrypoint="/bin/bash" -u root -u root quic:cn
else
  echo "chromium already setup"
fi
cd ../mvfst
chk_image="mvfst:cn"
image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
if [ "$image_name" != "$chk_image" ]; then
  docker run -it --name mvfst_s -v ./mvfst:/mvfst --entrypoint="/bin/bash" -u root mvfst:cn
  docker run -it --name mvfst_c -v ./mvfst:/mvfst --entrypoint="/bin/bash" -u root mvfst:cn
else
  echo "mvfst already setup"
fi
cd ../proxygen
chk_image="proxygen:cn"
image_name="$(docker ps -a | grep -m 1 $chk_image | awk '{print $2;}')"
if [ "$image_name" != "$chk_image" ]; then
  docker run --name proxygen_s -v ./vcpkg:/vcpkg --entrypoint="/bin/bash" -u root proxygen:cn
  docker run --name proxygen_c -v ./vcpkg:/vcpkg --entrypoint="/bin/bash" -u root proxygen:cn
else
  echo "proxygen already setup"
fi
cd ..
echo "Fin..."
