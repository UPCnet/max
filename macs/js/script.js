/* Author: 

*/

$(document).ready(function() {

    $("button").button();

    // Send the activity
    $("button.send").click(function() {
        content = $(".activityBox").val();
        data = {};
        // set actor - En un futur ho ha de fer el server comparant tokens
        data['actor'] = {};
        data['actor']['objectType'] = 'person';
        data['actor']['displayName'] = username;
        data['actor']['id'] = userid;
        data['verb'] = 'post'
        data['object'] = {}
        data['object']['objectType'] = 'note';
        data['object']['content'] = content;

        $.ajax({type:'POST',
                 url: '/activity',
                 data: JSON.stringify(data),
                 contentType: 'application/json; charset=utf-8'
             });

        $(".activityBox").val("");
        reloadActivity();
    });

    // Fill the last activity in the #activityContainer
    timeline_query = {"displayName": username};

    $.ajax({type:'GET',
            url:'/user_activity',
            data: timeline_query,
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                        // $.each(data.items, function(k,v){ $('#activityContainer').prepend('<p>' + JSON.stringify(v) + '</p>') })
                        $.each(data.items, function(k,v){ $('#activityContainer').prepend(formatActivityStream(v)) })
                    }
    });


});

function reloadActivity () {
    timeline_query = {"displayName": username};

    $.ajax({type:'GET',
            url:'/user_activity',
            data: timeline_query,
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                        $('#activityContainer').children().remove();
                        // $.each(data.items, function(k,v){ $('#activityContainer').prepend('<p>' + JSON.stringify(v) + '</p>') })
                        $.each(data.items, function(k,v){ $('#activityContainer').prepend(formatActivityStream(v)) })
                    }
    });    
}

function formatActivityStream (activity) {
    if (activity['verb']=='post') {
        // alert(activity['actor']['displayName']);
        var user = '<div><span class="user">' + activity['actor']['displayName'] + '</span></div>';
        if (activity['object']['objectType']=='note') {
            var body = '<div><span class="body">' + activity['object']['content'] + '</span></div>';
        } else {
            var body = '<div><span class="body">' + activity['object'] + '</span></div>';
        }
        var date = '<div><span class="date">' + activity['published'] + '</span></div>';
        var divcontent = '<div class="content">' + user + body + date + '</div>';
        var divdata = '<div class="activity" activityid="' + activity['_id']['$oid'] + '" userid="' + activity['actor']['_id']['$oid'] + '" displayname="' + activity['actor']['displayName'] + '">' + divcontent + '</div>';
    }
    return divdata
}