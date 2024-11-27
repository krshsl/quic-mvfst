image_name="$(docker images | grep -m 1 quic_mvfst | awk '{print $1;}')"
if [ "$image_name" != "quic_mvfst" ]; then
  docker build -t quic_mvfst .
else
  echo "docker image=$image_name already setup..."
fi
