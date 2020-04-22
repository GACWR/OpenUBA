from model_modules import test_module

# need to expose execute
def execute():
    print("model_test testing... before disk")
    return_object: dict = dict()
    test_module.Execute()
    for x in range(0,100000):
        return_object[x] = {
            "value": "test"
        }

    print("model end run..................")
    return return_object
