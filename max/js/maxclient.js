String.prototype.format = function(){
    var pattern = /\{\d+\}/g;
    var args = arguments;
    return this.replace(pattern, function(capture){ return args[capture.match(/\d+/)]; });
    }

function MaxClient (url) {
	this.url = url;
	this.mode = 'jquery'

    this.ROUTES = {   users : '/people',
		              user : '/people/{0}',
		              avatar : '/people/{0}/avatar',
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


MaxClient.prototype.setMode = function(mode) {
	this.mode = mode

};

MaxClient.prototype.setActor = function(displayName) {
	this.actor = {
            "objectType": "person",
            "displayName": displayName,
        }

};

MaxClient.prototype.POST = function(route, query, callback) {
    resource_uri = '{0}{1}'.format(this.url, route)
    if (this.mode=='jquery')
    {
	    $.ajax( {url: route,
		         success: function(result) { callback.call(result.data) },
			     type: 'POST',
			     data: JSON.stringify(query),
			     async: true,
			     dataType: 'json'
			    }
			   );
    }
    else
    {
	    var params = {}
	    params[gadgets.io.RequestParameters.CONTENT_TYPE] = gadgets.io.ContentType.JSON
	    params[gadgets.io.RequestParameters.METHOD] = gadgets.io.MethodType.POST
	    params[gadgets.io.RequestParameters.REFRESH_INTERVAL] = 1
	    params[gadgets.io.RequestParameters.POST_DATA] = JSON.stringify(query)

	    gadgets.io.makeRequest(
	                   resource_uri,
	                   function(result) { callback.call(result.data) },
	                   params
	                    )


    }
    return true
};

MaxClient.prototype.GET = function(route, callback) {
    resource_uri = '{0}{1}'.format(this.url, route)

    if (this.mode=='jquery')
    {
	    $.ajax( {url: route,
		         success: function(result) { callback.call(result) },
			     type: 'GET',
			     async: true,
			     dataType: 'json'
			    }
			   );
	}
	else
	{
	    var params = {}
	    params[gadgets.io.RequestParameters.CONTENT_TYPE] = gadgets.io.ContentType.JSON
	    params[gadgets.io.RequestParameters.METHOD] = gadgets.io.MethodType.GET
	    params[gadgets.io.RequestParameters.REFRESH_INTERVAL] = 1

	    gadgets.io.makeRequest(
	                   resource_uri,
	                   function(result) { callback.call(result.data) },
	                   params
	                    )

     }
   //return {json:ajax_result,statuscode:xhr['statusText']}
   return true
	}

MaxClient.prototype.getUserAvatarURL = function(displayName) {
	route = this.ROUTES['avatar'].format(displayName);
	imageurl = '{0}{1}'.format(this.url, route )
	return imageurl

};

MaxClient.prototype.getUserTimeline = function(displayName, callback) {
	route = this.ROUTES['timeline'].format(displayName);
    this.GET(route,callback)
};

MaxClient.prototype.getUserData = function(username, callback) {
    route = this.ROUTES['user'].format(username);
    this.GET(route,callback)
};


MaxClient.prototype.addComment = function(comment, activity, callback) {

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
    this.POST(route,query)

};


MaxClient.prototype.addActivity = function(text,callback) {
    query = {
        "verb": "post",
        "object": {
            "objectType": "note",
            "content": ""
            }
        }

    query.object.content = text

	route = this.ROUTES['user_activities'].format(this.actor.displayName);
    this.POST(route,query,callback)
};

MaxClient.prototype.follow = function(displayName, callback ) {
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
};
