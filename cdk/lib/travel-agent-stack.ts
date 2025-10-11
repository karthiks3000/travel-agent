import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';
import { CognitoStack } from './cognito-stack';

export interface TravelAgentStackProps extends cdk.StackProps {
  environment: string;
}

export class TravelAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: TravelAgentStackProps) {
    super(scope, id, props);

    // Create Cognito authentication infrastructure
    const cognitoStack = new CognitoStack(this, 'CognitoStack', {
      environment: props.environment,
    });

    // Create S3 bucket for AgentCore Gateway OpenAPI specifications
    const gatewayBucket = new s3.Bucket(this, 'GatewayOpenAPIBucket', {
      bucketName: `travel-agent-gateway-${props.environment}-${cdk.Aws.ACCOUNT_ID}-${cdk.Aws.REGION}`,
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Be careful in production
      lifecycleRules: [
        {
          id: 'DeleteIncompleteMultipartUploads',
          enabled: true,
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7)
        }
      ]
    });

    // Output the Cognito configuration for the frontend
    new cdk.CfnOutput(this, 'CognitoUserPoolId', {
      value: cognitoStack.userPool.userPoolId,
      description: 'Cognito User Pool ID for frontend configuration',
      exportName: `TravelAgent-${props.environment}-UserPoolId`,
    });

    new cdk.CfnOutput(this, 'CognitoUserPoolClientId', {
      value: cognitoStack.userPoolClient.userPoolClientId,
      description: 'Cognito User Pool Client ID for frontend configuration',
      exportName: `TravelAgent-${props.environment}-UserPoolClientId`,
    });

    new cdk.CfnOutput(this, 'CognitoRegion', {
      value: this.region,
      description: 'AWS Region for Cognito configuration',
      exportName: `TravelAgent-${props.environment}-Region`,
    });

    // Create S3 bucket for frontend hosting
    const frontendBucket = new s3.Bucket(this, 'FrontendBucket', {
      bucketName: `travel-agent-frontend-${props.environment}-${cdk.Aws.ACCOUNT_ID}-${cdk.Aws.REGION}`,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL, // Required for OAC
      objectOwnership: s3.ObjectOwnership.BUCKET_OWNER_ENFORCED, // Required for OAC
      versioned: true, // For rollback capability
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // Be careful in production
      autoDeleteObjects: true, // For dev environment cleanup
      lifecycleRules: [
        {
          id: 'DeleteIncompleteMultipartUploads',
          enabled: true,
          abortIncompleteMultipartUploadAfter: cdk.Duration.days(7)
        }
      ]
    });

    // Create Origin Access Identity for secure S3 access
    const oai = new cloudfront.OriginAccessIdentity(this, 'FrontendOAI', {
      comment: `OAI for Travel Agent Frontend - ${props.environment}`,
    });

    // Grant the OAI read access to the S3 bucket
    frontendBucket.grantRead(oai);

    // Create S3 Origin for CloudFront
    const s3Origin = new origins.S3Origin(frontendBucket, {
      originAccessIdentity: oai,
    });

    // Create CloudFront Distribution for frontend hosting
    const distribution = new cloudfront.Distribution(this, 'FrontendDistribution', {
      comment: `Travel Agent Frontend Distribution - ${props.environment}`,
      defaultBehavior: {
        origin: s3Origin,
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        compress: true,
      },
      // Additional behaviors for static assets with longer caching
      additionalBehaviors: {
        '/assets/*': {
          origin: s3Origin,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
          compress: true,
        },
        '/static/*': {
          origin: s3Origin,
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
          compress: true,
        },
      },
      defaultRootObject: 'index.html',
      // Error responses for SPA routing
      errorResponses: [
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0),
        },
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0),
        },
      ],
      // Price class optimized for North America
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100,
      enableIpv6: true,
    });

    // Output Gateway S3 bucket name for deployment scripts
    new cdk.CfnOutput(this, 'GatewayBucketName', {
      value: gatewayBucket.bucketName,
      description: 'S3 bucket name for Gateway OpenAPI specifications',
      exportName: `TravelAgent-${props.environment}-GatewayBucket`,
    });

    // Output frontend hosting configuration
    new cdk.CfnOutput(this, 'FrontendBucketName', {
      value: frontendBucket.bucketName,
      description: 'S3 bucket name for frontend hosting',
      exportName: `TravelAgent-${props.environment}-FrontendBucket`,
    });

    new cdk.CfnOutput(this, 'CloudFrontDistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront Distribution ID for cache invalidation',
      exportName: `TravelAgent-${props.environment}-DistributionId`,
    });

    new cdk.CfnOutput(this, 'CloudFrontDistributionDomainName', {
      value: distribution.distributionDomainName,
      description: 'CloudFront Distribution domain name for frontend access',
      exportName: `TravelAgent-${props.environment}-DistributionDomain`,
    });

    new cdk.CfnOutput(this, 'FrontendUrl', {
      value: `https://${distribution.distributionDomainName}`,
      description: 'Frontend application URL',
      exportName: `TravelAgent-${props.environment}-FrontendUrl`,
    });

  }
}
