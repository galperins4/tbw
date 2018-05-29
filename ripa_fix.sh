
sudo find / -name "transaction.createTransaction.py" 2>/dev/null | xargs sed -i "s/arkjs/ripa-js/g"
cd node_modules
git clone https://github.com/RipaEx/ripa-js
cd ripa-js
npm install
