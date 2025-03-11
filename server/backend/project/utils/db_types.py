import sqlalchemy.types as types
from pgvector.sqlalchemy import Vector

class Embedding(types.TypeDecorator):
    impl = Vector
    cache_ok = True

    # necessary to convert default numpy array return value to list that is json-encodable
    # Otherwise Fastapi type validation will fail as it can't decode json (breaking fastapi-users)
    def process_result_value(self, value, dialect):
        if value is not None:
            return value.tolist()
        else:
            return value
