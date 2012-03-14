# -*- coding: utf-8 -*-
# ===============================================================
# Format com deurien estar guardades les dades a la base de dades
# ===============================================================

# Un usuari de demo1
demouser1 = {
    'username': 'victor',
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
    'username': 'javier',
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
        "username": "victor"
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
        "username": "victor"
    },
    "verb": "post",
    "object": {
        "objectType": "note",
        "content": "[AC] Activitat amb contexte"
    },
    "target": {
        "objectType": "service",
        "username": "Introduccio als computadors",
        "url": "http://atenea.upc.edu/introcomp"
    },
    "published": "2011-08-31T13:45:55Z"
}

# =============================================================================
# Format dels requests que es fa als web services REST, es a dir, el que rep el
# web service com a arguments
# =============================================================================

# Un usuari crea una activitat de canvi d'estat
# Revisat i actualitzat
user_status = {
    "contexts": [
        "http://atenea.upc.edu/4127368123"
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_contextA = {
    "contexts": [
        "http://atenea.upc.edu/A"
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_contextB = {
    "contexts": [
        "http://atenea.upc.edu/B"
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_contextAB = {
    "contexts": [
        "http://atenea.upc.edu/B",
        "http://atenea.upc.edu/A"
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

context_query = {
    "contexts": [
        "http://atenea.upc.edu/4127368123"
    ]
}

# Un usuari crea un comentari
user_comment = {
    "actor": {
        "objectType": "person",
        "username": "javier"
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
        "username": "victor"
    },
    "verb": "follow",
    "object": {
        "objectType": "person",
        "username": "javier"
    },
}

unfollow = {
    "actor": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000000",
        "username": "victor"
    },
    "verb": "unfollow",
    "object": {
        "objectType": "person",
        "id": "4e6e1243aceee91143000001",
        "username": "javier"
    },
}

# Revisat i actualitzat
subscribe_context = {
    "object": {
        "objectType": "context",
        "url": "http://atenea.upc.edu/4127368123"
    }
}

# Revisat i actualitzat
subscribe_contextA = {
    "object": {
        "objectType": "context",
        "url": "http://atenea.upc.edu/A"
    }
}

# Revisat i actualitzat
subscribe_contextB = {
    "object": {
        "objectType": "context",
        "url": "http://atenea.upc.edu/B"
    }
}

unfollow_context = {
        "actor": {
            "objectType": "person",
            "id": "4e6e1243aceee91143000000",
            "username": "victor"
        },
        "verb": "unfollow",
        "object": {
            "objectType": "service",
            "username": "Introduccio als computadors",
            "url": "http://atenea.upc.edu/introcomp"
        },
    }

like = {
        "actor": {
            "objectType": "person",
            "id": "4e6e1243aceee91143000000",
            "username": "javier"
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
        "username": "javier"
    },
    "verb": "share",
    "object": {
        "objectType": "activity",
        "id": "4e6eefc5aceee9210d000004",
    },
  }
