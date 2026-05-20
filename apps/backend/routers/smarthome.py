"""
智能家居路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class SmartHomeCommand(BaseModel):
    command: str


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


@router.post("/smarthome/command")
async def execute_command(cmd_data: SmartHomeCommand):
    agent = get_agent()
    result = agent.smart_home.execute_command(cmd_data.command)
    return {"result": result}


@router.get("/smarthome/devices")
async def get_devices(device_type: Optional[str] = None):
    agent = get_agent()
    devices = agent.smart_home.get_devices_by_type(device_type) if device_type else agent.smart_home.get_all_devices()
    return {"devices": devices}
