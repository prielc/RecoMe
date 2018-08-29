#!flask/bin/python
import sys, os
sys.path.append(os.path.join(os.path.dirname(sys.path[0])))
import json
from flask import Flask, Response, render_template, request
from helloworld.flaskrun import flaskrun
import requests
import boto3 
from boto3.dynamodb.conditions import Key
from helloworld.setmetadata import db_set_item, inc_page_by
import datetime
from werkzeug.utils import secure_filename

application = Flask(__name__, template_folder='templates')

@application.route('/comper_face/<SourceImage>', methods=['GET'])
def compare_face(SourceImage):
    target_bucket = 'image-recog-lamda'
    source_bucket = 'image-recog-lamda1'
    region = 'us-east-2'
    s3 = boto3.resource('s3', region_name = 'us-east-2')
    # our image database
    my_target_bucket = s3.Bucket(target_bucket)
    # the place to upload the requester's image
    # my_source_bucket = s3.Bucket(source_bucket)
    result = {'compare_result': '0'}
    
    rekognition = boto3.client("rekognition", region)
    
    for obj in my_target_bucket.objects.all():
        # send the obj.key and bucket name to the compare
        print(obj.key)
    
        response = rekognition.compare_faces(
            SourceImage={
        		"S3Object": {
        			"Bucket": source_bucket,
        			"Name": SourceImage,
        		}
        	},
        	TargetImage={
        		"S3Object": {
        			"Bucket": target_bucket,
        			"Name": obj.key,
        		}
        	},
            SimilarityThreshold=50,
        )
        print (json.dumps('Allowed' if response['FaceMatches'][0]['Similarity'] else 'Not Allowed'))
        break
        #print (json.dumps(response['FaceMatches'][0]['Similarity'] if response['FaceMatches'] != [] else [{"Similarity": 0.0}]))

@application.route('/get_ip', methods=['GET'])
def get_ip():
    # print(get_ip_meta())
    # return time and path to url to database
    return Response(json.dumps(get_ip_meta()), mimetype='application/json', status=200)

def get_ip_meta():
    user_ip = str(request.environ['REMOTE_ADDR'])
    service_url = 'http://ipinfo.io/{}'.format(user_ip) 
    res = requests.get(service_url).json()
    # arrange data so it won't be missing when entering dynamo
    if 'country' not in res:
        res['country'] = 'mock_country'
    if 'ip_geo' not in res:
        res['ip_geo'] = 'mock_geo'
    if 'loc' not in res:
        res['loc'] = 'mock_loc'
    if 'city' not in res:
        res['city'] = 'mock_city'

@application.route('/temp/<temp>', methods=['GET'])
def get_temp(temp):
    
    response = get_ip_meta()
    my_ses = boto3.Session()
    dynamodb = my_ses.resource('dynamodb')
    table = dynamodb.Table('reco_me')
    
    item={
        'Alowed': str(response), 
        'path': temp,
        'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'time': datetime.datetime.now().strftime("%H:%M:%S"),
        'ip_meta' : response, # res_data
        'name':'security'
    }
    print(item)
    table.put_item(Item=item)
    return Response(json.dumps(item), mimetype='application/json', status=200)

@application.route('/bi', methods=['GET'])
def get_bi():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('reco_me')
    resp = table.scan()
     #return Response(json.dumps(str(resp)), mimetype='application/json', status=200)
    return render_template('index.html', response=str(resp), title='bi')

@application.route('/upload', methods=['GET','POST'])
def upload_s3():
    
    bucket = 'recome-new'
    file_name = 'temp.txt'
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # if get show page for upload
    if request.method == 'GET':
        return render_template('face_update.html')

    s3 = boto3.resource('s3', region_name = 'us-east-1')
    if request.files:
        file = request.files['user_file']
        file_name = secure_filename(file.filename) + time
        s3.Bucket(bucket).put_object(Key=file_name, Body=file)
    else:  
        response = request.get_json() 
        print(response)
        bucket = response['bucket'] # 'image-recog-lamda'
        file_name = response['file_name'] + time # whatever name
        country = response['country']
        data = json.dumps(response)
        # to create a file the obdy needs to be of type bytes, hence the data.encode
        s3.Bucket(bucket).put_object(Key=file_name, Body=data.encode('utf-8'))

    return Response(detect_labels(bucket, file_name), mimetype='application/json', status=200)
    #return Response(json.dumps({'uploaded': file_name }), mimetype='application/json', status=200)
    

if __name__ == '__main__':
    flaskrun(application)