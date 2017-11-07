# Base off of the Python image
FROM python:3.5.2-alpine
LABEL maintainer "Paul Annetts <paul.annetts@hutoma.com>"

RUN apk update \
  && apk add --no-cache python3-dev g++ linux-headers libffi-dev bash openssl wget

RUN pip install --no-cache-dir --upgrade pip

# Download the spacy model as contained in spacy_model.txt
# Using the file makes it easy to keep it consistent between virtualenv and Docker
COPY hu_entity/spacy_model.txt .
# Download, pip install spacy and the model and cleanup the .tar.gz
RUN pip install --no-cache-dir spacy==1.10.0 && \
  cat spacy_model.txt | xargs wget -O spacy_model.tar.gz && \
  pip install --no-cache-dir spacy_model.tar.gz && \
  rm spacy_model.tar.gz

# Copy common code
COPY requirements.txt .
# PIP install requirements and the spacy model
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Get the NLTK corpus data
RUN python -m nltk.downloader stopwords

# Copy the code
COPY setup.py src/
COPY hu_entity/ src/hu_entity/
RUN pip install -e /src

# Make available port 9095
EXPOSE 9095
CMD [ "python", "src/hu_entity/server.py", "--port=9095" ]
