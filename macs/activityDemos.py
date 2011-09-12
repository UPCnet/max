# ===============================================================
# Format com deurien estar guardades les dades a la base de dades
# ===============================================================

# Un usuari de demo1
demouser1 = {
    'displayName': 'victor',
    'url': 'http://macs.upc.edu/profiles/victor',
    'objectType': 'person'
}

# Un usuari de demo2
demouser2 = {
    'displayName': 'javier',
    'url': 'http://macs.upc.edu/profiles/javier',
    'objectType': 'person'
}

# Una activity de demo
demostatus = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "victor"
    },
    "verb": "post",
    "object": {
        "objectType": "note",
        "content": "Avui sera un gran dia!"
    },
    "published": "2011-08-31T13:45:55Z"
}

# =============================================================================
# Format dels requests que es fa als web services REST, es a dir, el que rep el
# web service com a arguments
# =============================================================================

# Un usuari crea una activitat de canvi d'estat
user_status = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "victor"
    },
    "verb": "post",
    "object": {
        "objectType": "note",
        "content": "Avui sera un gran dia!"
    },
}

# Un usuari crea un comentari
user_comment = {
        "actor": {
            "objectType": "person",
            "id": "victor"
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

