from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKey, APIKeyHeader
from routers import cameras, containers
import config
from starlette.status import HTTP_403_FORBIDDEN

app = FastAPI(title='Argus Spawner API', description='Register Cameras. Start/Stop containers',
              docs_url='/spawner-api/docs', redoc_url=None)

api_key_header = APIKeyHeader(name='spawner-api-key', auto_error=False)


async def get_api_key(api_key_h: APIKey = Security(api_key_header)):
    if api_key_h == config.API_KEY:
        return api_key_h
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )


@app.get("/spawner-api")
def home():
    return "Refer to '/spawner-api/docs' for API documentation"


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





