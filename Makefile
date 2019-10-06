dev: check run
run:
	cd core/ ; python core.py ;
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
	--ignore-missing-imports ;
run_ui:
	cd interface/ ; npm start ;
