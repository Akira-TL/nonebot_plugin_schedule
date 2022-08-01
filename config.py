import nonebot
from pydantic import BaseModel


class Config(BaseModel):
    morning = 6
    noon = 12
    afternoon = 14
    night = 18

Configs = Config()

driver = nonebot.get_driver()
global_configs = Config.parse_obj(driver.config.dict())