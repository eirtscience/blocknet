
#!/bin/bash

source config/.env

main(){
echo $IMAGE_TAG
echo $COMPOSE_PROJECT_NAME
echo $LANGUAGE
echo $CHANNEL_NAME
echo $NO_CHAINCODE
echo $MAX_RETRY
echo $CHAINCODE_DIR
echo $CHAINCODE_NAME
}

main
        