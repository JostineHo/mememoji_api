VERSION_STR = 'v1.0.0'

import cv2
import uuid
import base64
import requests
import numpy as np
from error import Error
# from pymongo import MongoClient
# from pymongo.errors import DuplicateKeyError, CollectionInvalid
from keras.models import model_from_json
from flask import Blueprint, request, jsonify
import json


blueprint = Blueprint(VERSION_STR, __name__)


FACE_CASCADE = cv2.CascadeClassifier("resources/cascades/haarcascades/haarcascade_frontalface_alt.xml")
emotions = ['angry', 'fear', 'happy', 'sad', 'surprise', 'neutral']

# load json and create model arch
json_file = open('model.json','r')
loaded_model_json = json_file.read()
json_file.close()
model = model_from_json(loaded_model_json)

# load weights into new model
model.load_weights('model.h5')

# execute mongoDB in terminal
# db_cilent = MongoClient()
# db = db_cilent['mememoji']
# collection = db['photoinfo']

def base64_encode_image(image_rgb):
    image_bgr = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR)
    ret, image_buf = cv2.imencode('.jpg', image_bgr, (cv2.IMWRITE_JPEG_QUALITY, 40))
    image_str = base64.b64encode(image_buf)
    return 'data:image/jpeg;base64,' + image_str


def predict_emotion(face_image_gray, index): # a single cropped face
    resized_img = cv2.resize(face_image_gray, (48,48), interpolation = cv2.INTER_AREA)
    # cv2.imwrite(str(index)+'.png', resized_img)
    image = resized_img.reshape(1, 1, 48, 48)
    list_of_list = model.predict(image, batch_size=1, verbose=1)
    angry, fear, happy, sad, surprise, neutral = [prob for lst in list_of_list for prob in lst]
    return  angry, fear, happy, sad, surprise, neutral


def build_PhotoInfo(image_gray, image_rgb, annotated_rgb, crop_faces):

    photoinfo = {}
    # this function returns coordinates of faces in grayscale
    faces = FACE_CASCADE.detectMultiScale(image_gray,
                                          scaleFactor=1.1,
                                          minNeighbors=3,
                                          minSize=(45, 45),
                                          flags = cv2.CASCADE_SCALE_IMAGE)

    face_color = [0, 0, 255] #blue
    thickness = 4
    FaceInfo = []
    index = 0
    for x_face, y_face, w_face, h_face in faces:

        faceinfo = {'index': index}
        faceinfo['location_xy'] = (int(x_face), int(y_face))
        faceinfo['width'] = int(w_face)
        faceinfo['height'] = int(h_face)

        face_image_gray = image_gray[y_face : y_face + h_face,
                                     x_face : x_face + w_face]
        angry, fear, happy, sad, surprise, neutral = predict_emotion(face_image_gray, index)
        faceinfo['prediction'] = [{'emotion': 'angry', 'percent': float(angry)},
                                  {'emotion': 'fear','percent': float(fear)},
                                  {'emotion': 'happy','percent': float(happy)},
                                  {'emotion': 'sad','percent': float(sad)},
                                  {'emotion': 'surprise','percent': float(surprise)},
                                  {'emotion': 'neutral','percent': float(neutral)}]

        if crop_faces != None:
            face_image_rgb = image_rgb[y_face : y_face + h_face,
                                       x_face : x_face + w_face]
            resized_image = cv2.resize(face_image_rgb, (40, 50))
            faceinfo['thumbnail'] = base64_encode_image(resized_image)

        if annotated_rgb != None: # opencv drawing the box
            cv2.rectangle(annotated_rgb, (x_face, y_face),
                          (x_face + w_face, y_face + h_face),
                          face_color, thickness)
        FaceInfo.append(faceinfo)
        index += 1

    photoinfo['faces'] = FaceInfo
    if annotated_rgb != None:
        photoinfo['annotated_image'] = base64_encode_image(annotated_rgb)
    # TO-DO: FINISH mongoDB
    # insert in mongoDB and return id

    photoinfo['pic_id'] = str(uuid.uuid1())
    # print 'picture_id: ', photoinfo['pic_id']
    # _id = collection.insert_one(photoinfo).inserted_id
    # mongo automatically insersts _id into photoinfo
    return photoinfo


def obtain_images(request):
    '''
    All three routes below pass the image in the same way as one another.
    This function attempts to obtain the image, or it throws an error
    if the image cannot be obtained.
    '''

    if 'image_url' in request.args:
        image_url = request.args['image_url']
        try:
            response = requests.get(image_url)
            encoded_image_str = response.content
        except:
            raise Error(2873, 'Invalid `image_url` parameter')

    elif 'image_buf' in request.files:
        image_buf = request.files['image_buf']  # <-- FileStorage object
        encoded_image_str = image_buf.read()

    elif 'image_base64' in request.args:
        image_base64 = request.args['image_base64']

        ext, image_str = image_base64.split(';base64,')
        try:
            encoded_image_str = base64.b64decode(image_str)
        except:
            raise Error(2873, 'Invalid `image_base64` parameter')

    else:
        raise Error(35842, 'You must supply either `image_url` or `image_buf`')

    if encoded_image_str == '':
        raise Error(5724, 'You must supply a non-empty input image')

    encoded_image_buf = np.fromstring(encoded_image_str, dtype=np.uint8)
    decoded_image_bgr = cv2.imdecode(encoded_image_buf, cv2.IMREAD_COLOR)

    image_rgb = cv2.cvtColor(decoded_image_bgr, cv2.COLOR_BGR2RGB)
    image_gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    annotate_image = (request.args.get('annotate_image', 'false').lower() == 'true')
    if annotate_image:
        annotated_rgb = np.copy(image_rgb)
    else:
        annotated_rgb = None
    crop_image = (request.args.get('crop_image', 'false').lower() == 'true')
    if crop_image:
        crop_faces = True
    else:
        crop_faces = False
    return image_rgb, image_gray, annotated_rgb, crop_faces

def obtain_feedback(request):
    feedback = {}
    if 'image_id' in request.args:
        feedback['id'] = request.args['image_id']
    else:
        raise Error(2873, 'No `image_id` provided')

    if 'face_index' in request.args:
        feedback['face_index'] = request.args['face_index']

    if 'feedback' in request.args:
        if request.args['feedback'] in emotions:
            feedback['feedback'] = request.args['feedback']
        else:
            raise Error(2873, 'Invalid `feedback` parameter')

    # insert = collection.update({"pic_id": feedback['id'], "faces.index": int(feedback['face_index'])},
    #                            {"$push": {"face.index.$.feedback": feedback['feedback']}})
    # print "INSERT STATUS: ", insert
    return feedback


@blueprint.route('/predict', methods=['POST'])
def predict():
    '''
    Find faces and predict emotions in a photo
    Find faces and their emotions, and provide an annotated image and thumbnails of predicted faces.
    ---
    tags:
      - v1.0.0

    responses:
      200:
        description: A photo info objects
        schema:
          $ref: '#/definitions/PhotoInfo'
      default:
        description: Unexpected error
        schema:
          $ref: '#/definitions/Error'

    parameters:
      - name: image_base64
        in: query
        description: A base64 string from an image taken via webcam or photo upload. This field must be specified, you must pass an image via the `image_base64` form parameter.
        required: false
        type: string
      - name: image_url
        in: query
        description: The URL of an image that should be processed. If this field is not specified, you must pass an image via the `image_url` form parameter.
        required: false
        type: string
      - name: image_buf
        in: formData
        description: An image that should be processed. This is used when you need to upload an image for processing rather than specifying the URL of an existing image. If this field is not specified, you must pass an image URL via the `image_buf` parameter
        required: false
        type: file
      - name: annotate_image
        in: query
        description: A boolean input flag (default=false) indicating whether or not to build and return annotated images within the `annotated_image` field of each response object
        required: false
        type: boolean
      - name: crop_image
        in: query
        description: A boolean input flag (default=false) indicating whether or not to crop and return faces within the `thumbnails` field of each response object
        required: false
        type: boolean

    consumes:
      - multipart/form-data
      - application/x-www-form-urlencoded

    definitions:
      - schema:
          id: PhotoInfo
          type: object
          required:
            - faces
          properties:
            id:
                type: string
                format: byte
                description: an identification number for received image
            faces:
              schema:
                type: array
                description: an array of emotion probabilites, face location (x,y), cropped height and width, an empty feedback form, and a base64 encoded cropped thumbnail for each face found in this image
            annotated_image:
              type: string
              format: byte
              description: a base64 encoded annotated image
    '''
    image_rgb, image_gray, annotated_rgb, crop_faces = obtain_images(request)
    photoinfo = build_PhotoInfo(image_gray, image_rgb,annotated_rgb, crop_faces)
    # photoinfo['_id'] = str(photoinfo['_id']) # makes ObjectId jsonify
    response = jsonify(photoinfo)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@blueprint.route('/feedback', methods=['POST'])
def feedback():
    '''
    Record user feedback
    Return the face and true label when user clicks on the corresponding emoji. The users are given the option to teach the model by clicking on the true emoji icon should the model makes a wrong predictions on a face. Faces with no feedback will default to None and assumes the model made a correct prediction.
    ---
    tags:
      - v1.0.0

    responses:
      200:
        description: A user feedback channel
        schema:
          $ref: '#/definitions/Feedback'
      default:
        description: Unexpected error
        schema:
          $ref: '#/definitions/Error'

    parameters:
      - name: image_id
        in: query
        description: The id of the image processed. This field must be specified in order to insert the feedback to the correct image documentation.
        required: false
        type: string
      - name: face_index
        in: query
        description: The index of the face in question. This field must be specified in order to insert the feedback to the correct image documentation.
        required: false
        type: string
      - name: feedback
        in: query
        description: User feedback of the true emotion if the model predicted less than accurate.
        required: false
        type: string

    consumes:
      - multipart/form-data
      - application/x-www-form-urlencoded

    definitions:
      - schema:
          id: Feedback
          type: object
          required:
            - image_id
          properties:
            response:
                type: string
                format: byte
                description: status of received feedback
    '''
    feedback = obtain_feedback(request)
    emojicon = {'angry': 'ANGRY', 'fear': 'FEAR', 'happy': 'HAPPY', 'sad': 'SAD','surprise': 'SURPRISE','neutral': 'NEUTRAL'}
    # print (emojicon[feedback['feedback']]+'-->')*8
    # print feedback
    response = jsonify(feedback)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# query: db.photoinfo.find({"_id": ObjectId("578fd839beba87784205b73b")},{})


from app import app
app.register_blueprint(blueprint, url_prefix='/'+VERSION_STR)
