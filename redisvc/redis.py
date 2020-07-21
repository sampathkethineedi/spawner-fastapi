import redis


class Redis:
    """Redis class for Events

    """
    def __init__(self, host, port=6379, **kwargs):
        self.r = redis.StrictRedis(host=host, port=port, **kwargs)

    def push_camera_event(self, cam_id, timestamp, filename, person_ids, event_name, priority='normal'):
        """Store camera event in db

        :param cam_id: camera id str
        :param timestamp: Timestamp str
        :param filename: Path to image
        :param person_ids: list of ids of persons involved
        :param event_name: Event category ['default', 'count', 'social_distance', 'face_mask', 'anomaly']
        :param priority: priority level ['normal', 'high', 'critical']
        :return: msg
        """

        involved = ''
        for idx in person_ids:
            involved += str(idx)+'_'
        data = {"path": filename, "event": event_name, "involved": involved[:-1], "priority": priority}
        self.r.hmset('event#'+event_name+'#'+cam_id+'#'+timestamp, data)
        return "Event registered in Redis with key: "+timestamp

    def get_keys(self, pattern):
        """Get keys of a given category

        :param pattern: Start pattern of keys ['person', 'event']
        :return: list of keys
        """
        if pattern == 'ALL':
            return self.r.scan_iter()
        else:
            return self.r.scan_iter(pattern+"*")

    def get_count(self):
        """Get customer count

        :return:
        """
        try:
            return int(self.r.get('global_count'))
        except Exception:
            return 0

    def update_count(self, inc, timestamp):
        """Get customer count

        :return:
        """
        count = self.get_count() + inc
        self.r.set('global_count', count)
        self.r.set('total#'+timestamp, count)
        return count

    def get_cam_config(self, cam_id):
        pass

