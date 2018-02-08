# Base off of the Python image
FROM python:3.5.4-slim
LABEL maintainer "Paul Annetts <paul.annetts@hutoma.com>"

RUN echo "2018-02-08" > /min_patch_date.txt

RUN apt-get update \
 && apt upgrade -y \
 && apt install -y --no-install-recommends \
  build-essential \
  wget \
 && rm -rf /var/lib/apt/lists/*
   
RUN pip install --no-cache-dir --upgrade pip

# Copy common code
COPY requirements.txt .
# PIP install requirements and the spacy model
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Run script to download models for languages we require
COPY initialize_spacy_model.py .
RUN python initialize_spacy_model.py

# Copy the code
COPY setup.py src/
COPY hu_entity/ src/hu_entity/
RUN pip install --no-cache-dir -e /src

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
