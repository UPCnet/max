import json
from bson import json_util


def checkRequestConsistency(request):
    if request.content_type != 'application/json':
        raise

    # TODO: Do more consistency checks


def extractPostData(request):
    return json.loads(request.body, object_hook=json_util.object_hook)

    # TODO: Do more syntax and format checks of sent data


def checkDataActivity(data):
    if not 'actor' in data:
        raise
    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataComment(data):
    if not 'actor' in data:
        raise
    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs


def checkDataFollow(data):
    if not 'actor' in data:
        raise
    if not 'verb' in data:
        if not data['verb'] == 'follow':
            raise
    # TODO: Check if data sent is consistent with JSON activitystrea.ms standard specs
