### Documentation

This is the way I intepreted the assignment:

It doesn't mention that I need to create instances, therefore
I just created the neccecary compounds per account.

* Each account needs 1 VPC with a different CIDR block per account.
I saved the information about the accounts in a dict, with the correct CIDR and account name.

* Each account needs 3 different subnets (private, public, protected).
They need to be assiged different IPs, so I looped through all avaliable IPs,
  and assigned the first one avaliable.

* Adding one route table to each of the subnets

* Create one InternetGateWay and attach it to the VPC.

* Create an ACL to the VPC, then add an association to each of the subnets.

* Create an outbound_http_acl rule, this will allow outbound traffic to flow through the public subnet, on port 80.

* Create an outbound_http_acl rule, which will deny outbound traffic to the private subnet, on port 80 (internet access)
  
* Create an Elastic IP and a NAT. To allow access to the internet with outbound traffic.

* Last we need to print out the template to json files.

### Conclusion

This assignment have been intresting. I have learnt a lot, due to the research I had to do on AWS cloudformation, 
and the Troposhere library. However, I haven't used cloudformation before, there were some problems along the way. 

* I tried to add Tags to all resources I added, but some functions didn't allow tags as a parameter.

* I was unable to find out how to add configs to the NAT, I'm unsure how to enable the port 80 on the NAT.

Created by:
Jakob Johansson