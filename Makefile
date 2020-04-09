dev: check run
run:
	cd core/ ; python3.7 core.py ;
check:
	cd core/ ; \
	mypy \
	anomaly.py \
	case.py \
	core.py \
	database.py \
	dataset.py \
	entity.py \
	entity_test.py \
	encode.py \
	encode_test.py \
	model.py \
	process.py \
	process_test.py \
	risk.py \
	riskmanager.py \
	display.py \
	user.py \
	user_test.py \
	utility.py \
	alert.py \
	api.py \
	hash.py \
	hash_test.py \
	--ignore-missing-imports ;
describe_model:
	cd core/ ; python3.7 core.py describe_model ${model_name};
uis: #ui server
	cd interface/ ; node server.js
rd: # react development server
	cd interface/ ; npm run start
rb: # react build
	cd interface/ ; npm run build
save_dev:
	git add * -v ; git commit -am ${M}-v ; git push origin master:main_dev_branch -v;
test:
	python3.7 -m unittest discover -s ./core -p "*_test.py" -v
docker_build_server:
	time docker build --file "./DockerfileServer" -t openuba-server .
start_local_elk_mac:
	brew services start logstash
	brew services start elasticsearch
	brew services start kibana
stop_local_elk_mac:
	brew services stop logstash
	brew services stop elasticsearch
	brew services stop kibana
start_elk_windows:
stop_elk_windows:
