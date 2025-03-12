# mirror

## Overview
With LLMs, the Turing test is basically dead. This project explores a fun successor for the new age of AI, inspired by the mirror test for animals.

Most animals, when viewing their own reflection, cannot recognize it and instead view it as another animal. the LLM Mirror Test is:

**Can an untrained (no LoRas or specific finetunes) LLM, when given information about a person, successfully act as a mirror?**

In other words, can it convince you you're talking to an uploaded version of yourself?

Right now (spoiler alert), the answer is no - but this repo gives a quick attempt at the challenge.

## Project Structure
1. **server**: FastAPI backend to serve model results and store uploaded user info. 
    * bin subdirectory contains bash helper scripts to run (deploy) or shutdown the server. Note these scripts must be run from the ```server``` directory using ```bin/{script}```.
    * compose subdirectory contains Dockerfiles and start scripts

2. **scripts**: Holds helpful scripts to access the API once running

