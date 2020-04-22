# need to expose execute
def execute():
	print("model_test testing...")
	return_object: dict = {}

	for x in range(0,100000):
		return_object[x] = {
			"value": "test"
		}

	print("model end run..")
	return return_object
