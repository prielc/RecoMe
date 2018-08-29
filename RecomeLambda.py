from __future__ import print_function

import boto3
from decimal import Decimal
import json
import urllib

print('Loading function')

rekognition = boto3.client('rekognition')


# --------------- Helper Functions to call Rekognition APIs ------------------

def detect_labels(bucket, key):
    response = rekognition.detect_labels(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response
	
def compare_faces(bucket, key):
    target_bucket = 'recome-approved'
    my_target_bucket = s3.Bucket(target_bucket)
    #for obj in my_target_bucket.objects.all():
        # send the obj.key and bucket name to the compare
        #print(obj.key)
    	response = rekognition.compare_faces(
    	    SourceImage={"S3Object": {"Bucket": bucket,"Name": key,}},
    		TargetImage={"S3Object": {"Bucket": bucket_target,"Name": key_target,}},
    	    #SimilarityThreshold=threshold,
    	)
	return response['SourceImageFace'], response['FaceMatches']


# --------------- Main handler ------------------


def lambda_handler(event, context):
    '''Demonstrates S3 trigger that uses
    Rekognition APIs to detect faces, labels and index faces in S3 Object.
    '''
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))
    try:
        # Calls rekognition DetectFaces API to detect faces in S3 object
        response = compare_faces(bucket, key)
        
        tosend=""
 
        for Label in response["Labels"]:
             # print (Label["Name"] + Label["Confidence"])
         
            print ('{0} - {1}%'.format(Label["Name"], Label["Confidence"]))
            tosend+= '{0} - {1}% '.format(Label["Name"], Label["Confidence"])

        # Calls rekognition DetectLabels API to detect labels in S3 object
        #response = detect_labels(bucket, key)

        # Calls rekognition IndexFaces API to detect faces in S3 object and index faces into specified collection
        #response = index_faces(bucket, key)

        # Print response to console.
        print(response)

        return response
    except Exception as e:
        print(e)
        print("Error processing object {} from bucket {}. ".format(key, bucket) +
              "Make sure your object and bucket exist and your bucket is in the same region as this function.")
        raise e
