from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field
from typing import List
from redisvc.redis import Redis
import docker
from functools import lru_cache
import config

docker_client = docker.from_env()

router = APIRouter()


@lru_cache()
def get_settings():
    return config.Settings()


if get_settings().DEV == "True":
    redis_db = Redis(get_settings().REDIS_URI_DEV, decode_responses=True)
else:
    redis_db = Redis(get_settings().REDIS_URI, password=get_settings().REDIS_PASSWORD, decode_responses=True)


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


class DefaultParam:
    def __init__(self, data):
        self.cam_id = data["cam_id"]
        self.cam_url = data["cam_url"]
        self.process_stack = data["process_stack"]
        self.info = data["info"]
        self.volumes = {'/home/ubuntu/argus/checkpoints': {'bind': '/app/checkpoints', 'mode': 'rw'}}

    def get_param(self):
        return ["--cam_id", self.cam_id, "--cam_url", self.cam_url, "--process_stack", self.process_stack]

    def final_param(self):
        return self.get_param()

    def run(self):
        try:
            container = docker_client.containers.run(
                get_settings().IMAGE_NAME, self.final_param(), volumes=self.volumes, detach=True)
            return container
        except Exception as err:
            raise HTTPException(status_code=444, detail="Error starting the container for " + self.cam_id)


class FinalParam(DefaultParam):
    def __init__(self, data):
        super().__init__(data)

        self.entry_points = data["entry_points"]
        self.floor_points = data["floor_points"]
        self.volumes['/home/ubuntu/argus/images'] = {'bind': '/app/images', 'mode': 'rw'}

    def final_param(self):
        param = self.get_param()
        if 'person_counter' in self.process_stack.split('#'):
            param.extend(["--entry_points", self.entry_points])
        if 'social_distance' in self.process_stack.split('#'):
            param.extend(["--floor_points", self.floor_points])
        return param


@router.post("/start/{cam_id}", response_model=StartResponse)
def container_start(cam_id: str = Path(..., description='camera ID', example='test_cam_01'),
                    process_stack: str = Body(None, description='change process stack', example='person_counter')):
    try:
        key = redis_db.get_keys('camera#' + str(cam_id))
    except Exception as err:
        raise HTTPException(status_code=332, detail="No camera registered with id: "+cam_id)

    key = list(key)[0]

    data = redis_db.r.hgetall(key)

    if process_stack:
        data['process_stack'] = process_stack

    camera_param = FinalParam(data)

    cam_running, _ = get_running_containers()

    if cam_id in cam_running:

        container_id = redis_db.r.get('container#' + cam_id)
        return 'Container already running for {} with id {}'.format(cam_id, container_id)

    container = camera_param.run()
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