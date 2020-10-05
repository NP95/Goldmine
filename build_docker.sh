#!/bin/bash

DOCKER="$(docker -v)"
DOCKER_OUTPUT=${DOCKER//,/ }
DOCKER_VER="$(cut -d' ' -f3 <<<"$DOCKER_OUTPUT")"
REQUIRED_VER="18.09"

if [ "$(printf '%s\n' "$REQUIRED_VER" "$DOCKER_VER" | sort -V | head -n1)" = "$REQUIRED_VER" ]
then
	if [ -z "${DOCKER_BUILDKIT}" ] 
	then
		echo "Setting DOCKER_BUILDKIT environment variables.."
		export DOCKER_BUILDKIT=1
	fi
	docker build --network=host -t $USER/pgoldmine .
	docker run -v $PWD:/opt/goldmine \
               -it $USER/pgoldmine:latest \
               /bin/bash
else
	docker build --network=host -t $USER/pgoldmine .
	docker run -v $pwd:/opt/goldmine \
               -it $USER/pgoldmine:latest \
               /bin/bash
fi
