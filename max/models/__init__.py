import inspect

from max.models.activity import Activity
from max.models.context import Context
from max.models.conversation import Conversation
from max.models.message import Message
from max.models.user import User
from max.models.security import Security


CLASS_COLLECTION_MAPPING = dict([(klass.collection, name) for name, klass in locals().items() if inspect.isclass(klass) and getattr(klass, 'collection', None)])
