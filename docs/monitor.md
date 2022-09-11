# Monitoring

Monitoring will be done on a batch basis. Prefect will orchestrate metric evaluation flows on the data pushed to a MongoDB container. Model performance, data drift, and concept drift will be prioritized.

## Setup

As part of the `predict` app, the web service will push a copy of the input data, the prediction made, as well as the model metadata to a MongoDB service. The `mongo` service will be spun up within the same `docker-compose.yaml` that specifies the `predict` service to facilitate easier communication.

The docker compose section for `mongo`:

```yaml
services:
  predict:
    depends_on:
      - mongo
    environment: # uses the service name to find the mongo container host IP
      MONGODB_URI: "mongodb://mongo.:27017/" # hence `mongo.:`
    networks:   # same network as mongo
      - back-tier
  mongo:
    image: mongo
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    networks:
      - back-tier
        
volumes:
  mongo_data: {}

networks:
  back-tier:
```

## Execution

1. Send the results to `mongo` after making the prediction

    ```py
    from pymongo import MongoClient
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    mongo_client = MongoClient(MONGODB_URI)
    db = mongo_client.get_database("prediction_service")
    collection = db.get_collection("data")

    def save_to_db(result: dict) -> None:
    """Save prediction metadata to a DB for batch monitoring"""
    collection.insert_one(result)

    def predict_endpoint():
        ...
        save_to_db(result.copy())
        return result
    ```

2. Orchestrate a Prefect flow to collect data from the MongoDB and invoke Evidently to evaluate model metrics.
    1. `upload_target` - In the ride prediction context, the target is not available until the trip has finished, and so must be uploaded after the prediction is made. Our example of membership prediction doesn't fit cleanly into this mold; the target is available right off the bat. Having the target allows us to evaluate model performance.
    2. `load_reference_data` - To evaluate data drift, we need a reference point. Here we load the dataset we initially selected as the anchor point against which to compare all new data. Preprocess the reference as we would any new data, and then add *prediction* as a new column for return
    3. `fetch_data` - get the newest batch of data from mongoDB. This data has been preprocessed
    4. `run_evidently` - model performance and data drift analysis using new data and reference data


