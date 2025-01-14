import yaml
from singleton_decorator import singleton

@singleton
class Settings:
    def __init__(self):
        self.data = {}

    def load(self, filename):
        # File must be valid YAML
        try:
            with open(filename, 'r') as file:
                self.data = yaml.safe_load(file)
        except (FileNotFoundError, yaml.YAMLError) as e:
            pass  # Handle error if needed, here we just ignore

    def add(self, key, value):
        self.data[key] = value

    def version(self):
        return '0.0.1'
