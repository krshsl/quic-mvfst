# /bin/bash
if [ ! -d "depot_tools" ]; then
  echo "fetching chromium dependencies (depot_tools)"
  git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
fi

export PATH="$(pwd)/depot_tools:$PATH"

image_name="$(docker images | grep -m 1 quic | awk '{print $1;}')"
if [ "$image_name" != "quic" ]; then
  image_name="$(docker images | grep -m 1 quic_sc | awk '{print $1;}')"
  if [ "$image_name" != "quic_sc" ]; then
    docker build -t quic_sc .
  else
    echo "docker image=$image_name already setup..."
  fi

  if [ ! -d "chromium" ]; then
    echo "fetching chromium"
    mkdir chromium && cd chromium
    fetch --nohooks --no-history chromium
    cd ..
  fi

  docker run --name quic_sc -v ./chromium:/chromium -v ./depot_tools:/depot_tools -u root quic_sc /bin/bash /initial_setup.sh
  container_id="$(docker container ls -a | grep -m 1 quic_sc | awk '{print $1;}')"
  docker commit $container_id quic:cn
  docker stop quic_sc && docker container rm quic_sc && docker image rmi quic_sc
fi
