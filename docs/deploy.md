# Model Deployment

A Gunicorn container will act as the interface to serve the trained ML model.

Workflow:

* Gunicorn instance is listening at specific port
* User POSTs @ `/predict` with the path to the file
    * Path should be an S3 path?
* Container will retrieve the 