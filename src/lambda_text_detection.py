from urllib import request
import boto3
from decimal import Decimal
import json
import os
import base64
from botocore.exceptions import ClientError

# from helper import AwsHelper, S3Helper, DynamoDBHelper
# from og import OutputGenerator
# import datastore

# Parameters from requests
# source - file or s3 location
# return_format - text or full
# file_location - s3 location if source is file. Example: s3://jm-uswest2-test-1/test-imgs/ocr-img-1.png
# HTTP_BODY - A binary file string or S3 location string

textract_client = boto3.client('textract')

# Get contents from OCR results
def getPageText(jobResults):

    pageTextList = []
    pageListLen  = 0
    #validTextTypes = ('LINE', 'WORD')
    validTextTypes = ('LINE') # LINE blocks contain WORD blocks 
    lineBreaker = "\n"
    print('### jobResults:', jobResults)

    for docs in jobResults:
        print('IN FUNCTION DOCS:', docs)

        if 'Blocks' in docs:

            for blocks in docs['Blocks']:

                # Have to deal with empty pages
                if ('PAGE' == blocks['BlockType']):

                    if 'Page' in blocks:
                        pageNum = int(blocks['Page'])
                        pageId = pageNum - 1
                    else:
                        pageNum = 1
                        pageId = 0

                    if (pageListLen < pageNum):
                        pageTextList.append('')
                        pageListLen += 1

                if blocks['BlockType'] in validTextTypes:

                    print('###Block Page Number: {}, PageTextList length: {}, Page Index: {}.'.format(pageNum, pageListLen, pageId))
                    
                    if blocks['Confidence'] < 70: # Skip blocks with confidence lower than 70%
                        blocks['Text'] = ' '

                    if '.' != blocks['Text'][-1]: # In order to increase readability, append a space when the last character is not '.'
                        pageTextList[pageId] += blocks['Text'] + ' '
                    else: # Only append line breakers when the last character is '.'
                        pageTextList[pageId] += blocks['Text'] + lineBreaker
                    
                    #print('Sample data contains valid text.')
                    print('### PAGE #{} TEXT LENGTH IS {}KB.'.format(pageNum, (len(pageTextList[pageId])/1024)))

    if pageTextList:
        return pageTextList
    else:
        return False

def lambda_handler(event, context):

    s3_paths = []

    # S3 testing path: s3://jm-uswest2-test-1/test-imgs/ocr-img-1.png
    print("event: {}".format(event))
    request_parameters = event['pathParameters']
    request_body = event['body']
    
    print("PARAMS: {}".format(request_parameters))

    if not request_body:
        return {
            'statusCode': 400,
            'body': 'Invalid request!'
        }

    # Base64 decode
    if event['isBase64Encoded'] == True:
        request_body = base64.b64decode(request_body.encode('utf-8'))
        print('B64 DECODE REQUEST_BODY: ', request_body)

    textract_request_document = {}

    if request_parameters['source'] == 'file':
        # Get the file string from the HTTP Request Body
        print('File handler')

        textract_request_document['Bytes'] = request_body

    else: # Get the S3 location from HTTP Request Body
        # Base64 decode
        if event['isBase64Encoded'] == True:
            request_body = str(request_body, 'utf-8')
            print('### S3 PATH: ', request_body)

        request_body = request_body.replace('s3://', '')
        s3_paths = request_body.split('/', 1)
        print('S3 PATH: ', s3_paths)

        textract_request_document['S3Object'] = {
            'Bucket': s3_paths[0],
            'Name': s3_paths[1]
        }
        
    print('TEXTRACT REQUEST: ', textract_request_document)

    try:
        response = textract_client.detect_document_text(
            Document=textract_request_document
        )
        print('RAW RESPONSE: ', response)

        if request_parameters['return_format'] == 'text':
            doc_pages = []
            doc_pages.append(response)
            print('DOC RESULT: ', doc_pages)

            page_text_list = getPageText(doc_pages)

            if page_text_list:
                del response['Blocks']
                response['Text'] = page_text_list

            # return_body = json.dumps(page_text_list)
            # print('RETURN BODY: ', page_text_list)

        # return_body = json.dumps(response)
        # print('RETURN BODY: ', response)

        # Append the s3 path to the response
        # if 0 in s3_paths and s3_paths[0] != '':
        if len(s3_paths) != 0:
            response['s3_location'] = {
              'bucket': s3_paths[0],
              'key': s3_paths[1]  
            }

        return {'statusCode': 200, 'body': json.dumps(response)}

    except ClientError as e:
        # print('ERROR: ', e)
        return {
            'statusCode': 400,
            'body': json.dumps({
                'msg': 'Amazon Textract OCR failed!',
                'error': e
            })
        }