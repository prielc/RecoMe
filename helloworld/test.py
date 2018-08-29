import boto3

BUCKET = "loggereast1"
KEY = "dinner1.jpg"

def detect_labels(bucket, key, max_labels=10, min_confidence=90, region="us-east-1"):
	rekognition = boto3.client("rekognition", region)
	response = rekognition.detect_labels(
		Image={
			"S3Object": {
				"Bucket": bucket,
				"Name": key,
			}
		},
		MaxLabels=max_labels,
		MinConfidence=min_confidence,
	)
	print(response)
	for label in response['Labels']:
	    print(label)
	return response['Labels']


for label in detect_labels(BUCKET, KEY):
	print("{Name} - {Confidence}%".format(**label))