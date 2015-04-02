
# MAX API Documentation

# Group Users
These are the user related actions in the system.

## People [/people]

### Queries an user [GET]
It performs a query to the system for an specific parameter or parameters.

+ Parameters

    + limit = `10` (optional, number, `0`) ... Maximum number of users to retrieve. Specify 0 for unlimited.

+ Request JSON Message

    + Body

            {
                "username": "messi",
            }

+ Response 200 (application/json)

    + Body

            [
                {
                    "username": "messi",
                    "displayName": "messi",
                    "id": "519b00000000000000000000",
                    "objectType": "person"
                }
            ]

### Creates an user [POST]
It creates a system user ready for it later use. The action is idempotent, what
means than in case that the user already exists, it simply returns the `user`
object. It returns the right code depending of the result of the action.

+ username (string) - The unique identifier of the user in the system
+ displayName (string) - The display and human friendly name for the user

| Permission | Description |
| ---------- | ----------- |
| Create own | Users can create its own user in the system |
| Manager    | Managers can create any user in the system |

+ Request JSON Message

    + Body

            {
                "username": "messi",
                "displayName": "Lionel Messi"
            }

+ Response 201 (application/json)

    + Body

            {
                "username": "messi",
                "iosDevices": [],
                "displayName": "messi",
                "talkingIn": [],
                "creator": "test_manager",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

+ Response 200 (application/json)

    + Body

            {
                "username": "messi",
                "iosDevices": [],
                "displayName": "messi",
                "talkingIn": [],
                "creator": "test_manager",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "messi",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

## User [/people/{username}]
It performs actions over an specific user.

+ Parameters

    + username (required, string) ... Username identifier.

### Queries an user [GET]
Returns the information of the given username.

+ Response 200 (application/json)

    + Body

            {
                "username": "neymar",
                "iosDevices": [],
                "displayName": "Neymar JR",
                "talkingIn": [],
                "creator": "neymar",
                "androidDevices": [],
                "following": [],
                "subscribedTo": [],
                "last_login": "2000-01-01T00:01:00Z",
                "published": "2000-01-01T00:01:00Z",
                "owner": "neymar",
                "id": "519b00000000000000000000",
                "objectType": "person"
            }

<!-- This is 404? -->
+ Response 404 (application/json)

    + Body

            {
                "error_description": "Unknown user: messi",
                "error": "UnknownUserError"
            }
