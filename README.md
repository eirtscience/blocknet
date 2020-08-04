
<div align="center" style="">
  <img src="images/blocknet.png"><br><br>
</div>

# `BlockNet`

   Running private blockchain application using Hyperledger Fabric network, it is a pain when it comes to the configuration. Missing some configuration will deny the network to run. The pain of modifying the Hyperledger Fabric organization default setting. The lock into the Hyperledger fabric default two `orgs` and so on. If you are among those people, then welcome to `Blocknet`. `blocknet` is design to solve the above issues, and allow you to generate the Hyperledger Fabric setting.


## `Structure of the Project`
The blocknet project is comprised with 2 type of applications. The `hyperledger-fabric` and `hyperledger-explorer`


  - `hyperledger-fabric`:

    It is a Hyperledger Fabric blockchain network.

  - `hyperledger-explorer`:

     It is a web application, that shows the blockchain configuration and transactions.


## `Requirement`

- `Environment`
  - `Operating System` : GNU/Linux Ubuntu 18.04
  - `CPU`              : 4 core 3693 MHz
  - `Memory`           : 10GB or more

- `Software packages`

  The require packages to allow `blocknet` to successfuly install the blockchain network are described below:

  | **Packages** | **Version** |
  |:-------------|:--------------------------------|
  | docker       | 18.09.7                         |
  | docker-compose   | 1.24.1                    |
  | python   | 3.5+            |
  | git      | 2.17.1 |

  In case you have issue installing those packages , no worry, `blocknet` can help provided that. After download the `blocknet`, when you execute `blocknet` for the first time, it will install all the missing packages, if thy are not installed.




## `Installation Guide`

  - `Download blocknet`

      Download `blocknet` following the below command.

      ```sh
      ~$ sudo curl -L "https://raw.githubusercontent.com/eirtdev/shell/master/blocknet" -o /usr/local/bin/blocknet && sudo chmod +x /usr/local/bin/blocknet
      ```

      Now go ahead and run the below command and wait.

      ```sh
      ~$ blocknet
      ```

## `How it works`

To be able to start with blocknet, you can decide to run it using either the configuration file or input the information about your setting manually.

   
   - `Running blocknet with a configuration file`
    
      To run the blocknet with the configuration file, you need to create the configuration file called `network.jon`. Luckly `blocknet` has solution for you.
      To create the configuration template file, run the below command.

      ```sh
      ~$ blocknet --init
      ```
      Once you execute the above command, a  `network.json` file will be created in the current directory

      `network.json file`

      ```json
      {
        "network": {
          "name": "ExampleNetwork",
          "admin": {
            "first_name": "",
            "last_name": "",
            "login_name": "admin",
            "domain": "example.com",
            "login_password": "adminpwd"
          },
          "channel": {
            "name": "ExampleChannel"
          },
          "orderer": {
            "type": "etcdraft",
            "number": 5
          }
        },
        "chaincode": {
          "name": "example_chaincode",
          "directory": "",
          "language": "node"
        },
        "org": [
          {
            "name": "ORG1",
            "domain": "org1.example.com",
            "number_of_peer": 2
          },
          {
            "name": "ORG2",
            "domain": "org2.example.com",
            "number_of_peer": 2,
            "has_chaincode": true
          }
        ],
        "explorer": {
          "install": false
        }
      } 
      ```


        - `network object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          | `name`     | The name of the blokchain network |`True`|`Nil`|


        - `admin object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          |`first_name`|The first name of the blokchain admin network|`False`|`Nil`|
          |`last_name`| The last name of the blockchain admin network|`False`|`Nil`|
          |`login_name`|The login name of the blokchain admin network|`True`|`admin`|
          |`login_password`| The password of the blockchain admin network|`True`|`adminpw`|            
          |`domain`|The domain name of the blokchain admin network|`True`|`Nil`|

        - `channel object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          | `name`   |The initial channel name of the blokchain network|`True`|`Nil`|

        - `order object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          | `type`   |The orderer type|`True`|`etcdraft`|
          | `number`   |The total number of the orderer |`True`|`5`|


        - `chaincode object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          | `name`   |The chaincode name. This need to be the directory that has the chaincode|`True`|`Nil`|
          | `directory`|The absolute directory path to the chaincode name|`True`|`Nil`|
          | `language`   |The support chaincode programming language|`True`|`Nil`|


            `Example`:

            The below directory tree, listed all the directories listening in your chaincode directory showing below.

            ```sh
            ├── home            
            |   ├── chaincode
            │   |    ├── car
            │   │    |     └── node
            ```
            Follow the above directory tree, the chaincode information will be as showing below

          |**Keys**|**Value**|
          |:---------|:------|
          | `name`   |car|
          | `directory`   |/home/chaincode|
          | `language`   |node|


        - `org object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          | `name`   |The Organization name|`True`|`Nil`|
          | `domain`   |The domain name of the organization |`True`|`Nil`|
          | `number_of_peer`   |The total number of the peers to use. minimum should be 2. |`True`|`0`|
          | `has_chaincode`|Inform the blocknet whether the above chaincode will be installed on this organization |`True`|`Nil`|

          

        - `explorer object`

          |**Keys**|**Description**|**Mandatory**|**Default**|
          |:---------|:------------|-------------|-----------|
          | `install`   |Evaluate whether to install the Hyperledger explorer or not|`True`|`Nil`|
     
          
  - `Running blocknet with Interractive configuration`

    Running the blocknet in interractive mode, require you to run the blocknet script without arguments as showing below.

    ```sh
    ~$ blocknet
    ```

    ```sh
      ################################################################################
      #
      #
      # SECTION: Network Admin
      #
      #
      #
      ################################################################################

              
      First name: Jhon
      Last name: Wick
      Domain: example.com
      Login name [admin]: 
      Login password [adminpw]: 
      Organization name [EXAMPLE]: WickLimited
      Email address [admin@example.com]: 

      ################################################################################
      #
      #
      #  SECTION: Network
      #
      #
      ################################################################################
      
      Name [ExampleNetwork]: 
              
      Select Network version ['V1_4_4', 'V1_4_2', 'V1_3', 'V1_2', 'V1_1'] [V1_4_4]: 

      ################################################################################
      #
      #
      #  SECTION: Consurtium
      #
      #
      ################################################################################

              
      Channel Name [WicklimitedChannel]: 

      ################################################################################
      #
      #   SECTION: Orderer
      #
      #   - This section defines the values to encode into a config transaction or
      #   genesis block for orderer related parameters
      #
      ################################################################################

              
      Network Orderer name [Orderer]: 
      Type ['etcdraft', 'solo', 'kafka'] [etcdraft]: 
      Total Number of Orderer [5]: 
      BatchTimeout [2]: 
      MaxMessageCount [10]: 
      AbsoluteMaxBytes [99 MB]: 
      PreferredMaxBytes [512 KB]: 

      ################################################################################
      #
      #  
      #  SECTION: Organizations
      #
      #
      ################################################################################

              
      How many organizations do you want to create? [2]:  

              Org 1 
                      Name: ORG1
                      Domain [org1.com]: 
                      MSPDIR [org1.com]: 
                      Number of peers [2]: 

              Org 2 
                      Name: ORG2
                      Domain [org2.com]: 
                      MSPDIR [org2.com]: 
                      Number of peers [2]: 

      ################################################################################
      #
      #
      #  SECTION: ChainCode
      #
      #
      ################################################################################

              
      Do you want to generate a chaincode? ['YES', 'NO'] [YES]: 
      Name: authentication
      Language ['go', 'node', 'java'] [go]: 2
      Directory (Use the absolute path): ~/path_to_the_chaincode
      Do you want to run this chaincode for organization 'ORG1'  ['YES', 'NO', 'N', 'Y', 'TRUE', 'FALSE']:n
      Do you want to run this chaincode for organization 'ORG2'  ['YES', 'NO', 'N', 'Y', 'TRUE', 'FALSE']:y
      [sudo] password for blackcreek: 

      ################################################################################
      #
      #   SECTION: Composer Explorer
      #
      #   - This section will create a Hyperledger Explorer UI to view the blockchain
      #     transaction and configuration.
      #
      ################################################################################
              
      Do you want to install Hyperledger composer? ['YES', 'NO', 'N', 'Y', 'TRUE', 'FALSE']:n

      ```

## `Other command line options`

  |**options**|**Description**|
  |:---------|:---------------|
  | `--version`   |Display the current blocknet version|
  |   | |


