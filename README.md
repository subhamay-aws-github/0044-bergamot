# Project Bergamot: Generating thumbnail from images uploaded to a S3 bucket.

Creating thumnail of images using AWS Lambda with Python runtime and storing the metadata in a DynamoDB table.

## Description

This is a sample project to demonstrate the capability of creating thumbnail images from original images uploaded to a S3 bucket. The metadata of the image is stored in a DynamoDB table. When the source image is deleted, the thumbail also gets deleted along with the item stored in the DynamoDB table. The DynamoDB items are exposed to the outside work using a Rest API endpoint, using which the users can view the list of original and thumbnail images available in the S3 bucket.The stack is created using Serverless framework (https://www.serverless.com)

![Project Bergamot - Design Diagram]( https://blog.subhamay.com/wp-content/uploads/2023/01/44_Bergamot_1_1_Architecture_Diagram-1024x505.png")

## Getting Started

### Dependencies

* AWS CLI should be installed and configured.
* Latest version of Node.js must be installed.
* Serverless (https://www.serverless.com) framework should be installed and configured.

### Installing

clone the repo to a local directory.

### Deployment

In order to deploy the example, you need to run the following command:

```
$ serverless deploy
```

After running deploy, you should see output similar to:

```bash
Deploying aws-node-project to stage dev (us-east-1)

✔ Service deployed to stack aws-node-project-dev (112s)

functions:
  hello: aws-node-project-dev-hello (1.5 kB)
```

### Invocation

After successful deployment, you can invoke the deployed function by using the following command:

```bash
serverless invoke --function hello
```

Which should result in response similar to the following:

```json
{
    "statusCode": 200,
    "body": "{\n  \"message\": \"Go Serverless v3.0! Your function executed successfully!\",\n  \"input\": {}\n}"
}
```

### Local development

You can invoke your function locally by using the following command:

```bash
serverless invoke local --function hello
```

Which should result in response similar to the following:

```
{
    "statusCode": 200,
    "body": "{\n  \"message\": \"Go Serverless v3.0! Your function executed successfully!\",\n  \"input\": \"\"\n}"
}
```

### Executing program

* Use Postman to invove the Rest API endpoints.


## Help

Post message in my blog (https://blog.subhamay.com)


## Authors

Contributors names and contact info

Subhamay Bhattacharyya  - [subhamoyb@yahoo.com](https://subhamay.blog)

## Version History

* 0.1
    * Initial Release

## License

This project is licensed under Subhamay Bhattacharyya. All Rights Reserved.

## Acknowledgments

Inspiration, code snippets, etc.
* [Paulo Dichone ](https://www.linkedin.com/in/paulo-dichone/)

