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
  config.vm.network "forwarded_port", guest: 8080, host: 8001
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
    apt-get install -y python3-pip mongodb nmap
    systemctl enable mongodb
    systemctl start mongodb
    pip3 install --upgrade pip
    pip3 install virtualenv mongo-connector elastic2-doc-manager
    mkdir -p /srv/ctf/{ctf-pwn,logs,exploits}
    chown -R ubuntu:ubuntu /srv/ctf
    su ubuntu -c "virtualenv /srv/ctf/env"
    su ubuntu -c "cp -r /vagrant/{ctfpwn,run-*.py,*.ini,config.yaml,requirements.txt} /srv/ctf/ctf-pwn"
    su ubuntu -c "/srv/ctf/env/bin/pip install -r /srv/ctf/ctf-pwn/requirements.txt"
    cp -r /vagrant/systemd/{*.service,*.target} /etc/systemd/system
    mkdir /etc/systemd/system/ctfpwn.target.wants
    ln -s /etc/systemd/system/ctfpwn-api.service /etc/systemd/system/ctfpwn.target.wants/ctfpwn-api.service
    ln -s /etc/systemd/system/exploitservice.service /etc/systemd/system/ctfpwn.target.wants/exploitservice.service
    ln -s /etc/systemd/system/flagservice.service /etc/systemd/system/ctfpwn.target.wants/flagservice.service
    ln -s /etc/systemd/system/targetservice.service /etc/systemd/system/ctfpwn.target.wants/targetservice.service
  SHELL
end
