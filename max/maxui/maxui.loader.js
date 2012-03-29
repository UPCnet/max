
/*
* Defines a global namespace var to hold maxui stuff, and a function onReady that
* will be called as a result of the maxui code being completely loaded.
* Custom settings and instantiation of maxui MUST be done in the onReady function body
* Other calculations that needs maxui to be loaded MAY be done also in the onReady function body
*/

window._MAXUI.onReady = function() {
    // This is called when the code has loaded.

    literals_ca = {'new_activity_text': 'Escriu alguna cosa ...',
                   'new_activity_post': "Envia l'activitat",
                   'toggle_comments': "Comentaris",
                   'new_comment_post': "Envia el comentari",
                   'load_more': "Carrega'n més"
                 }

    var settings = {
           'literals': literals_ca,
           'username' : window._MAXUI.username,
           'oAuthToken' : window._MAXUI.token,
           'oAuthGrantType' : window._MAXUI.grant,
           'maxServerURL' : window._MAXUI.server,
           'maxServerURLAlias' : '',
           'avatarURLpattern' : '',
           'readContext': "https://max.upc.edu",
           'activitySource': 'activities'
           }

    $('#activityStream').maxUI(settings)
};

/*
* Loads the maxui code asynchronously
* The generated script tag will be inserted after the first existing script tag
* found in the document.
* Modify `mui_location` according to yout settings
*/

(function(d){
var mui_location = 'https://max.upc.edu/maxui/maxui.js'
var mui = d.createElement('script'); mui.type = 'text/javascript'; mui.async = true;
mui.src = mui_location
var s = d.getElementsByTagName('script')[0]; s.parentNode.insertBefore(mui, s);

}(document));
