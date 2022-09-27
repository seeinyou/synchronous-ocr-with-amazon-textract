# synchronous-ocr-with-amazon-textract
This project includes an Amazon API Gateway API to call Amazon Textract for OCR synchronously 

## Runtime
Python 3.9

## Introduction
The project includes a set of synchronous APIs to receive an uploaded file (or an Amazon S3 path) and execute OCR processing for documents in PDF, JPEG, PNG, and TIFF formats.

## Files
### Lambda functions
#### src
lambda_text_detection.py - Run OCR the input file using Amazon Textract and return OCR results.

### SAM template
template.yaml - The SAM template creates an Amazon API Gateway with a usage plan and API key, and a Lambda function to handle requests from the API Gateway and run OCR process using Amazon Textract.
