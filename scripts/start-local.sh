
#!/bin/bash
echo "Run backend and ML locally (you still need a local MongoDB running)"
cd server && npm install
cd ../ml_model && pip install -r requirements.txt
