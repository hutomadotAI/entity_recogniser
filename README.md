# Introduction 
The entity matcher serves as a client to connect with the entity recognizer for entity extraction as well as tokenization. It also includes matching logic based solely on entities found in the training and chat questions. It only deals with spacy entities. Custom entities are treated as string matches and are therefore discussed in the String Matcher. 

The Entity Recogniser is part of the Conversational AI Platform and will be also installed if you follow the instructions posted in our [main repo](https://github.com/hutomadotAI/Hutoma-Conversational-AI-Platform)


## Match Entities 
The chat worker calls function "match_entities" with the chat question, the entities found in the question and potentially a list of indices to subset the training question (see discussion in QA-Matcher).  At the beginning it gets preprocessed to normalize the questions. 
It first searches for similarities between user query and training questions using function "interrogative_match". This method searches specifically for question which 

  * Have the word "who" in them and no entity of type "person" in the query. For such questions it increases the count for training questions which have an entity of type "person" in the answer 

  * Have the word "what" in them and contain an entity of type "org" or "group". If any of those entities appears in a training question the count for this question increases by one (NOT IN USE CURRENTLY!!!!) 

  * Have the word "who" in them. If such questions also contain an entity of type "person" which also appears in a training questions its count increases by one 

  * Have an entity of type "person" in them. If any part of the name matches a name in a training question its count increases by one 

It reduces the list of possible training matches to the ones that have the largest count value. If the count is 0 for all, all training questions continue to the next step. 

 
In the next step  it calls function "match_entities". It counts the number of entity substrings which match between query and training questions. The training questions with the most matches are returned to the chat function. If the number of matches in this second step is zero the questions which matched the first step are returned. If both are zero an empty list is returned. 

# Build and Test

Requirements:
- Docker


To build the docker image from source, run:
```
cd src
docker build -t hu_er .
```

To run the container:
```
docker run \
    -p 9095:9095 \
    -e ERS_LANGUAGE={language} \
     --network hu_net \
     --name hu_er \
     hu_er
```
Where language can be _en_, _es_, _fr_, _pt_ or _it_.
