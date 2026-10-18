
import os
from pathlib import Path

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def convert(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return str(value).lower() in ("true", "1", "yes", "on")
    return str(value)

@app.get("/effective-config")
def effective_config(set_: list[str] = Query(default=[], alias="set")):
    config = DEFAULTS.copy()

    env_name = os.getenv("APP_ENV", "development")
    yaml_file = Path(f"config.{env_name}.yaml")

    if yaml_file.exists():
        with open(yaml_file, encoding="utf-8") as f:
            config.update(yaml.safe_load(f) or {})

    file_env = dotenv_values(".env")
    for key, value in file_env.items():
        if value is None:
            continue
        if key == "NUM_WORKERS":
            config["workers"] = value
        elif key.startswith("APP_"):
            config[key[4:].lower()] = value

    for key, value in os.environ.items():
        if key.startswith("APP_") and key != "APP_ENV":
            config[key[4:].lower()] = value

    for item in set_:
        if "=" in item:
            key, value = item.split("=", 1)
            config[key.strip().lower()] = value

    config = {
        key: convert(key, value)
        for key, value in config.items()
    }

    config["api_key"] = "****"
    return config
