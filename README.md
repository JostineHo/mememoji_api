# Mememoji REST API

## Overview

This API is used to both find human faces within images and provide information about each face. You feed the API images, and it returns you lists of faces (each face record containing various information about the face, including info about each eye, etc).

## Simple Demo

Identify emotions in facial expression with this easy REST API: [mememoji.rhobota.com](mememoji.rhobota.com)

## Technologies Used

- [python](https://www.python.org/)
- [flask](http://flask.pocoo.org/)
- [flask-swagger](https://github.com/gangverk/flask-swagger)
- [Swagger-UI](https://github.com/swagger-api/swagger-ui)
- [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/) (fla _Swagger Spec_)
    - also see http://editor.swagger.io/ for a playground to help you write Swagger Spec
- [OpenCV](http://opencv.org/)
- [Keras](http://keras.io/) (soon!)
- [MongoDB](https://docs.mongodb.com/manual/introduction/)
- [AWS](https://aws.amazon.com/) (with an EC2 [Ubuntu](http://www.ubuntu.com/) image)

In addition and by necessity, the simple demo uses [HTML5](https://en.wikipedia.org/wiki/HTML5)/[CSS3](https://en.wikipedia.org/wiki/Cascading_Style_Sheets#CSS_3) + [Javascript](https://en.wikipedia.org/wiki/JavaScript)/[jQuery](https://jquery.com/).
