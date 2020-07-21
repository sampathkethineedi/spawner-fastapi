from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field
from typing import List
from redisvc.redis import Redis
import docker
import config

docker_client = docker.from_env()

router = APIRouter()

# redis_db = Redis(config.REDIS_URI_DEV, password=config.REDIS_PASSWORD, decode_responses=True)
redis_db = Redis(config.REDIS_URI_DEV, decode_responses=True)


class StartResponse(BaseModel):
    redis_message: str = Field(..., example="true/false")
    message: str = Field(..., example="Registered camera with key: camera#test_cam_01")


class ListResponse(BaseModel):
    camera_ids: List[str] = Field(..., example=['test_cam_01'])
    container_ids: List[str] = Field(..., example=['121n341j3l1kjlk'])


def get_running_containers():
    cam_running = []
    container_ids = []
    keys = redis_db.get_keys('container#')

    for key in keys:
        container_id = redis_db.r.get(key)
        try:
            container = docker_client.containers.get(container_id)
            if container.status == 'running':
                cam_running.append(key.split('#')[1])
                container_ids.append(container_id)
        except Exception as err:
            print(err)
            continue

    return cam_running, container_ids


@router.get("/start/{cam_id}", response_model=StartResponse)
def container_start(cam_id: str = Path(..., description='camera ID', example='test_cam_01')):
    try:
        key = redis_db.get_keys('camera#' + str(cam_id))
    except Exception as err:
        raise HTTPException(status_code=332, detail="No camera registered with id: "+cam_id)

    key = list(key)[0]

    data = redis_db.r.hgetall(key)

    cam_url, entry_points = data['cam_url'], data['entry_points']

    cam_running, _ = get_running_containers()

    if cam_id not in cam_running:
        pass
    else:
        container_id = redis_db.r.get('container#' + cam_id)
        return 'Container already running for {} with id {}'.format(cam_id, container_id)

    try:
        container = docker_client.containers.run(
            config.IMAGE_NAME,
            ["--cam_id", cam_id, "--cam_url", 'mask_entrance.mp4', "--entry_points", entry_points],
            volumes={'/home/ubuntu/argus/checkpoints': {'bind': '/app/checkpoints', 'mode': 'rw'}},
            detach=True)
    except Exception as err:
        raise HTTPException(status_code=444, detail="Error starting the container for "+cam_id)

    print('Started container for {} with id {}'.format(cam_id, container.id))

    msg = redis_db.r.set('container#' + cam_id, container.id)

    return dict(message='Started container for {} with id {}'.format(cam_id, container.id), redis_msg=msg)


@router.get('/list', response_model=ListResponse)
def container_list():

    cam_running, container_ids = get_running_containers()

    return dict(camera_ids=cam_running, container_ids=container_ids)


@router.get('/stop/{cam_id}', response_model=StartResponse)
def container_stop(cam_id: str = Path(..., description='camera ID', example='test_cam_01')):
    try:
        container_id = redis_db.r.get('container#'+cam_id)
    except Exception as err:
        raise HTTPException(status_code=322, detail="No container found for the camera id: "+cam_id)

    try:
        containers = docker_client.containers.list()
    except Exception as err:
        raise HTTPException(status_code=444, detail="Docker connection failed ")
    for container in containers:
        if container.id == container_id:
            container.stop()

    msg = redis_db.r.delete('container#'+cam_id)
    return {
        "redis_msg": msg,
        "message": 'Stopped container with id {} running for {}'.format(container_id, cam_id)
    }