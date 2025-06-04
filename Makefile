dev: check run
run:
	cd core/ ; python3.7 core.py ;
check:
	mypy \
	core/anomaly.py \
	core/case.py \
	core/core.py \
	core/database.py \
	core/dataset.py \
	core/entity.py \
	core/entity_test.py \
	core/encode.py \
	core/encode_test.py \
	core/model.py \
	core/process.py \
	core/process_test.py \
	core/risk.py \
	core/riskmanager.py \
	core/display.py \
	core/user.py \
	core/user_test.py \
	core/utility.py \
	core/alert.py \
	core/api.py \
	core/hash.py \
	core/hash_test.py \
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
