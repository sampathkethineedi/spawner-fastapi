class DefaultParam:
    def __init__(self):
        self.cam_id = "cam_id"
        self.cam_url = "cam_url"
        self.process_stack = "person_counter#social_distance"
        self.info = "info"
        self.volumes = {'/home/ubuntu/argus/checkpoints': {'bind': '/app/checkpoints', 'mode': 'rw'}}

    def get_param(self):
        return ["--cam_id", self.cam_id, "--cam_url", self.cam_url, "--process_stack", self.process_stack]

    def run(self):
        print("Running")


class FinalParam(DefaultParam):
    def __init__(self):
        super().__init__()

        self.entry_points = "entry_points"
        self.floor_points = "floor_points"
        self.volumes['/home/ubuntu/argus/images'] = {'bind': '/app/images', 'mode': 'rw'}

    def final_param(self):
        param = self.get_param()
        if 'person_counter' in self.process_stack.split('#'):
            param.extend(["--entry_points", self.entry_points])
        if 'social_distance' in self.process_stack.split('#'):
            param.extend(["--floor_points", self.floor_points])
        return param


final_param = FinalParam()

print(final_param.final_param())