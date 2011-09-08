
# Un usuari crea una activitat de canvi d'estat
user_status = {
    "actor": {
        "objectType" : "person",
        "id":"victor"
    },
    "verb": "post",
    "object": {
        "objectType": "note",
        "content": "Avui sera un gran dia!"
    }
}

user_comment = {
        "actor": {
            "objectType" : "person",
            "id":"victor"
        },
        "verb": "post",
        "object": {
            "objectType": "comment",
            "content": "<p>This is a comment</p>",
            "inReplyTo": [
              {
                "id": "http://example.org/objects/123",
              }
            ]
        },
    }
