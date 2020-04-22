# Saved Models/Model Checkpoints

There exists a directory for each model. The directory holds saved model files. The model files can be the following formats:
- Pickle file
- Protobuf file
- Arbitrary file to be parsed by the model itself

# Directory contents
In each model folder, each file has a sortable name, preferably numerical. On model execution, the default model save point loaded has the highest number -- like a nonce, of which is increased upon every new model checkpoint created

*purposely kept as files to lessen dependencies of OpenUB. However this may be changed in the future*
