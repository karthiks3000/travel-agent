// Jest setup file for CDK tests

// Suppress CDK deprecation warnings in tests
process.env.JSII_DEPRECATED = 'quiet';

// Set default AWS region for tests
process.env.CDK_DEFAULT_REGION = 'us-east-1';
process.env.CDK_DEFAULT_ACCOUNT = '123456789012';