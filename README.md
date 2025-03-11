# mirror

## Project Structure
1. **server**: FastAPI backend to support web app experience. 
    * bin subdirectory contains bash helper scripts to run (deploy) or shutdown the server. Note these scripts must be run from the ```server``` directory using ```bin/{script}```.
    * compose subdirectory contains Dockerfiles and start scripts

2. **scripts**: Holds helpful scripts to access the API once running

