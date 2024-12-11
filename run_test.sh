#!/bin/bash
if [[ $# -ne 7 ]]; then
    echo 'Too many/few arguments, expecting one' >&2
    echo '1 - loss as int'
    echo '2 - delay in ms'
    echo '3 - throughput testing 0/1 to disable or enable'
    echo '4 - your init folder name'
    echo '5 - quic/mvfst mode'
    echo '6 - server ip'
    echo '7 - client ip'

    echo 'Running with default arguments!!'
    set -- "0" "0" "0" "1" "quic" "5" "6"
fi

# Name of the network and subnet
network_name="my_bridge_network"
subnet="172.168.150.0/24"

# Check if the network exists
if ! docker network inspect "$network_name" >/dev/null 2>&1; then
    echo "Network '$network_name' does not exist. Creating it with subnet '$subnet'..."
    docker network create --driver bridge --subnet="$subnet" "$network_name"

    # Check if the creation was successful
    if [[ $? -eq 0 ]]; then
        echo "Network '$network_name' created successfully with subnet '$subnet'."
    else
        echo "Failed to create network '$network_name'. Exiting."
        exit 1
    fi
else
    echo "Network '$network_name' already exists."

    # Verify if the existing network has the desired subnet
    existing_subnet=$(docker network inspect "$network_name" -f '{{(index .IPAM.Config 0).Subnet}}')
    if [[ "$existing_subnet" == "$subnet" ]]; then
        echo "The network already has the desired subnet '$subnet'."
    else
        echo "Warning: The network exists but has a different subnet '$existing_subnet'."
    fi
fi

shopt -s nocasematch

lossp=$1
delay=$2
throughput=$3
init_fldr=$4
sim_dir=./../../sim # update as per your location
folder_structure=$init_fldr\/$lossp\/$delay\/$throughput
log_file=$folder_structure/init.log
pcap_file=$folder_structure/init.pcap
docker_run="docker run -u root --net $network_name --cap-add=NET_ADMIN --cap-add=NET_RAW --privileged -v $sim_dir:/sim -v /filer/tmp1/$USER/mvfst:/mvfst -v /filer/tmp1/$USER/quic:/quic"
entry_point="/bin/bash /sim/start_server.sh $lossp $delay $throughput $pcap_file"
client_e_point="python3 /sim/test.py --throughput=$throughput --mode=client"
# update ip for each iters
ip_prefix=172.168.150.
ip_prefix_1=$ip_prefix$6
ip_prefix_2=$ip_prefix$7
echo "testing using $ip_prefix_1 & $ip_prefix_2"
chmod +x sim/start_server.sh
if [[ "$5" == "mvfst" ]]; then
    containers=("mvfst_server$6" "mvfst_client$7")
    image_name=proxygen:cn
    echo "log files at docker_setup/proxygen/mvfst_s/$log_file & docker_setup/proxygen/mvfst_c/$log_file"
    echo "pcap files folder /filer/tmp1/$USER/mvfst/$pcap_file"
    mkdir -p /filer/tmp1/$USER/mvfst/$folder_structure

    chmod +x sim/start_server.sh
    cd docker_setup/proxygen; mkdir -p mvfst_s/$folder_structure; $docker_run --ip $ip_prefix_1 -v ./vcpkg:/vcpkg --name mvfst_server$6 $image_name $entry_point $ip_prefix_1 mvfst > mvfst_s/$log_file 2>&1 &
    mkdir -p mvfst_c/$folder_structure; $docker_run --ip $ip_prefix_2 -v ./vcpkg:/vcpkg --name mvfst_client$7 $image_name $client_e_point --host=$ip_prefix_1 --instance=mvfst > mvfst_c/$log_file 2>&1 &
elif [[ "$5" == "quic" ]]; then
    containers=("quic_server$6" "quic_client$7")
    image_name=quic:cn
    echo "log files at docker_setup/chromium/quic_s/$log_file & docker_setup/chromium/quic_c/$log_file"
    echo "pcap files folder /filer/tmp1/$USER/quic/$pcap_file"
    mkdir -p /filer/tmp1/$USER/quic/$folder_structure

    chmod +x sim/start_server.sh
    cd docker_setup/chromium; mkdir -p quic_s/$folder_structure; $docker_run --ip $ip_prefix_1 -v ./chromium:/chromium -v ./depot_tools:/depot_tools --name quic_server$6 $image_name $entry_point $ip_prefix_1 quic > quic_s/$log_file 2>&1 &
    mkdir -p quic_c/$folder_structure; $docker_run --ip $ip_prefix_2 -v ./chromium:/chromium -v ./depot_tools:/depot_tools --name quic_client$7 $image_name $client_e_point --host=$ip_prefix_1 --instance=quic > quic_c/$log_file 2>&1 &
else
    echo "Pass argumet for instance to run as [mvfst, quic]"
    exit 1
fi


# Monitor the status of containers
sleep 10
while true; do
  for container in "${containers[@]}"; do
    # Check if a container has stopped
    if ! docker container inspect "$container" >/dev/null 2>&1; then
        echo "Container $container does not exist. Stopping all containers..."
        for c in "${containers[@]}"; do
          docker stop $c
          docker container remove -f $c
        done

        cat $5\_c/$log_file
        exit 0
      fi

    if [[ "$(docker inspect -f '{{.State.Running}}' $container 2>/dev/null)" == "false" ]]; then
      echo "Container $container has stopped. Stopping all containers..."
      for c in "${containers[@]}"; do
        docker stop $c
        docker container remove -f $c
      done

      cat $5\_c/$log_file
      exit 0
    fi
  done
  echo "Containers are still runnning..."
  sleep 5  # Check every 5 seconds
done
