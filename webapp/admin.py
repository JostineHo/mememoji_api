VERSION_STR = 'admin'


from app import APP_NAME
from error import Error
from flask import Blueprint, jsonify, request

blueprint = Blueprint(VERSION_STR, __name__)


@blueprint.route('/status')
def status():
    '''
    Get current status
    This endpoint provides a remote way to monitor this service
    and get status information about how well it is running.
    ---
    tags:
      - admin

    responses:
      200:
        description: A status info object
        schema:
          $ref: '#/definitions/StatusInfo'
      default:
        description: Unexpected error
        schema:
          $ref: '#/definitions/Error'

    parameters:
      - name: include_keys
        in: query
        description: A array of the keys that should be included in the response (default is all keys)
        required: false
        type: array
      - name: exclude_keys
        in: query
        description: A array of keys that should be excluded from the response (default is no keys)
        required: false
        type: array
      - name: request_interval
        in: query
        description: The number of recent requests to include when calculating 'avg_response_time' (default=100)
        required: false
        type: integer
      - name: time_interval
        in: query
        description: The number of seconds of recent activity to include when calculating 'num_requests' (default=60)
        required: false
        type: integer

    definitions:
      - schema:
          id: StatusInfo
          type: object
          required:
            - service_name
          properties:
            uptime:
              type: integer
              description: the number of seconds this service has been running
            num_requests:
              type: integer
              description: the number of requests this service has received in the last 'time_interval' number of seconds
            avg_response_time:
              type: number
              description: the average time in milliseconds that it took to generate the last 'request_interval' responses
            service_name:
              type: string
              description: the name of this service
      - schema:
          id: Error
          type: object
          required:
            - code
            - message
          properties:
            code:
              type: integer
              description: Basic opaque status code
            message:
              type: string
              description: the human readable description of this error's error code
    '''
    # SWAGGER_STUFF:30 actually provide real functions that do real stuff... instead of these lambdas
    info = {'avg_response_time': lambda: -1.0,
            'num_requests': lambda: -1,
            'service_name': lambda: APP_NAME,
            'uptime': lambda: -1
           }
    include_keys = request.args.get('include_keys', ','.join(info.keys())).split(',')
    exclude_keys = request.args.get('exclude_keys', '').split(',')
    request_interval = request.args.get('request_interval', 100)
    time_interval = request.args.get('time_interval', 60)
    keys = (set(info.keys()) & set(include_keys)) - set(exclude_keys)
    res = {k: info[k]() for k in keys}
    return jsonify(res)


from app import app
app.register_blueprint(blueprint, url_prefix='/'+VERSION_STR)
