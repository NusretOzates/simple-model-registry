# FastAPI Model Registry Service

This service is a FastAPI application that provides a REST API for managing machine learning models. 
It allows you to register models, upload new versions, save important metadata such as:

- Parameters: hyperparameters used to train the model
- Metrics: evaluation metrics
- Tags: labels that can be used to filter models
- Description: a brief description of the model
- Model file: the actual model file
- Creator: the user who registered the model
- Created at: the date and time when the model was registered
- Updated at: the date and time when the model was last updated
- Alias: a unique name for "that model and that version" that can be used to reference the model in other services

You can run this service locally or deploy it to a cloud provider such as AWS, GCP, or Azure.

3 environment variables are required to run the service:

- `DATABASE_URL`: the URL of the database where the models will be stored
- `MODEL_STORAGE_PATH`: the path where the model files will be saved
- `MODEL_STORAGE_METHOD`: the method used to store the model files. Currently, only `local` is supported.

## How to use
In code changes you can use the following commands to fix formatting (assuming you have `make` and `ruff` installed):

```bash
make format
```

When you want to test the code, you can use the following command:

```bash
make build test
```
This will build the docker container and run the tests.

To run the service locally, you can use the following command:

```bash
make run
```

This will start the FastAPI service on `http://localhost:8000`. You can access the Swagger UI at `http://localhost:8000/docs` to interact with the API.

## Limitations

- Only local file storage is supported for model files. You can extend the service to use cloud storage such as S3 or GCS.
- Authentication and authorization are not implemented. You can add authentication middleware to secure the service.
- The service does not support model serving or inference. You can build a separate service for model deployment and inference.
- No one forbids you to send a picture of a cat instead of a model file. You can add file type validation to ensure that the uploaded file is a valid model file.
- There is no client library and I think this is a must-have for a service like this.
- Version saving is not robust to distributed systems. You can use a distributed lock to ensure that the version is unique such as Redis.

## TO DO
- Add authentication and authorization
- Add file type validation
- Add client library
- Add distributed lock for version saving
- Add alias support for updating, deleting and getting models
- Something about model save interface doesn't make sense, but I forgot what it was