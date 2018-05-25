#!/bin/bash
sudo apt-get install python3-pip
sudo -H pip3 install setuptools
sudo -H pip3 install -r requirements.txt
npm install 
sudo npm install pm2@latest -g
cd node_modules
git clone https://github.com/PersonaIam/persona-js
cd persona-js
npm install
