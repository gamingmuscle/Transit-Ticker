
import importlib.util
from google.protobuf.message import Message


class ProtoHandler:
    def __init__(self):
        pass

    def loadProtoClass(self,proto:str, protoDir:str):
        try:
            spec = importlib.util.spec_from_file_location(proto, f"{protoDir}/gtfs_realtime_pb2.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"[DEBUG] module: {module}")
            return module
        except FileNotFoundError:
            print(f"[ERROR] Protobuf class file not found: {protoDir}/gtfs_realtime_pb2.py")
            return None
        except Exception as e:
            print(f"[ERROR] Failed to load protobuf class: {protoDir}/gtfs_realtime_pb2.py - {e}")
            return None
    def get_message_class(self,module, class_name):
        classes = self.get_message_classes(module)
        if class_name not in classes:
            raise ValueError(f"Message class {class_name} not found in module")
        return classes[class_name]
    def get_message_classes(self,module):
        return {
            name: cls
            for name, cls in module.__dict__.items()
            if isinstance(cls, type) and issubclass(cls, Message)
        }

    def GetMessageClass(self,module, class_name):
        classes = self.get_message_classes(module)
        if class_name not in classes:
            raise ValueError(f"Message class {class_name} not found in module")
            return False
        return classes[class_name]
    def ParseProto(self,module, class_name, raw_bytes):
        cls = self.get_message_class(module, class_name)
        msg = cls()
        msg.ParseFromString(raw_bytes)
        return msg

    def get_entity_fields(self, feed_entity) -> dict:
        """Return a dict of populated field names on a FeedEntity using ListFields() reflection.
        Keys are field names, values are the field descriptors."""
        return {descriptor.name: value for descriptor, value in feed_entity.ListFields()}