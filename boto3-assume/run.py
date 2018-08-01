# Test script to assume into a different AWS account using sts assume-role 
# keep those session credentials in memory and then invoke api calls 
# across 2 AWS endpoints using those credentials. 

# takes 2 command line options 
# --email=<your-email> or -e <your-email>
# --token=<your-mfa-token> or -t <your-mfa-token>
# if either option are not supplied the script will prompt for them

# at present it just lists the number of S3 buckets and the name 
# of the first bucket it finds 

# it then lists all the ingress and egresss cidrs for security 
# groups in all regions specified in the regions array

from aws.GdsAwsClient import GdsAwsClient
from aws.GdsS3Client import GdsS3Client
from aws.GdsEc2Client import GdsEc2Client
from aws.GdsSupportClient import GdsSupportClient
import json
from optparse import OptionParser

# allow user to supply email and token as script options
parser = OptionParser()
parser.add_option("-e", "--email", dest="email", default="", 
                  help="Your gov.uk email")
parser.add_option("-t", "--token", dest="token", default="",
                  help="Your MFA auth token")

# parse command line options
(options, args) = parser.parse_args()


# get the user details from stdin if not specified
if options.email == "": 
    options.email = input("Email? ")

if options.token == "":
    options.token = input("MFA? ")

# temp hard code existing account and role name
regions = ["eu-west-1","eu-west-2"]
account = "779799343306"
role = "AdminRole"

### Assume Role ###
aws_client = GdsAwsClient()
# assume role into target account 
assumed = aws_client.assume_role(account,role,options.email,options.token)
session = aws_client.get_session(account,role)

print(session['AccessKeyId'])

### S3  ###
print ("### S3  ###")
s3_client = GdsS3Client()

# retrieve bucket list 
buckets = s3_client.get_bucket_list(session)
# output number of buckets
print("Found " + str(len(buckets)) + " buckets:\n")

for bucket in buckets: 

    # output bucket name
    print("Bucket name: " + bucket['Name'] + "\n")
    policy = s3_client.get_bucket_policy(session, bucket['Name'])
    print("Policy: " + policy + "\n")

### EC2 ###
print ("### EC2 ###")
ec2_client = GdsEc2Client()

# describe security groups
for region in regions:
    
    print(f"#### REGION: {region} ####")
    groups = ec2_client.describe_security_groups(session, region)

    for group in groups:

        print(group['GroupName'])
        
        print(" ingress ")
        for perm in groups[0]['IpPermissions']:
            
            if 'FromPort' in perm.keys(): 
                from_port = perm['FromPort']
            else: 
                from_port = 'Anywhere'

            if 'ToPort' in perm.keys():
                to_port = perm['ToPort']
            else: 
                to_port = 'Anywhere'

            ports = f"{from_port}>{to_port}"

            for cidr in perm['IpRanges']:
                cidr_range = cidr['CidrIp']
                if 'Description' in cidr.keys():
                    cidr_desc = cidr['Description']
                else: 
                    cidr_desc = "No description"
                    
                print(f"{ports} = {cidr_range}: {cidr_desc}")


        print(" egress ")
        for perm in groups[0]['IpPermissionsEgress']:
            
            if 'FromPort' in perm.keys(): 
                from_port = perm['FromPort']
            else: 
                from_port = 'Anywhere'

            if 'ToPort' in perm.keys():
                to_port = perm['ToPort']
            else: 
                to_port = 'Anywhere'

            ports = f"{from_port}>{to_port}"

            for cidr in perm['IpRanges']:
                cidr_range = cidr['CidrIp']
                if 'Description' in cidr.keys():
                    cidr_desc = cidr['Description']
                else: 
                    cidr_desc = "No description"

                print(f"{ports} = {cidr_range}: {cidr_desc}")


### Support ###
print ("### Support ###")
support_client = GdsSupportClient()

# retrieve bucket list 
checks = support_client.describe_trusted_advisor_checks(session)
#
for check in checks: 
    

    result = support_client.describe_trusted_advisor_check_result(session, check['id'])
    if 'resourcesSummary' in result.keys():

        if result['resourcesSummary']['resourcesProcessed'] > 0: 
            print(check['id'])
            print("check name: " + check['name'] + "\n")
            print("description: " + check['description'] + "\n")
            print("category: " + check['category'] + "\n   stats:\n")

            print ("processed: " + str(result['resourcesSummary']['resourcesProcessed']))
            print ("flagged: " + str(result['resourcesSummary']['resourcesFlagged']))
            print ("ignored: " + str(result['resourcesSummary']['resourcesIgnored']))
            print ("supressed: " + str(result['resourcesSummary']['resourcesSuppressed']))
            print ("\n")
