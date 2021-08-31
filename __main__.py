from __future__ import print_function
import iptools
from troposphere import Join, Output, GetAZs, Select, Export, Ref, Tags, Template, ec2, GetAtt
from troposphere.ec2 import PortRange, NetworkAcl, Route, \
    VPCGatewayAttachment, SubnetRouteTableAssociation, Subnet, RouteTable, \
    NetworkAclEntry, SubnetNetworkAclAssociation, InternetGateway

template = Template()


def make_name(component_name):
    return Join('', [component_name, ' - ', Ref('AWS::StackName')])


accounts = {
    "Dev": "10.0.0.0/24",  # avaliable hosts: 10.0.0.1 - 10.0.0.254
    "Stage": "10.1.0.0/18",  # avaliable hosts: 10.1.0.1 - 10.1.63.254
    "Production": "10.2.0.0/18"  # avaliable hosts: 10.2.0.1 - 10.2.63.254
}

account_name = list(accounts.keys())
account_cidr_block = list(accounts.values())

# Loop through the account_names, and create all the components it needs per account
for account_name, value in accounts.items():
    # Create a VPC, adding tag
    vpc_tags = Tags(Network="public", Name=make_name(account_name))
    VPC = template.add_resource(ec2.VPC(
        account_name + 'VPC', CidrBlock=value, EnableDnsHostnames=True, EnableDnsSupport=True,
        InstanceTenancy="default", Tags=vpc_tags)
    )
    # increases the index by 1
    index = 1

    # Addubg the VPC to the template
    template.add_output(Output(account_name + "VPC", Description="Creating VPC for " + account_name +
                                                                 " CIDR: " + value, Value=Ref(VPC),
                               Export=Export(name="VPC")))

    # Give an avaliable host ip to each subnets
    avaliable_hosts = iptools.IpRange(value)

    # Save the notation to a variable
    ip_notation = value[8:11]

    # Create a subnet for the private subnet
    subnetprivate = template.add_resource(
        Subnet(account_name + 'subnetPrivate', CidrBlock=avaliable_hosts[index] + ip_notation, VpcId=Ref(VPC),
               # 10.0.0.1/24
               AvailabilityZone=Select(index, GetAZs(Ref('AWS::Region'))),
               Tags=Tags(Network="public", Name=make_name(avaliable_hosts[index]))
               )
    )
    index += 1
    # Create a subnet for the public subnet
    subnetpublic = template.add_resource(
        Subnet(account_name + 'subnetPublic', CidrBlock=avaliable_hosts[index] + ip_notation, VpcId=Ref(VPC),
               # '10.0.0.2/24'
               AvailabilityZone=Select(index, GetAZs(Ref('AWS::Region'))),
               Tags=Tags(Network="public", Name=make_name(avaliable_hosts[index]))
               )
    )
    # Create a subnet for the protected subnet
    index += 1
    subnetprotected = template.add_resource(
        Subnet(account_name + 'subnetProtected', CidrBlock=avaliable_hosts[index] + ip_notation, VpcId=Ref(VPC),
               # '10.0.0.3/24'
               AvailabilityZone=Select(index, GetAZs(Ref('AWS::Region'))),
               Tags=Tags(Network="public", Name=make_name(avaliable_hosts[index]))
               )
    )

    # Adding Tags to each of the subnets
    template.add_output([
        Output(account_name + "PrivateSubnet", Description="Create private subnet for " + account_name,
               Value=Ref(subnetprivate), Export=Export(name="private")),
        Output(account_name + "PublicSubnet", Description="Create public subnet for " + account_name,
               Value=Ref(subnetpublic), Export=Export(name="public")),
        Output(account_name + "ProtectedSubnet", Description="Create protected subnet for " + account_name,
               Value=Ref(subnetprotected), Export=Export(name="protected"))
    ])
    # Create Route tags and table
    route_tags = Tags(Name=make_name(account_name + 'Route Table'))
    route_table = template.add_resource(RouteTable(account_name + 'RouteTable', VpcId=Ref(VPC), Tags=route_tags))

    # Append the route to template
    route = template.add_resource(
        Route(
            account_name + 'Route',
            DependsOn='AttachGateway',
            GatewayId=Ref('InternetGateway'),
            DestinationCidrBlock='0.0.0.0/0',
            RouteTableId=Ref(route_table)
        )
    )

    # Attach all our subnets to our new Route Tables
    private_sub_route_table = SubnetRouteTableAssociation(account_name + 'SubnetPrivateRouteAssociation',
                                                        SubnetId=Ref(subnetprivate), RouteTableId=Ref(route_table))
    public_sub_route_table = SubnetRouteTableAssociation(account_name + 'SubnetPublicRouteAssociation',
                                                        SubnetId=Ref(subnetpublic), RouteTableId=Ref(route_table))
    protected_sub_route_table = SubnetRouteTableAssociation(account_name + 'SubnetProtectedRouteAssociation',
                                                        SubnetId=Ref(subnetprotected),RouteTableId=Ref(route_table))

    # Adding Route table to template, and associate it with the right subnet
    template.add_resource(private_sub_route_table)
    template.add_resource(public_sub_route_table)
    template.add_resource(protected_sub_route_table)

    # Create GateWay, which will allow Internet Access through your Route Table.
    # This will make it possible for the accounts to flow traffic inbetween the subnets
    igw = InternetGateway(account_name + 'InternetGateway', Tags=Tags(Name=make_name('IGW')))
    internet_gateway = template.add_resource(igw)

    # Attach out GW to our VPC
    vpc_gw = VPCGatewayAttachment(account_name + 'AttachGateway', VpcId=Ref(VPC),
                                  InternetGatewayId=Ref(internet_gateway))
    gateway_attachment = template.add_resource(vpc_gw)

    # A ACL will allow and deny traffic at a network level to a Subnet.
    # This is what we need to modify our private subet.
    # We still want traffic to flow between our account.
    # Deny the traffic on port 80 (internet access)

    # Create one ACL for the VPC
    network_acl = template.add_resource(
        NetworkAcl(account_name + 'NetworkAcl', VpcId=Ref(VPC), Tags=Tags(
            Name=make_name(account_name + 'Network ACL')))
    )

    # Create an ACL for each subnet, this will make it possible for the subnets to flow trafic between
    subnetPrivate_network_acl_association = template.add_resource(
        SubnetNetworkAclAssociation(
            account_name + 'SubnetPrivateNetworkAclAssociation',
            SubnetId=Ref(subnetprivate),
            NetworkAclId=Ref(network_acl),
        ))

    subnetPublic_network_acl_association = template.add_resource(
        SubnetNetworkAclAssociation(
            account_name + 'SubnetPublicNetworkAclAssociation',
            SubnetId=Ref(subnetpublic),
            NetworkAclId=Ref(network_acl),
        ))

    subnetprotected_network_acl_association = template.add_resource(
        SubnetNetworkAclAssociation(
            account_name + 'SubnetProtectedNetworkAclAssociation',
            SubnetId=Ref(subnetprotected),
            NetworkAclId=Ref(network_acl),
        ))

    # This will open the port 80 and allow internet access to the public subnet
    outbound_http_acl_public = template.add_resource(
        NetworkAclEntry(
            account_name + 'OutBoundHTTPNetworkAclEntryPrivate',
            # Tags=Tags(Name=make_name('Allow port 80')),
            NetworkAclId=Ref(subnetPublic_network_acl_association),
            RuleNumber='100',
            Protocol='6',
            PortRange=PortRange(To='80', From='80'),
            Egress='true',
            RuleAction='allow',
            CidrBlock='0.0.0.0/0',
        ))

    # This will deny the port 80 to the private subnet
    outbound_http_acl_private = template.add_resource(
        NetworkAclEntry(
            account_name + 'OutBoundHTTPNetworkAclEntryPublic',
            NetworkAclId=Ref(subnetPrivate_network_acl_association),
            RuleNumber='100',
            Protocol='6',
            PortRange=PortRange(To='80', From='80'),
            Egress='true',
            RuleAction='deny',
            CidrBlock='0.0.0.0/0',
        ))
    # Adding Elastic IP, to connect with NAT, to allow access to internet with outbound traffic
    nat_eip = template.add_resource(
        ec2.EIP(
            account_name + "NatEip",
            Domain="vpc",
        )
    )

    # Adding the subnet to the NatGateway
    nat = template.add_resource(
        ec2.NatGateway(
            account_name + "Nat",
            AllocationId=GetAtt(nat_eip, "AllocationId"),
            SubnetId=Ref(subnetprotected),
        )
    )
    # Adding the Nat to the subnet route table
    template.add_resource(
        ec2.Route(
            account_name + "NatRoute",
            RouteTableId=Ref(protected_sub_route_table),
            DestinationCidrBlock="0.0.0.0/0",
            NatGatewayId=Ref(nat),
        )
    )
    # Append the template to a json file
    with open(account_name + ".json", mode="w") as w:
        w.write(template.to_json())
