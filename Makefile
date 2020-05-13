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
profile_model:
	cd core/ ; python3.7 core.py profile_model ${model_name};
rd: # react development server
	cd interface/ ; npm run start
rb: # react build
	cd interface/ ; npm run build
electron: # launch electron
	cd interface/ ; npm run start-electron
electron_static: # launch electron static react
	cd interface/ ; npm run start-electron-static
package: #package react
	cd interface/ ; npm run package;
save_dev:
	git add * -v ; git commit -am ${M}-v ; git push origin master:main_dev_branch -v;
test:
	python3.7 -m unittest discover -s ./core -p "*_test.py" -v
docker_build_server:
	time docker build --file "./DockerfileServer" -t openuba-server .
docker_build_ui:
	time docker build --file "./DockerfileUI" -t openuba-ui .
