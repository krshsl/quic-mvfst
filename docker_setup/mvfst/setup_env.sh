# /bin/bash
if [ ! -d "mvfst" ]; then
  git clone https://github.com/facebook/mvfst.git
fi

image_name="$(docker images | grep -m 1 mvfst | awk '{print $1;}')"
if [ "$image_name" != "mvfst" ]; then
  image_name="$(docker images | grep -m 1 mvfst_sc | awk '{print $1;}')"
  if [ "$image_name" != "mvfst_sc" ]; then
    docker build -t mvfst_sc .
  else
    echo "docker image=$image_name already setup..."
  fi

  docker run --name mvfst_sc -v ./mvfst:/mvfst -u root mvfst_sc /bin/bash /initial_setup.sh
  container_id="$(docker container ls -a | grep -m 1 mvfst_sc | awk '{print $1;}')"
  docker commit $container_id mvfst:cn
  docker stop mvfst_sc && docker container rm mvfst_sc && docker image rmi mvfst_sc
fi
