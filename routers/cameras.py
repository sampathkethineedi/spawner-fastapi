from fastapi import APIRouter, HTTPException, Path
from typing import List
from pydantic import BaseModel, Field
from typing import Optional
from redisvc.redis import Redis
from functools import lru_cache
import config

router = APIRouter()


@lru_cache()
def get_settings():
    return config.Settings()


if get_settings().DEV:
    redis_db = Redis(get_settings().REDIS_URI_DEV, decode_responses=True)
else:
    redis_db = Redis(get_settings().REDIS_URI, password=get_settings().REDIS_PASSWORD, decode_responses=True)


class Camera(BaseModel):
    cam_id: str = Field("test_cam_01", description="Unique Camera ID", example="test_cam_01")
    cam_url: str = Field("mask_entrance.mp4", description="Camera RTSP stream URL", example="mask_entrance.mp4")
    entry_points: str = Field("300#1000#1050#450", description="Camera entry points. Ex: 300#1000#1050#450", example="300#1000#1050#450")
    info: Optional[str] = 'Generic information'


class RegisterResponse(BaseModel):
    data: Camera = Camera()
    redis_message: str = Field(..., example="true/false")
    message: str = Field(..., example="Registered camera with key: camera#test_cam_01")


@router.post("/register", response_model=RegisterResponse)
def register_camera(camera: Camera = Camera()):

    key = 'camera#' + camera.cam_id

    data = {"cam_id": camera.cam_id, "cam_url": camera.cam_url, "entry_points": camera.entry_points, "info": camera.info}

    msg = redis_db.r.hmset(key, data)

    return {"redis_message": msg, "message": "Registered camera with key: "+key, "data": data}


@router.get("/all/{k}", response_model=List)
def camera_info(k: str = Path('ALL', description="Camera information to return - 'ALL' or one out of ['cam_id', 'cam_url', 'entry_points', 'info']")
                ):
    if k not in ['ALL', 'cam_id', 'cam_url', 'entry_points', 'info']:
        raise HTTPException(status_code=333, detail="key must be one out of ['cam_id', 'cam_url', 'entry_points', 'info'] ")

    out = list_cameras(k)
    return out


@router.get("/{cam_id}", response_model=Camera)
def camera_info(cam_id: str = Path(..., description="Camera ID")):

    key = 'camera#'+cam_id

    data: Camera = Camera()
    data.cam_id = cam_id
    data = redis_db.r.hgetall(key)

    if data == {}:
        raise HTTPException(status_code=332, detail="No camera registered with id: "+cam_id)
    return data


def list_cameras(k):
    keys = list(redis_db.get_keys('camera#'))
    all_cameras: List[Camera] = []
    for key in keys:
        if k == 'ALL':
            all_cameras.append(redis_db.r.hgetall(key))
        else:
            all_cameras.append(redis_db.r.hmget(key, k)[0])

    return all_cameras
