if [ ! -d "vcpkg" ]; then
  git clone https://github.com/Microsoft/vcpkg.git
fi

image_name="$(docker images | grep -m 1 proxygen | awk '{print $1;}')"
if [ "$image_name" != "proxygen" ]; then
  image_name="$(docker images | grep -m 1 proxygen_sc | awk '{print $1;}')"
  if [ "$image_name" != "proxygen_sc" ]; then
    docker build -t proxygen_sc .
  else
    echo "docker image=$image_name already setup..."
  fi

  docker run --name proxygen_sc -v ./vcpkg:/vcpkg -u root proxygen_sc /bin/bash /initial_setup.sh
  container_id="$(docker container ls -a | grep -m 1 proxygen_sc | awk '{print $1;}')"
  docker commit $container_id proxygen:cn
  docker stop proxygen_sc && docker container rm proxygen_sc && docker image rmi proxygen_sc
fi
