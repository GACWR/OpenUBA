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
	model.py \
	process.py \
	risk.py \
	riskmanager.py \
	display.py \
	--ignore-missing-imports ;
run_ui:
	cd interface/ ; npm start ;
save_dev:
	git add * -v ; git commit -am "saved from makefile to main_dev_branch" -v ; git push origin master:main_dev_branch -v;
test:
	python -m unittest discover -s ./core -p "*_test.py" -v
