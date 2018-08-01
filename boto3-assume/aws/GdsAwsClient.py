# GdsAwsClient
# Manage sts assume-role calls and temporary credentials
import os
import boto3
import json
import configparser

class GdsAwsClient:

    # initialise empty dictionaries for clients and assume role sessions
    resources = dict()
    clients = dict()
    sessions = dict()

    # retrieve default key and secret from ~/.aws/credentials file
    def load_credentials(self): 

        # implement ini file parser for user home configuration file
        config = configparser.ConfigParser()
        home = os.getenv("HOME")
        config.read(f"{home}/.aws/credentials")

        # store the key and secret locally in the class 
        # ideally these should be protected/private variables 
        # there doesn't seem to be a way to do that in python
        self.key = config['default']['aws_access_key_id']
        self.secret = config['default']['aws_secret_access_key']
        #print(self.key)
        return True
        
    # store temporary credentials from sts-assume-roles 
    # session names are based on the account and role
    # {account-number}-{role-name}
    # eg: 779799343306-AdminRole
    def get_session_name(self, account, role=''): 
        if (role == ""):
            session_name = account
        else: 
            session_name =  f"{account}-{role}"
        return session_name

    # create clients once and reuse - store by client name 
    # which encompasses the account, role and service
    # {account-number}-{role-name}-{region}-{service}
    # eg: 779799343306-AdminRole-eu-west-2-s3
    def get_client_name(self, service_name, session_name='default', region='eu-west-2'):
        return f"{session_name}-{region}-{service_name}"

    # gets a boto3.client class for the given service, account and role 
    # if the client has already been defined in self.clients it is 
    # reused instead of creating a new instance
    def get_boto3_client(self, service_name, account='default', role='', region=None): 

        session_name = self.get_session_name(account, role)
        client_name = self.get_client_name(service_name, session_name, region)

        if not client_name in self.clients: 

            if (session_name == 'default'):
                client = self.get_default_client(service_name, account, role, region)
            else: 
                client = self.get_assumed_client(service_name, account, role, region)
        
        else: 
            client = self.clients[client_name]

        return client

    # gets a boto3.client with the default credentials 
    def get_default_client(self, service_name, account='default', role='', region=None):

        session_name = self.get_session_name(account, role)
        client_name = self.get_client_name(service_name, session_name, region)

        if not hasattr(self,'key'): 
            self.load_credentials()

        self.clients[client_name] = boto3.client(
            service_name,
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
            region_name=region
        )  
        return self.clients[client_name]

    # gets a boto3.client with the temporary session credentials 
    # resulting from sts assume-role command
    def get_assumed_client(self, service_name, account='default', role='', region=None):

        session_name = self.get_session_name(account, role)
        client_name = self.get_client_name(service_name, session_name)
        
        if not session_name in self.sessions.keys(): 
            self.assume_role(account, role)

        session = self.get_session(session_name)
        self.clients[client_name] = boto3.client(
            service_name,
            aws_access_key_id=session['AccessKeyId'],
            aws_secret_access_key=session['SecretAccessKey'],
            aws_session_token=session['SessionToken'],
            region_name=region
        )    

        return self.clients[client_name]

    def get_boto3_session_client(self, service_name, session, region=None):
       
        client = boto3.client(
            service_name,
            aws_access_key_id=session['AccessKeyId'],
            aws_secret_access_key=session['SecretAccessKey'],
            aws_session_token=session['SessionToken'],
            region_name=region
        )    

        return client

    def get_boto3_resource(self,resource_name):
        
        if not resource_name in self.resources: 
            self.resources[resource_name] = boto3.resource(resource_name)    

        return self.resources[resource_name]    

    # issue the sts assume-role command and store the returned credentials
    def assume_role(self,account,role,email="",token=""): 

        '''
        Example response
        {
            'Credentials': {
                'AccessKeyId': 'string',
                'SecretAccessKey': 'string',
                'SessionToken': 'string',
                'Expiration': datetime(2015, 1, 1)
            },
            'AssumedRoleUser': {
                'AssumedRoleId': 'string',
                'Arn': 'string'
            },
            'PackedPolicySize': 123
        }
        '''
        try:
            sts = self.get_boto3_client('sts')
            
            role_arn = f"arn:aws:iam::{account}:role/{role}"
            print(f"Assume role: {role_arn}")

            mfa_serial = f"arn:aws:iam::622626885786:mfa/{email}"
            session_name = self.get_session_name(account,role)

            assumed_credentials = sts.assume_role(
                RoleSessionName=session_name,
                RoleArn=role_arn,
                SerialNumber=mfa_serial,
                TokenCode=token
            )

            role_assumed = 'Credentials' in assumed_credentials.keys()
            
            if role_assumed: 
                print(assumed_credentials['Credentials']['Expiration'])
                self.sessions[session_name] = assumed_credentials['Credentials']
            else:    
                raise Exception("Assume role failed")

        except Exception as exception:
            print(exception)
            role_assumed = False

        return role_assumed

    # get_session returns the existing session if it already exists 
    # or assumes the role and returns the new session if it doesn't 
    def get_session(self,account,role=""): 

        try:
            session_name = self.get_session_name(account,role)
            
            if not session_name in self.sessions.keys():

                assumed = self.assume_role(account,role)
                if not assumed: 
                    raise Exception("Assume role failed")

            session = self.sessions[session_name]

        except Exception as exception:
            print(exception)
            session = False

        return session
