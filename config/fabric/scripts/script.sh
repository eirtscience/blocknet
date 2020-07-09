
#!/bin/bash

echo
echo " ____    _____      _      ____    _____ "
echo "/ ___|  |_   _|    / \    |  _ \  |_   _|"
echo "\___ \    | |     / _ \   | |_) |   | |  "
echo " ___) |   | |    / ___ \  |  _ <    | |  "
echo "|____/    |_|   /_/   \_\ |_| \_\   |_|  "
echo
echo "Build BLACKCREEK network "
echo
CHANNEL_NAME="$1"
DELAY="$2"
LANGUAGE="$3"
TIMEOUT="$4"
VERBOSE="$5"
NO_CHAINCODE="$6"
: ${CHANNEL_NAME:="BlackCreekChannel"}
: ${DELAY:="3"}
: ${LANGUAGE:="node"}
: ${TIMEOUT:="10"}
: ${VERBOSE:="false"}
: ${NO_CHAINCODE:="false"}
LANGUAGE=`echo "$LANGUAGE" | tr [:upper:] [:lower:]`
COUNTER=1
MAX_RETRY=10
CHAINCODE_DIR="./"
CHAINCODE_NAME="blackcreek_estate"

CC_SRC_PATH="github.com/chaincode/${CHAINCODE_DIR}/go/"
if [ "$LANGUAGE" = "node" ]; then
	CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/${CHAINCODE_DIR}/node/"
fi

if [ "$LANGUAGE" = "java" ]; then
	CC_SRC_PATH="/opt/gopath/src/github.com/chaincode/${CHAINCODE_DIR}/java/"
fi

echo "Channel name : "$CHANNEL_NAME

# import utils
. scripts/utils.sh

createChannel() {
	setGlobals 0 1

	if [ -z "$CORE_PEER_TLS_ENABLED" -o "$CORE_PEER_TLS_ENABLED" = "false" ]; then
                set -x
		peer channel create -o orderer.blackcreek.tech:7050 -c $CHANNEL_NAME -f ./channel-artifacts/channel.tx >&log.txt
		res=$?
                set +x
	else
				set -x
		peer channel create -o orderer.blackcreek.tech:7050 -c $CHANNEL_NAME -f ./channel-artifacts/channel.tx --tls $CORE_PEER_TLS_ENABLED --cafile $ORDERER_CA >&log.txt
		res=$?
				set +x
	fi
	cat log.txt
	verifyResult $res "Channel creation failed"
	echo "===================== Channel '$CHANNEL_NAME' created ===================== "
	echo
}

joinChannel () {
	for org in dc dp dt; do
	    for peer in 0 ; do
		joinChannelWithRetry $peer $org
		echo "===================== peer${peer}.${org} joined channel '$CHANNEL_NAME' ===================== "
		sleep $DELAY
		echo
	    done
	done
}

# Create channel
echo "Creating channel..."
createChannel

# Join all the peers to the channel
echo "Having all peers join the channel..."
joinChannel

# Set the anchor peers for each org in the channel
echo "Updating anchor peers for dc..."
updateAnchorPeers 0 0
# Set the anchor peers for each org in the channel
echo "Updating anchor peers for dc..."
updateAnchorPeers 0 1

echo "Updating anchor peers for dp..."
updateAnchorPeers 0 2

if [ "${NO_CHAINCODE}" != "true" ]; then

	# Install chaincode on peer0.dc and peer0.dp
	echo "Installing chaincode on peer0.dc..."
	installChaincode 0 0
	# Install chaincode on peer0.dc and peer0.dp
	echo "Installing chaincode on peer1.dc..."
	installChaincode 0 1

	echo "Installing chaincode on peer2.dp..."
	installChaincode 0 2


	# Instantiate chaincode on peer0.dp
	echo "Instantiating chaincode on peer2.dp..."
	instantiateChaincode 0 2
	# # Query chaincode on peer0.dc
	echo "Querying chaincode on peer2.dc..."
	chaincodeQuery 0 2 '{"estate_id":"HglTE3ABymlcWnsiy9b1","estate_name":"Marriot","provider_id":"f363b02c-e1f1-42d4-9078-b4848c45fb42","region":"Guangcheng Hui","staff_id":"e47c659e-a81e-4759-af9e-b42110002b09","street_address":"123 Argyle"}'

	# # Invoke chaincode on peer0.dc and peer0.dp
	# echo "Sending invoke transaction on peer0.dc peer0.dp..."
	# chaincodeInvoke 0 1 0 2

	# ## Install chaincode on peer1.dp
	echo "Installing chaincode on peer1.dp..."
	installChaincode 1 2

	# # Query on chaincode on peer1.dp, check if the result is 90
	echo "Querying chaincode on peer1.dp..."
	# chaincodeQuery 1 2 90

fi

if [ $? -ne 0 ]; then
	echo "ERROR !!!! Test failed"
    exit 1
fix
        