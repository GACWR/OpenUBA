## Installation

Fork this repository (Click the Fork button in the top right of this page, click your Profile Image)
Clone your fork down to your local machine
```
git clone https://github.com/your-username/OpenUB.git
```

1. Install pip3 if you don't have it already
```    
    curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py"
    python3 get-pip.py     
    sudo python3 get-pip.py
```
2. Install the python dependencies and execute the makefile
```
pip3 install requirements.txt
make
```
3. Install HADOOP and JDK
4. Configure Spark environment by running spark_env.sh
```
bash spark_env.sh 
OR
./spark_env.sh
```
5. Run the node server
```
cd interface
npm init
npm start
```
6. Point your browser to localhost:3000 to view the web app running
7. Run the python scripts
```
python3 filename.py
```
