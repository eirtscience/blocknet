

def crytoconfig(data):

    template = '''
    # Copyright IBM Corp. All Rights Reserved.
  #
  # SPDX-License-Identifier: Apache-2.0
  #

  # ---------------------------------------------------------------------------
  # "OrdererOrgs" - Definition of organizations managing orderer nodes
  # ---------------------------------------------------------------------------
  OrdererOrgs:
    # ---------------------------------------------------------------------------
    # Orderer
    # ---------------------------------------------------------------------------
    - Name: Orderer
      Domain: blackcreek.tech
      EnableNodeOUs: true
      # ---------------------------------------------------------------------------
      # "Specs" - See PeerOrgs below for complete description
      # ---------------------------------------------------------------------------
      Specs:
        - Hostname: orderer
        - Hostname: orderer2
        - Hostname: orderer3
        - Hostname: orderer4
        - Hostname: orderer5

  # ---------------------------------------------------------------------------
  # "PeerOrgs" - Definition of organizations managing peer nodes
  # ---------------------------------------------------------------------------
  PeerOrgs:
    # ---------------------------------------------------------------------------
    # Org1
    # ---------------------------------------------------------------------------
    - Name: DC
      Domain: dc.blackcreek.tech
      EnableNodeOUs: true
      # ---------------------------------------------------------------------------
      # "Specs"
      # ---------------------------------------------------------------------------
      # Uncomment this section to enable the explicit definition of hosts in your
      # configuration.  Most users will want to use Template, below
      #
      # Specs is an array of Spec entries.  Each Spec entry consists of two fields:
      #   - Hostname:   (Required) The desired hostname, sans the domain.
      #   - CommonName: (Optional) Specifies the template or explicit override for
      #                 the CN.  By default, this is the template:
      #
      #                              "{\\{.Hostname}}.{\\{.Domain}}"
      #
      #                 which obtains its values from the Spec.Hostname and
      #                 Org.Domain, respectively.
      # ---------------------------------------------------------------------------
      # Specs:
      #   - Hostname: foo # implicitly "foo.org1.blackcreek.tech"
      #     CommonName: foo27.org5.blackcreek.tech # overrides Hostname-based FQDN set above
      #   - Hostname: bar
      #   - Hostname: baz
      # ---------------------------------------------------------------------------
      # "Template"
      # ---------------------------------------------------------------------------
      # Allows for the definition of 1 or more hosts that are created sequentially
      # from a template. By default, this looks like "peer%\\d" from 0 to Count-1.
      # You may override the number of nodes (Count), the starting index (Start)
      # or the template used to construct the name (Hostname).
      #
      # Note: Template and Specs are not mutually exclusive.  You may define both
      # sections and the aggregate nodes will be created for you.  Take care with
      # name collisions
      # ---------------------------------------------------------------------------
      Template:
        Count: 2
        # Start: 5
        # Hostname: {{.Prefix}}{{.Index}} # default
      # ---------------------------------------------------------------------------
      # "Users"
      # ---------------------------------------------------------------------------
      # Count: The number of user accounts _in addition_ to Admin
      # ---------------------------------------------------------------------------
      Users:
        Count: 1
    # ---------------------------------------------------------------------------
    # Org2: See "Org1" for full specification
    # ---------------------------------------------------------------------------
    - Name: DP
      Domain: dp.blackcreek.tech
      EnableNodeOUs: true
      Template:
        Count: 2
      Users:
        Count: 1

    - Name: BLACKCREEK
      Domain: blackcreek.tech
      EnableNodeOUs: true
      Template:
        Count: 2
      Users:
        Count: 1

    '''.format(**data)

    return template
