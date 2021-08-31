
### Work Assignment

Cloud Platform, Viaplay
Thank you for taking the time to do our assignment! 

Your solution should be written in  Python 3 and use the Troposphere library which is used to generate Cloudformation templates. We use the same tools internally to create deployment stacks in AWS. This assignment will help us see your understanding  of project scope, coding style, attention to detail and approach to problem solving.

Once you have finished please package and deliver your solution so that we can run it. A zip file or link to an online repository is fine. Please ensure to include any documentation for your solution as well.

 

Assignment
The Growth team has created 3 new AWS accounts (Growth-Dev, Growth-Stage, Growth-Prod) and would like you to develop a solution to create Cloudformation templates that set-up some base infrastructure.

Some considerations:
They may want to use the same tool to add additional accounts in the future.
How you might test/validate your generated templates.

They have requested that the tool initially creates templates for the accounts as follows:

Each account should have a VPC with 

Dev:
* VPC IP: 10.0.0.0/
* Netmask: 255.255.255.0	
* DNS Support enabled
* Default instance tenancy

Stage:
* VPC IP: 10.1.0.0/18 HostMin:   10.1.0.1    -  10.1.63.254  
* Netmask: 255.255.192.0
* DNS Support and DNS Hostnames enabled
* Default instance tenancy

Prod:
* VPC IP: 10.2.0.0/18	HostMin:   10.2.0.1  -  10.2.63.254  
* Netmask: 255.255.192.0
* DNS Support and DNS Hostnames enabled
* Default instance tenancy

Each account should have the following multi-az subnets. 

The VPC IPs should be spread as evenly as possible between the az’s.

Private:

* No internet access

Public
* Outbound internet access

Protected
* Outbound internet access via NAT

Tags should be added to each resource for billing purposes. You may decide which tags to add.
