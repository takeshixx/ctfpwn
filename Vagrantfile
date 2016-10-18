# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/xenial64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  # config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.network "forwarded_port", guest: 9001, host: 8001
  config.vm.network "forwarded_port", guest: 8081, host: 8002

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get upgrade -y
    apt-get install -y python3-pip mongodb
    systemctl enable mongodb
    systemctl start mongodb
    pip3 install --upgrade pip
    pip3 install virtualenv
    mkdir -p /srv/ctf/logs
    chown -R ubuntu:ubuntu /srv/ctf
    su ubuntu -c "virtualenv /srv/ctf/env"
    echo "-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACCYcfv0TVKe3gmG1pDZ+00gwJIQFaQAJFz8Eecv9zWO7gAAAJBYEBZMWBAW
TAAAAAtzc2gtZWQyNTUxOQAAACCYcfv0TVKe3gmG1pDZ+00gwJIQFaQAJFz8Eecv9zWO7g
AAAEBkLzbDGgLKI3X8DOtVqpC0m3V+qHwh7mW8/RXZr60wqphx+/RNUp7eCYbWkNn7TSDA
khAVpAAkXPwR5y/3NY7uAAAADXRha2VzaGl4QFdPUFI=
-----END OPENSSH PRIVATE KEY-----
" > /home/ubuntu/.ssh/id_ed25519
    chown -R ubuntu:ubuntu /home/ubuntu/.ssh
    chmod 400 /home/ubuntu/.ssh/id_ed25519
    su ubuntu -c "echo -e 'Host github.com\n\tStrictHostKeyChecking no\n' >> /home/ubuntu/.ssh/config"
    su ubuntu -c "git clone git@github.com:takeshixx/ctf-pwn.git \
        --branch master --single-branch /srv/ctf/ctf-pwn"
    su ubuntu -c "/srv/ctf/env/bin/pip install -r /srv/ctf/ctf-pwn/requirements.txt"
    cp -r /srv/ctf/ctf-pwn/{exploitservice.service,flagservice.service} /etc/systemd/system
  SHELL
end
