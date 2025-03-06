NAME=mocap
SELINUX="--security-opt label=disable"
podman container rm $NAME
podman build -t $NAME -f ./docker/Dockerfile . $SELINUX
podman run -it --name $NAME -e LOGLEVEL=DEBUG $SELINUX $NAME
podman start -i $NAME