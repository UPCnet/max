# -*- coding: utf-8 -*-
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
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

# Un usuari crea un comentari
user_comment = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "javier"
    },
    "verb": "post",
    "object": {
        "objectType": "comment",
        "content": "<p>[C] Testejant un comentari nou a una activitat</p>",
        "inReplyTo": [
          {
            "id": "4e6eefc5aceee9210d000004",
          }
        ]
    },
}

follow = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "victor"
    },
    "verb": "follow",
    "object": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000001",
        "displayName": "javier"
    },
}

unfollow = {
    "actor": {
        "objectType" : "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "victor"
    },
    "verb": "unfollow",
    "object": {
        "objectType" : "person",
        "id": "4e6e1243aceee91143000001",
        "displayName": "javier"
    },
}