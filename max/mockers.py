# -*- coding: utf-8 -*-
# ===============================================================
# Format com deurien estar guardades les dades a la base de dades
# ===============================================================

# Un usuari de demo1
demouser1 = {
    'displayName': 'victor',
    'url': 'http://max.upc.edu/profiles/victor',
    'objectType': 'person',
    'following': {
        'totalItems': 0,
        'items': []
    },
    'subscribedTo': {
        'totalItems': 0,
        'items': []
    }
}

# Un usuari de demo2
demouser2 = {
    'displayName': 'javier',
    'url': 'http://max.upc.edu/profiles/javier',
    'objectType': 'person',
    'following': {
        'totalItems': 0,
        'items': []
    },
    'subscribedTo': {
        'totalItems': 0,
        'items': []
    }
}

# Una activity de demo
demostatus = {
    "actor": {
        "objectType": "person",
        "displayName": "victor"
    },
    "verb": "post",
    "object": {
        "objectType": "note",
        "content": "Avui sera un gran dia!"
    },
    "published": "2011-08-31T13:45:55Z"
}

demostatus_with_context = {
    "actor": {
        "objectType": "person",
        "displayName": "victor"
    },
    "verb": "post",
    "object": {
        "objectType": "note",
        "content": "[AC] Activitat amb contexte"
    },
    "target": {
        "objectType": "service",
        "displayName": "Introduccio als computadors",
        "url": "http://atenea.upc.edu/introcomp"
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
        "displayName": "victor"
    },
    "verb": "follow",
    "object": {
        "objectType": "person",
        "displayName": "javier"
    },
}

unfollow = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "victor"
    },
    "verb": "unfollow",
    "object": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000001",
        "displayName": "javier"
    },
}

follow_context = {
        "actor": {
            "objectType": "person",
            "id": "4e6e1243aceee91143000000",
            "displayName": "victor"
        },
        "verb": "follow",
        "object": {
            "objectType": "service",
            "displayName": "Introduccio als computadors",
            "url": "http://atenea.upc.edu/introcomp"
        },
    }

unfollow_context = {
        "actor": {
            "objectType": "person",
            "id": "4e6e1243aceee91143000000",
            "displayName": "victor"
        },
        "verb": "unfollow",
        "object": {
            "objectType": "service",
            "displayName": "Introduccio als computadors",
            "url": "http://atenea.upc.edu/introcomp"
        },
    }

like = {
        "actor": {
            "objectType": "person",
            "id": "4e6e1243aceee91143000000",
            "displayName": "javier"
        },
        "verb": "like",
        "object": {
            "objectType": "activity",
            "id": "4e707f80aceee94f49000002"
        },
    }

share = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "displayName": "javier"
    },
    "verb": "share",
    "object": {
        "objectType": "activity",
        "id": "4e6eefc5aceee9210d000004",
    },
  }
