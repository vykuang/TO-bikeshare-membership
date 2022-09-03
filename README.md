# TO Bikeshare Membership

## Problem Statement

End-to-end ML deployment of a model predicting whether a trip record belongs to a member or a casual rider.

Bikeshare ridership data - given these features:

* ride start time
* duration
* start station id
* to-station id

Can we predict whether the user is a member (annual pass) or casual (short term pass)? Is this an unbalanced dataset? Are there far more members than casual trips logged?

## Running this thing

To run this for yourself, do this:

### ENV VARS

## Future Development

* Handling datasets from different years, not just 2017, taking into account the different column names and data fields
* Adding seasonality and year as features
* Complete script to include fetching data from TO open data as part of the pipeline
    * prefect-agent assumes that all source data has been neatly stored on `to-bikeshare-data` bucket in `/source/<year>/<quarter>.csv` format
    * `fetch` should pull from TO open data and push to cloud bucket in that format.
