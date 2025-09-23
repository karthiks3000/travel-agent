"""
Gateway setup utilities for AgentCore Gateway with Google Maps API integration
"""
import os
import time
import boto3
import json
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


def print_status(message: str):
    """Print success message with green checkmark"""
    print(f"✅ {message}")

def print_warning(message: str):
    """Print warning message with yellow warning symbol"""  
    print(f"⚠️  {message}")

def print_error(message: str):
    """Print error message with red X"""
    print(f"❌ {message}")


def get_or_create_user_pool_domain(cognito_client, user_pool_id: str, region: str) -> str:
    """Ensure user pool has domain and return domain name (AWS Labs pattern)"""
    try:
        # Check if user pool already has a domain
        response = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
        user_pool = response.get('UserPool', {})
        domain = user_pool.get('Domain')
        
        if domain:
            print_status(f"Found existing domain for user pool {user_pool_id}: {domain}")
            return domain
        
        print_status(f"No domain found for user pool {user_pool_id}, creating one...")
        
        # Create domain using AWS Labs pattern - remove underscores and lowercase
        user_pool_id_without_underscore_lc = user_pool_id.replace("_", "").lower()
        
        try:
            cognito_client.create_user_pool_domain(
                Domain=user_pool_id_without_underscore_lc,
                UserPoolId=user_pool_id
            )
            print_status(f"Created domain: {user_pool_id_without_underscore_lc}")
            return user_pool_id_without_underscore_lc
            
        except ClientError as e:
            if "already exists" in str(e).lower() or "domain" in str(e).lower():
                # Domain name conflict, try with timestamp suffix
                import time
                timestamp_suffix = str(int(time.time()))[-4:]  # Last 4 digits
                domain_name = f"{user_pool_id_without_underscore_lc}{timestamp_suffix}"
                
                try:
                    cognito_client.create_user_pool_domain(
                        Domain=domain_name,
                        UserPoolId=user_pool_id
                    )
                    print_status(f"Created domain with timestamp suffix: {domain_name}")
                    return domain_name
                except ClientError as e2:
                    print_error(f"Failed to create domain even with suffix: {e2}")
                    raise e2
            else:
                raise e
                
    except ClientError as e:
        print_error(f"Error with user pool domain: {e}")
        raise


def get_or_create_resource_server(cognito_client, user_pool_id: str, 
                                  resource_server_id: str, resource_server_name: str, scopes: list):
    """Create or update resource server for Gateway access"""
    try:
        # Check if resource server exists
        try:
            response = cognito_client.describe_resource_server(
                UserPoolId=user_pool_id,
                Identifier=resource_server_id
            )
            print_status(f"Resource server already exists: {resource_server_id}")
            return response['ResourceServer']
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceNotFoundException':
                raise e
        
        # Create new resource server
        response = cognito_client.create_resource_server(
            UserPoolId=user_pool_id,
            Identifier=resource_server_id,
            Name=resource_server_name,
            Scopes=scopes
        )
        print_status(f"Created resource server: {resource_server_id}")
        return response['ResourceServer']
        
    except ClientError as e:
        print_error(f"Error with resource server: {e}")
        raise


def get_or_create_m2m_client(cognito_client, user_pool_id: str, client_name: str, resource_server_id: str):
    """Create or get machine-to-machine client for Gateway authentication (improved with Parameter Store)"""
    try:
        # First check Parameter Store for existing M2M client credentials
        ssm_client = boto3.client('ssm')
        param_prefix = f"/travel-agent/m2m-client/{client_name}"
        
        try:
            # Try to get existing M2M client from Parameter Store
            client_id_param = ssm_client.get_parameter(Name=f"{param_prefix}/client-id", WithDecryption=True)
            client_secret_param = ssm_client.get_parameter(Name=f"{param_prefix}/client-secret", WithDecryption=True)
            
            existing_client_id = client_id_param['Parameter']['Value']
            existing_client_secret = client_secret_param['Parameter']['Value']
            
            # Verify the client still exists in Cognito
            try:
                cognito_client.describe_user_pool_client(
                    UserPoolId=user_pool_id,
                    ClientId=existing_client_id
                )
                print_status(f"Found existing M2M client from Parameter Store: {client_name}")
                return existing_client_id, existing_client_secret
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    print_warning("M2M client in Parameter Store no longer exists in Cognito, creating new one...")
                    # Delete stale parameters
                    ssm_client.delete_parameter(Name=f"{param_prefix}/client-id")
                    ssm_client.delete_parameter(Name=f"{param_prefix}/client-secret")
                else:
                    raise e
                    
        except ClientError as e:
            if e.response['Error']['Code'] != 'ParameterNotFound':
                raise e
            # Parameters don't exist, will create new client
        
        # Create new M2M client only if not found in Parameter Store
        print_status("Creating new M2M client...")
        scope_string = f"{resource_server_id}/gateway:read {resource_server_id}/gateway:write"
        
        response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=client_name,
            GenerateSecret=True,
            AllowedOAuthFlows=['client_credentials'],
            AllowedOAuthScopes=scope_string.split(),
            AllowedOAuthFlowsUserPoolClient=True,
            ExplicitAuthFlows=['ALLOW_REFRESH_TOKEN_AUTH'],  # GitHub reference pattern
            SupportedIdentityProviders=['COGNITO']
        )
        
        client_id = response['UserPoolClient']['ClientId']
        client_secret = response['UserPoolClient']['ClientSecret']
        
        # Store credentials in Parameter Store for future deployments
        ssm_client.put_parameter(
            Name=f"{param_prefix}/client-id",
            Value=client_id,
            Type='String',
            Overwrite=True,
            Description=f'M2M client ID for {client_name}'
        )
        
        ssm_client.put_parameter(
            Name=f"{param_prefix}/client-secret",
            Value=client_secret,
            Type='SecureString',
            Overwrite=True,
            Description=f'M2M client secret for {client_name}'
        )
        
        print_status(f"Created M2M client and stored credentials in Parameter Store: {client_name}")
        return client_id, client_secret
        
    except ClientError as e:
        print_error(f"Error with M2M client: {e}")
        raise


def get_token(user_pool_id: str, client_id: str, client_secret: str, scope: str, region: str, domain_prefix: str = None) -> Dict[str, Any]:
    """Get access token for M2M client using client credentials flow (GitHub reference pattern)"""
    import requests
    
    # Cognito token endpoint - use domain prefix if provided, otherwise fallback to user pool ID format
    if domain_prefix:
        token_url = f"https://{domain_prefix}.auth.{region}.amazoncognito.com/oauth2/token"
        print_status(f"Using Cognito domain: {domain_prefix}")
    else:
        # AWS Labs pattern - remove underscores from user pool ID
        user_pool_id_clean = user_pool_id.replace("_", "")
        token_url = f"https://{user_pool_id_clean}.auth.{region}.amazoncognito.com/oauth2/token"
        print_status(f"Using domain from user pool ID: {user_pool_id_clean}")
    
    # GitHub reference pattern: client_secret_post (credentials in body, not header)
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }
    
    print_status(f"Token request to: {token_url}")
    print_status(f"Using client ID: {client_id}")
    
    try:
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()  # GitHub pattern uses raise_for_status()
        
        token_data = response.json()
        print_status("Successfully obtained access token")
        return token_data
        
    except requests.exceptions.RequestException as e:
        print_error(f"Token request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print_error(f"Response: {e.response.text}")
        raise Exception(f"Token request failed: {str(e)}")


def create_agentcore_gateway_role(role_name: str) -> Dict[str, Any]:
    """Create IAM role for AgentCore Gateway execution (AWS Labs reference pattern)"""
    iam_client = boto3.client('iam')
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    region = boto3.Session().region_name
    
    # AWS Labs reference policy - comprehensive permissions
    role_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AgentCoreGatewayFullAccess",
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*",
                "bedrock:*",
                "agent-credential-provider:*",
                "iam:PassRole",
                "secretsmanager:GetSecretValue",  # Key missing permission!
                "lambda:InvokeFunction",
                "s3:GetObject",
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }]
    }

    # AWS Labs reference assume role policy with conditions
    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AssumeRolePolicy",
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock-agentcore.amazonaws.com"
                },
                "Action": "sts:AssumeRole",
                "Condition": {
                    "StringEquals": {
                        "aws:SourceAccount": f"{account_id}"
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
                    }
                }
            }
        ]
    }

    assume_role_policy_document_json = json.dumps(assume_role_policy_document)
    role_policy_document = json.dumps(role_policy)
    
    try:
        # Try to get existing role first
        try:
            response = iam_client.get_role(RoleName=role_name)
            print_status(f"Updating existing Gateway role: {role_name}")
            
            # Update the role policy with comprehensive permissions
            iam_client.put_role_policy(
                PolicyDocument=role_policy_document,
                PolicyName="AgentCoreGatewayPolicy",
                RoleName=role_name
            )
            print_status(f"Updated Gateway role with comprehensive permissions: {role_name}")
            return response
            
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchEntity':
                raise e
        
        # Create new role using AWS Labs pattern
        print_status(f"Creating new Gateway role: {role_name}")
        agentcore_iam_role = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=assume_role_policy_document_json,
            Description='AgentCore Gateway execution role with comprehensive permissions'
        )

        # Pause to make sure role is created
        time.sleep(5)
        
        # Attach the comprehensive policy
        iam_client.put_role_policy(
            PolicyDocument=role_policy_document,
            PolicyName="AgentCoreGatewayPolicy",
            RoleName=role_name
        )
        
        print_status(f"Created Gateway role with comprehensive permissions: {role_name}")
        return agentcore_iam_role
        
    except ClientError as e:
        print_error(f"Error creating Gateway role: {e}")
        raise


def setup_gateway_infrastructure(user_pool_id: str, openapi_spec_path: str, 
                                google_places_api_key: str, region: str = "us-east-1", 
                                bucket_name: str = None, domain_prefix: str = None) -> Dict[str, Any]:
    """
    Complete Gateway infrastructure setup following AWS Labs pattern
    
    Args:
        user_pool_id: Existing Cognito User Pool ID from CDK
        openapi_spec_path: Path to Google Maps OpenAPI spec file
        google_places_api_key: Google Maps API key
        region: AWS region
        bucket_name: S3 bucket name from CDK (optional, will be inferred if not provided)
        domain_prefix: Cognito domain prefix from CDK (optional, will fallback if not provided)
        
    Returns:
        Dict with gateway_url, gateway_id, credential_provider_arn, access_token
    """
    print_status("Setting up AgentCore Gateway infrastructure...")
    
    # Initialize clients
    cognito_client = boto3.client('cognito-idp', region_name=region)
    gateway_client = boto3.client('bedrock-agentcore-control', region_name=region)
    identity_client = boto3.client('bedrock-agentcore-control', region_name=region)
    s3_client = boto3.client('s3', region_name=region)
    sts_client = boto3.client('sts')
    
    account_id = sts_client.get_caller_identity()['Account']
    
    # Determine bucket name if not provided
    if not bucket_name:
        bucket_name = f'travel-agent-gateway-dev-{account_id}-{region}'
    
    try:
        # Step 1: Ensure User Pool has domain (AWS Labs pattern)
        print_status("Ensuring Cognito User Pool has OAuth domain...")
        domain_name = get_or_create_user_pool_domain(cognito_client, user_pool_id, region)
        
        # Step 2: Setup Cognito resource server and M2M client
        print_status("Setting up Cognito resource server...")
        
        scopes = [
            {"ScopeName": "gateway:read", "ScopeDescription": "Read access to gateway tools"},
            {"ScopeName": "gateway:write", "ScopeDescription": "Write access to gateway tools"}
        ]
        
        resource_server_id = "travel-agent-gateway"
        resource_server_name = "Travel Agent Gateway"
        client_name = "travel-agent-gateway-m2m"
        
        get_or_create_resource_server(cognito_client, user_pool_id, resource_server_id, resource_server_name, scopes)
        client_id, client_secret = get_or_create_m2m_client(cognito_client, user_pool_id, client_name, resource_server_id)
        
        # Step 3: Create API key credential provider
        print_status("Creating Google Maps API key credential provider...")
        
        try:
            # Use AgentCore Identity service to create credential provider
            response = identity_client.create_api_key_credential_provider(
                name="GoogleMapsAPIKeyProvider",
                apiKey=google_places_api_key
            )
            credential_provider_arn = response['credentialProviderArn']
            print_status(f"Created credential provider: {credential_provider_arn}")
        except ClientError as e:
            if "already exists" in str(e):
                print_warning("Credential provider might already exist")
                # Try to list and find existing provider
                credential_provider_arn = f"arn:aws:bedrock-agentcore:{region}:{account_id}:token-vault/default/apikeycredentialprovider/GoogleMapsAPIKeyProvider"
            else:
                raise e
        
        # Step 4: Create Gateway execution role
        print_status("Creating Gateway execution role...")
        gateway_role = create_agentcore_gateway_role("TravelAgentGatewayRole")
        gateway_role_arn = gateway_role['Role']['Arn']
        
        # Step 5: Upload OpenAPI spec to S3
        print_status("Uploading Google Maps OpenAPI spec to S3...")
        
        with open(openapi_spec_path, 'rb') as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key='google-maps-travel-agent-openapi.json',
                Body=f,
                ContentType='application/json'
            )
        
        openapi_s3_uri = f's3://{bucket_name}/google-maps-travel-agent-openapi.json'
        print_status(f"OpenAPI spec uploaded to: {openapi_s3_uri}")
        
        # Step 6: Create Gateway
        print_status("Creating AgentCore Gateway...")
        
        discovery_url = f'https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration'
        
        auth_config = {
            "customJWTAuthorizer": { 
                "allowedClients": [client_id],
                "discoveryUrl": discovery_url
            }
        }
        
        try:
            gateway_response = gateway_client.create_gateway(
                name='TravelAgentGateway',
                roleArn=gateway_role_arn,
                protocolType='MCP',
                authorizerType='CUSTOM_JWT',
                authorizerConfiguration=auth_config,
                description='API Gateway for Travel Agent - supports multiple external services via MCP protocol'
            )
            
            gateway_id = gateway_response["gatewayId"]
            gateway_url = gateway_response["gatewayUrl"]
            print_status(f"Created Gateway: {gateway_id}")
            print_status(f"Gateway URL: {gateway_url}")
            
        except ClientError as e:
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                print_warning("Gateway already exists, checking client ID consistency...")
                # List gateways to find the existing one
                list_response = gateway_client.list_gateways()
                for gateway in list_response.get('items', []):
                    if gateway['name'] == 'TravelAgentGateway':
                        gateway_id = gateway['gatewayId']
                        get_response = gateway_client.get_gateway(gatewayIdentifier=gateway_id)
                        gateway_url = get_response['gatewayUrl']
                        
                        # Check if existing Gateway has the correct client ID
                        existing_allowed_clients = get_response.get('authorizerConfiguration', {}).get('customJWTAuthorizer', {}).get('allowedClients', [])
                        
                        if client_id not in existing_allowed_clients:
                            print_warning(f"Gateway client ID mismatch! Gateway allows: {existing_allowed_clients}, but we have: {client_id}")
                            print_warning("Skipping Gateway auth update to avoid breaking existing functionality")
                            print_status("Using existing Gateway configuration - may cause authentication issues")
                        else:
                            print_status(f"Gateway already configured with correct client ID: {client_id}")
                        
                        print_status(f"Found existing Gateway: {gateway_id}")
                        print_status(f"Gateway URL: {gateway_url}")
                        break
                else:
                    print_error("Could not find existing Gateway")
                    raise e
            else:
                raise e
        
        # Step 7: Create or find Gateway target for Google Maps
        print_status("Setting up Google Maps API target...")
        
        target_config = {
            "mcp": {
                "openApiSchema": {
                    "s3": {
                        "uri": openapi_s3_uri
                    }
                }
            }
        }
        
        # API key credential configuration - Google Maps uses 'key' parameter
        credential_config = [
            {
                "credentialProviderType": "API_KEY",
                "credentialProvider": {
                    "apiKeyCredentialProvider": {
                        "credentialParameterName": "key",  # Google Maps API key parameter
                        "providerArn": credential_provider_arn,
                        "credentialLocation": "QUERY_PARAMETER"
                    }
                }
            }
        ]
        
        try:
            target_response = gateway_client.create_gateway_target(
                gatewayIdentifier=gateway_id,
                name='GoogleMapsPlacesAPI',
                description='Google Maps Places API for restaurant and location search',
                targetConfiguration=target_config,
                credentialProviderConfigurations=credential_config
            )
            print_status("Created Gateway target: GoogleMapsPlacesAPI")
            
        except ClientError as e:
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                print_warning("Gateway target already exists, using existing one...")
                # List targets to find existing one
                list_response = gateway_client.list_gateway_targets(gatewayIdentifier=gateway_id)
                for target in list_response.get('items', []):
                    if target['name'] == 'GoogleMapsPlacesAPI':
                        print_status(f"Found existing target: {target['name']} (ID: {target['targetId']})")
                        break
                else:
                    print_error("Could not find existing target")
                    raise e
            else:
                raise e
        
        # Step 8: Get access token using the created domain
        print_status("Obtaining access token...")
        scope_string = f"{resource_server_id}/gateway:read {resource_server_id}/gateway:write"
        token_response = get_token(user_pool_id, client_id, client_secret, scope_string, region, domain_name)
        access_token = token_response['access_token']
        
        # Debug: Log the client_id used in Gateway vs what will be stored
        print_status(f"Gateway configured with client_id: {client_id}")
        print_status(f"This client_id will be stored for agent access")
        
        # Return configuration
        return {
            'gateway_id': gateway_id,
            'gateway_url': gateway_url,
            'gateway_role_arn': gateway_role_arn,
            'credential_provider_arn': credential_provider_arn,
            'client_id': client_id,  # Same client_id used in Gateway auth_config
            'client_secret': client_secret,
            'access_token': access_token,
            'discovery_url': discovery_url,
            'openapi_s3_uri': openapi_s3_uri
        }
        
    except Exception as e:
        print_error(f"Gateway setup failed: {e}")
        raise


def cleanup_gateway(gateway_id: str, region: str = "us-east-1"):
    """Clean up Gateway resources"""
    try:
        gateway_client = boto3.client('bedrock-agentcore-control', region_name=region)
        
        # Delete Gateway (this will also delete targets)
        gateway_client.delete_gateway(gatewayIdentifier=gateway_id)
        print_status(f"Deleted Gateway: {gateway_id}")
        
    except Exception as e:
        print_error(f"Gateway cleanup failed: {e}")
        raise


def store_gateway_config_in_parameters(config: Dict[str, Any], region: str = "us-east-1"):
    """Store Gateway configuration in Parameter Store for agent access"""
    ssm_client = boto3.client('ssm', region_name=region)
    
    parameters = {
        '/travel-agent/gateway-url': config['gateway_url'],
        '/travel-agent/gateway-id': config['gateway_id'], 
        '/travel-agent/gateway-client-id': config['client_id'],
        '/travel-agent/gateway-client-secret': config['client_secret'],
        '/travel-agent/gateway-credential-provider-arn': config['credential_provider_arn']
    }
    
    for param_name, param_value in parameters.items():
        try:
            ssm_client.put_parameter(
                Name=param_name,
                Value=param_value,
                Type='SecureString' if 'secret' in param_name else 'String',
                Overwrite=True,
                Description=f'Gateway configuration for travel agent'
            )
            print_status(f"Stored parameter: {param_name}")
        except Exception as e:
            print_error(f"Failed to store parameter {param_name}: {e}")
            raise
