
#!/bin/bash


FABRIC_DIR =$PWD

CONNECXION_PROFILE_DIR =${FABRIC_PATH}/connecxion-profile

one_line_pem() {

   echo "`awk 'NF {sub(/\\\n/, ""); printf " % s\\\n",$0;}' $1`"
}

json_ccp() {

    # local PP=$(one_line_pem $5)
    # local CP=$(one_line_pem $6)

    
    sed - e 's/\${ORG}/$1/' \
        - e 's/\${P0PORT}/$2/' \
        - e 's/\${P1PORT}/$3/' \
        - e "s#\${CAPORT}/$4/" \
        - e "s#\${PEERPEM}/$5/" \
        - e "s#\${CAPEM}/$6/" \
        - e "s#\${MSP}/$7/" \
        - e "s#\${DOMAIN}/$8/" \
        - e "s#\${CA}/$9/" \
        - e "s#\${PEER0}#${10}#" \
        - e "s#\${PEER1}#${11}#" \
        - e "s#\${CANAME}#${12}#" \
        ${FABRIC_DIR}/ccp-template.json
}

 yaml_ccp() {
    # local PP=$(one_line_pem $5)
    # local CP=$(one_line_pem $6)
    
    sed - e 's/\${ORG}/$1/' \
        - e 's/\${P0PORT}/$2/' \
        - e 's/\${P1PORT}/$3/' \
        - e "s#\${CAPORT}/$4/" \
        - e "s#\${PEERPEM}/$5/" \
        - e "s#\${CAPEM}/$6/" \
        - e "s#\${MSP}/$7/" \
        - e "s#\${DOMAIN}/$8/" \
        - e "s#\${CA}/$9/" \
        - e "s#\${PEER0}#${10}#" \
        - e "s#\${PEER1}#${11}#" \
        - e "s#\${CANAME}#${12}#" \
        ${FABRIC_DIR}/ccp-template.yaml | sed - e $'s/\\n/\
        /g'
}


usage(){

    echo "usages"
}


main(){

    
    ORG =${2}
    P0PORT =${3}
    P1PORT =${4}
    CAPORT =${5}
    PEERPEM =${6}
    CAPEM =${7}
    MSP =${8}
    DOMAIN =${9}
    CA =${10}
    PEER0 =${11}
    PEER1 =${12}
    CANAME =${13}


    if [! -d "$FABRIC_PATH/connecxion-profile"]; then

            mkdir - p $FABRIC_PATH/connecxion-profile
    fi



    case $1 in
        yaml)
             echo "$(yaml_ccp $ORG $P0PORT $P1PORT $CAPORT $PEERPEM $CAPEM $MSP $DOMAIN $CA $PEER0 $PEER1 $CANAME)" > ${CONNECXION_PROFILE_DIR} /${DOMAIN}.yaml
            exit 0;;

        json)
            echo "$(json_ccp $ORG $P0PORT $P1PORT $CAPORT $PEERPEM $CAPEM $MSP $DOMAIN $CA $PEER0 $PEER1 $CANAME)" > ${CONNECXION_PROFILE_DIR} /${DOMAIN}.json
        ;;
        all)
            echo "$(json_ccp $ORG $P0PORT $P1PORT $CAPORT $PEERPEM $CAPEM $MSP $DOMAIN $CA $PEER0 $PEER1 $CANAME)" > ${CONNECXION_PROFILE_DIR}/${DOMAIN}.json
            echo "$(yaml_ccp $ORG $P0PORT $P1PORT $CAPORT $PEERPEM $CAPEM $MSP $DOMAIN $CA $PEER0 $PEER1 $CANAME)" > ${CONNECXION_PROFILE_DIR}/${DOMAIN}.yaml
        ;;
        *)
            usage
        ;;
    esac
}


main $@
