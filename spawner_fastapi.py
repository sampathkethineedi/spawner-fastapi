from fastapi import Depends, FastAPI, Header, HTTPException, Security
from fastapi.security.api_key import APIKey, APIKeyHeader
from routers import cameras, containers
import config
from starlette.status import HTTP_403_FORBIDDEN

app = FastAPI()

api_key_header = APIKeyHeader(name='spawner-api-key', auto_error=False)


async def get_api_key(api_key_h: APIKey = Security(api_key_header)):
    # if api_key_h == config.API_KEY:
    #     return api_key_h
    # else:
    #     raise HTTPException(
    #         status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
    #     )
    return api_key_h

app.include_router(
    cameras.router,
    prefix="/spawner-api/cameras",
    tags=["cameras"],
    dependencies=[Depends(get_api_key)],
    responses={404: {"description": "Not found"}},
)

app.include_router(
    containers.router,
    prefix="/spawner-api/containers",
    tags=["containers"],
    dependencies=[Depends(get_api_key)],
    responses={404: {"description": "Not found"}},
)





