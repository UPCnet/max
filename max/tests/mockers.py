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


# Revisat i actualitzat
subscribe_context = {
    "object": {
        "objectType": "context",
        "url": "http://atenea.upc.edu/"
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


create_context = {

    'url': subscribe_context['object']['url'],
    'displayName': 'Atenea'
}

create_context_private_rw = {

    'url': subscribe_context['object']['url'],
    'displayName': 'Atenea',
    'permissions': {'read':'subscribed',
                    'write':'subscribed',
                    'join':'restricted',
                    'invite':'restricted'}
}

create_context_private_r = {

    'url': subscribe_context['object']['url'],
    'displayName': 'Atenea',
    'permissions': {'read':'subscribed',
                    'write':'restricted',
                    'join':'restricted',
                    'invite':'restricted'}

}

create_contextA = {

    'url': subscribe_contextA['object']['url'],
    'displayName': 'Atenea A'
}

create_contextB = {

    'url': subscribe_contextB['object']['url'],
    'displayName': 'Atenea B'
}

# Un usuari crea una activitat de canvi d'estat
# Revisat i actualitzat
user_status = {
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_context = {
    "contexts": [
        subscribe_context['object']['url']
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_contextA = {
    "contexts": [
        subscribe_contextA['object']['url']
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_contextB = {
    "contexts": [
        subscribe_contextB['object']['url']
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

user_status_contextAB = {
    "contexts": [
        subscribe_contextA['object']['url'],
        subscribe_contextB['object']['url'],
    ],
    "object": {
        "objectType": "note",
        "content": "<p>[A] Testejant la creació d'un canvi d'estatus</p>"
    },
}

context_query = {
    "context": subscribe_context['object']['url']
}

context_queryA = {
    "contexts": subscribe_contextA['object']['url']
}


# Un usuari crea un comentari
user_comment = {
    "object": {
        "objectType": "comment",
        "content": "<p>[C] Testejant un comentari nou a una activitat</p>"
    }
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
