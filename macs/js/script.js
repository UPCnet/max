/* Author: 

*/

$(document).ready(function() {

    $("button").button();

    $("button.send").click(function() {
        content = $(".activityBox").val();
        data = {};
        // set actor - En un futur ho ha de fer el server comparant tokens
        data['actor'] = {};
        data['actor']['objectType'] = 'person';
        data['actor']['id'] = 'victor';
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

    $.ajax({type:'GET',
            url:'/user_activity',
            data: JSON.parse('{"actor.id":"victor"}'),
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                        $.each(data.items, function(k,v){ $('#activityContainer').prepend('<p>' + JSON.stringify(v) + '</p>') })
                        // alert(JSON.stringify(data));
                    }
    });

    // function getUser() { var user = {}; return user}

});

function reloadActivity () {
    $.ajax({type:'GET',
            url:'/user_activity',
            data: JSON.parse('{"actor.id":"victor"}'),
            contentType: 'application/json; charset=utf-8',
            success: function(data) {
                        $('#activityContainer').children().remove();
                        $.each(data.items, function(k,v){ $('#activityContainer').prepend('<p>' + JSON.stringify(v) + '</p>') })
                        // alert(JSON.stringify(data));
                    }
    });    
}


















