# ML deployed as web service
FROM python:3.9-slim

# gets the latest pip
RUN pip install --upgrade pip

# to use our Pipfile and Pipfile.lock
RUN pip install pipenv

WORKDIR /app

# need to use double quotes
# For > 2 args, all args are considered files except
# for the last, which will be the destination folder
COPY [ "Pipfile", "Pipfile.lock", "./"]

RUN pipenv install --system --deploy

# EXEC form; ENTRYPOINT provides the wrapper,
ENTRYPOINT [ "prefect", "agent", "start" ]

# CMD provides the customization argument
CMD [ "$PREFECT_WORK_QUEUE" ]