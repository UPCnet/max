String.prototype.format = function(){
    var pattern = /\{\d+\}/g;
    var args = arguments;
    return this.replace(pattern, function(capture){ return args[capture.match(/\d+/)]; });
    }

function MaxClient (url) {
	this.url = url;

    this.ROUTES = {   users : '/people',
		              user : '/people/{0}',
		              user_activities : '/people/{0}/activities',
		              timeline : '/people/{0}/timeline',
		              user_comments : '/people/{0}/comments',
		              user_shares : '/people/{0}/shares',
		              user_likes : '/people/{0}/likes',
		              follows : '/people/{0}/follows',
		              follow : '/people/{0}/follows/{1}',
		              subscriptions : '/people/{0}/subscriptions',
		              activities : '/activities',
		              activity : '/activities/{0}',
		              comments : '/activities/{0}/comments',
		              comment : '/activities/{0}/comments/{1}',
		              likes : '/activities/{0}/likes',
		              like : '/activities/{0}/likes/{1}',
		              shares : '/activities/{0}/shares',
		              share : '/activities/{0}/shares/{1}'
		           }
};


MaxClient.prototype.setActor = function() {
	this.actor = {
            "objectType": "person",
            "displayName": arguments[0],
        }

};

MaxClient.prototype.POST = function() {
	route = arguments[0]
	query = arguments[1]
    resource_uri = '{0}{1}'.format(this.url, route)
    var ajax_result = '';
    xhr = $.ajax( {url: route,
	         success: function(data) {
	         	ajax_result = data
		         },
		     type: 'POST',
		     data: JSON.stringify(query),
		     async: false,
		     dataType: 'json'
		    }
		   );
    return {json:ajax_result,statuscode:xhr['statusText']}
};

MaxClient.prototype.GET = function() {
	route = arguments[0]
    resource_uri = '{0}{1}'.format(this.url, route)
    var ajax_result = '';
    xhr = $.ajax( {url: route,
	         success: function(data) {
	         	ajax_result = data
		         },
		     type: 'GET',
		     async: false,
		     dataType: 'json'
		    }
		   );
    return {json:ajax_result,statuscode:xhr['statusText']}
}


MaxClient.prototype.getUserTimeline = function() {
    displayName = arguments[0]
	route = this.ROUTES['timeline'].format(displayName);
    resp = this.GET(route)

    return resp['json']
};

MaxClient.prototype.addComment = function() {
	comment = arguments[0]
	activity = arguments[1]

    query = {
        "actor": {},
        "verb": "post",
        "object": {
            "objectType": "comment",
            "content": ""
            }
        }

    query.actor = this.actor
    query.object.content = comment

	route = this.ROUTES['comments'].format(activity);
    resp = this.POST(route,query)

    return resp['json']
};


MaxClient.prototype.addActivity = function() {
	text = arguments[0]

    query = {
        "verb": "post",
        "object": {
            "objectType": "note",
            "content": ""
            }
        }

    query.object.content = text

	route = this.ROUTES['user_activities'].format(this.actor.displayName);
    resp = this.POST(route,query)

    return resp['json']
};

MaxClient.prototype.follow = function() {
	displayName = arguments[0]

    query = {
        "verb": "follow",
        "object": {
            "objectType": "person",
            "displayName": ""
            }
        }

    query.object.displayName = displayName

	route = this.ROUTES['follow'].format(this.actor.displayName,displayName);
    resp = this.POST(route,query)

    return resp['json']
};
