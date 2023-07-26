from fastapi import HTTPException

from api.data.client import DatabaseClient


def get_object_or_404(client: DatabaseClient, conditions: list):
    result = client.get_single(conditions)
    if result is None:
        object_type_name = client.table_class().__class__.__name__
        raise HTTPException(status_code=404, detail=f"{object_type_name} not found")
    else:
        return result
