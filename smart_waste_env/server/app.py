from openenv.core.env_server.http_server import create_app

from smart_waste_env.models import SmartWasteAction, SmartWasteObservation
from smart_waste_env.server.environment import SmartWasteEnvironment


app = create_app(
    SmartWasteEnvironment,
    SmartWasteAction,
    SmartWasteObservation,
    env_name="smart_waste_env",
    max_concurrent_envs=1
)