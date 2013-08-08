from zope.interface import Interface, Attribute


class IMADObjects(Interface):  # pragma: no cover
    """
        Base Class for Objects in the MongoDB, It can be instantiated with a MongoDB Object
        or a request object in the source param.

        If instantiated with a MongoDB Object the collection where the object must be passed
        If instantiated with a request, rest_params may be passed to extend request params

        Provides the methods to validate and construct an object according to activitystrea.ms
        specifications by subclassing it and providing an schema with the required fields,
        and a structure builder function 'buildObject'
    """

    unique = Attribute("""Ensure Unique""")
    collection = Attribute("""Name of the collection""")
    mdb_collection = Attribute("")
    data = Attribute("")

    def __init__(source, collection=None, rest_params={}):
        """Constructor"""

    def getActorFromDB():
        """
            If a 'actor' object is present in the received params, search for the user
            record on the DB and set it as actor. Also provides the user object with default
            displayName if not set.
        """

    def insert():
        """
            Inserts the item into his defined collection and returns its _id
        """

    def addToList(field, obj, allow_duplicates=False, safe=True):
        """
            Updates an array field of a existing DB object appending the new object
            and incrementing the total Items counter.

            if allow_duplicates = True, allows to add items even if its already on the list. If not
            , looks for `safe` value to either raise an exception if safe==False or pass gracefully if its True

            XXX TODO allow object to be either a single object or a list of objects
        """

    def deleteFromList(field, obj, safe=True):
        """
            Updates an array field of a existing DB object removing the object

            If safe == False, don't perform any deletion, otherwise remove the found objects.
        """

    def alreadyExists():
        """
            Checks if there's an object with the value specified in the unique field.
            If present, return the object, otherwise returns None
        """

    def flatten():
        """
            Recursively transforms non-json-serializable values and simplifies
            $oid and $data BISON structures. Intended for final output
        """

    def getObjectWrapper(objType):
        """
            Get the apppopiate class to be inserted in the object field
            of (mainly) an Activity
        """

    def updateFields(fields):
        """
            Update fields on objects
        """
