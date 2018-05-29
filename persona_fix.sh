find / -name "transaction.createTransaction.py" 2>/dev/null | xargs sed -i "s/arkjs/persona-js/g"

cd node_modules
git clone https://github.com/PersonaIam/persona-js
cd persona-js
npm install
