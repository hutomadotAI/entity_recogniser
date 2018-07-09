# Base off of the Python image
FROM python:3.6.6-slim-stretch
LABEL maintainer "Paul Annetts <paul.annetts@hutoma.com>"

RUN echo "2018-07-06" > /os_patch_date.txt

RUN apt-get update \
 && apt upgrade -y \
 && apt install -y --no-install-recommends \
  build-essential \
  wget \
 && rm -rf /var/lib/apt/lists/*

# Install pipenv
ENV PIP_NO_CACHE_DIR=false
RUN pip install --upgrade pip pipenv

# Apply the pipenv
RUN mkdir -p /src/hu_entity/
COPY Pipfile* setup.py /src/
WORKDIR /src
RUN pipenv install --system

# Run script to download models for languages we require
COPY initialize_spacy_model.py /src/
RUN python initialize_spacy_model.py

# Copy the code
COPY hu_entity/ /src/hu_entity/

#---------------------------
# switch to non root user
# define user/group IDs as ARG
ARG USERID=1000
ARG GROUPID=1000
RUN addgroup --system --gid $GROUPID appuser
RUN adduser --system --uid $USERID --gid $GROUPID appuser

USER appuser
WORKDIR /home/appuser

# Get the NLTK corpus data
RUN python -m nltk.downloader stopwords


# Make available port 9095
EXPOSE 9095
CMD [ "python", "/src/hu_entity/server.py", "--port=9095" ]
