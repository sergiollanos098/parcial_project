#!/bin/bash
set -e
# installs docker and docker-compose on Amazon Linux 2 and runs docker-compose
sudo yum update -y
sudo amazon-linux-extras install docker -y || sudo yum install docker -y
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# docker-compose install
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o docker-compose
chmod +x docker-compose
sudo mv docker-compose /usr/local/bin/docker-compose
# start stack (assumes code is in /home/ec2-user/parcial_project)
cd ~/parcial_project || exit 0
docker-compose up -d --build
