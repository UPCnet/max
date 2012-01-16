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
                 url: '/people/'+username+'/activities',
                 data: JSON.stringify(data),
//                 contentType: 'application/json; charset=utf-8'
             });

        $(".activityBox").val("");
        reloadActivity();
    });

    $("button.followButton").toggle(
        function() {
            if ($("button.followButton span").text() == 'Follow') {
                sendFollow();
                $("button.followButton span").text('Unfollow');                
            } else {
                sendUnfollow();
                $("button.followButton span").text('Follow');               
            }
        },
        function() {
            if ($("button.followButton span").text() == 'Unfollow') {
                sendUnfollow();
                $("button.followButton span").text('Follow');
            } else {
                sendFollow();
                $("button.followButton span").text('Unfollow'); 
            }
        }
    );

    // Fill the last activity in the #activityContainer
    timeline_query = {"displayName": username};

    max = new MaxClient('http://localhost:6543')
    max.setActor(username)
    timeline = max.getUserTimeline(username)


    $.each(timeline.items, function(k,v){ $('#activityContainer').append(formatActivityStream(v)) })
    $(".date").easydate(easydateOptions);
    $("button").button();
    $(".comment").click( function() {
        $(this).closest(".activity").find(".newcommentbox").toggle('fold');
    });
    $("button.sendcomment").click(function() {

        comment_text = $(this).closest(".activity").find(".commentBox").val();
        activityid = $(this).closest(".activity").attr('activityid');
        
        max.addComment(comment_text,activityid)

        $(".activityBox").val("");
        reloadActivity();                            
      })

    
});

function reloadActivity () {
    timeline_query = {"displayName": username};

    $.ajax({type:'GET',
            url:'/people/'+username+'/timeline',
            data: timeline_query,
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                        $('#activityContainer').children().remove();
                        $.each(data.items, function(k,v){ $('#activityContainer').append(formatActivityStream(v)) })
                        $(".date").easydate(easydateOptions);
                        $("button").button();
                        $(".comment").click( function() {
                            $(this).closest(".activity").find(".newcommentbox").toggle('fold');
                        });
                    }
    });    
}

function formatActivityStream (activity) {
    if (activity['verb']=='post') {
        var user = '<div><span class="user">' + activity['actor']['displayName'] + '</span></div>';
        if (activity['object']['objectType']=='note') {
            var body = '<div><span class="body">' + activity['object']['content'] + '</span></div>';
        } else if (activity['object']['objectType']=='comment') {
            var body = '<div><span class="body">' + 'ha comentat l\'activitat (link): ' + activity['object']['content'] + '</span></div>';
        } else {
            var body = '<div><span class="body">' + activity['object'] + '</span></div>';
        }

        if (activity['object'].hasOwnProperty('replies')) {
            // fer un each i construir la estructura dels comentaris
            var divcommentsStructure = activity['object']['replies']
        }

        var date = '<div><span class="date">' + activity['published'] + '</span></div>';
        var divactions = '<div class="actions"><ul><li><a class="comment" href="#">Comentari</a></li><li><a class="like" href="#">M\'agrada</a></li><ul></div>'
        var divcontent = '<div class="content">' + user + body + divactions + date +'</div>';
        var divcomments = '<div class="comments"></div><div class="newcommentbox" style="display: none"><div class="commentBoxContainer"><textarea class="commentBox"></textarea></div><div class="button-container"><button class="sendcomment">Envia comentari</button></div></div>'
        var divdata = '<div class="activity" activityid="' + activity['id'] + '" userid="' + activity['actor']['id'] + '" displayname="' + activity['actor']['displayName'] + '">' + divcontent + divcomments +'</div>';
    }
    return divdata
}


function sendFollow () {
    follow = {
        "actor": {
            "objectType": "person",
            "id": userid,
            "displayName": username
        },
        "verb": "follow",
        "object": {
            "objectType": "person",
            "id": $("h1").attr("userid"),
            "displayName": $("h1").attr("displayname")
        },
    }

    $.ajax({type:'POST',
         url: '/follow',
         data: JSON.stringify(follow),
         contentType: 'application/json; charset=utf-8'
     }); 
}

function sendUnfollow () {
    unfollow = {
        "actor": {
            "objectType": "person",
            "id": userid,
            "displayName": username
        },
        "verb": "unfollow",
        "object": {
            "objectType": "person",
            "id": $("h1").attr("userid"),
            "displayName": $("h1").attr("displayname")
        },
    }

    $.ajax({type:'POST',
         url: '/unfollow',
         data: JSON.stringify(unfollow),
         contentType: 'application/json; charset=utf-8'
     });
}

easydateOptions = {
    live: false,
    locale: { 
        "future_format": "%s %t", 
        "past_format": "%s %t", 
        "second": "segon", 
        "seconds": "segons", 
        "minute": "minut", 
        "minutes": "minuts", 
        "hour": "hora", 
        "hours": "hores", 
        "day": "dia", 
        "days": "dies", 
        "week": "setmana", 
        "weeks": "setmanes", 
        "month": "mes", 
        "months": "mesos", 
        "year": "any", 
        "years": "anys", 
        "yesterday": "ahir", 
        "tomorrow": "demà", 
        "now": "fa un moment", 
        "ago": "fa",
        "in": "en" 
    }
 }
