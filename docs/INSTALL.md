## Installation

Fork this repository (Click the Fork button in the top right of this page, click your Profile Image)
Clone your fork down to your local machine
```
git clone https://github.com/your-username/OpenUBA.git
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

5. Run the API server (from root directory)
```
make
```
This will invoke the "dev" stage of the Makefile, thus running the mypy linter for syntax checking, and the core.py

### To run test on your project
```
make test
```

### If you have another python executable version
you may need to alter the "run" stage of the Makefile, similar to:
```
cd core/ ; python3.7 core.py ;
```

To verify this is working, try to access
```
http://127.0.0.1:5000/display/teststring
```

6. Run the web server (from root directory)
```
make run_ui
```
7. Point your browser to http://127.0.0.1:3000/ to view the web app running

# React
From the root folder, run the following command to initiate the react development server
```
make rd
```

If you run this command, it will build the static html from React
```
make rb
```

From this point, running the following command will server the static HTML
```
make uis # UI server
```

# Electron app
To start the electron app, run
```bash
make electron
```

# Installing ELK on mac

https://logz.io/blog/elk-mac/

```
brew install elasticsearch && brew info elasticsearch
```

```
brew services start elasticsearch
```

```
brew install logstash
```

```
brew services start logstash
```


```
brew install kibana
```

```
brew services start kibana
```

```
brew services list
```

```
sudo vi /usr/local/etc/kibana/kibana.yml
```

# Installing ELK on windows
