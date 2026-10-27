"""MongoDB connection and collection setup for the application."""
import os
import gzip
import json
import logging
from pathlib import Path

from dotenv import load_dotenv
from gridfs import GridFS
from pymongo import ASCENDING, MongoClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from pymongo.uri_parser import parse_uri

load_dotenv(Path(__file__).resolve().with_name(".env"))

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "account_tally")
# Uvicorn configures this logger to write INFO messages to the server console.
logger = logging.getLogger("uvicorn.error")
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
database = client[MONGODB_DATABASE]
gridfs = GridFS(database)


def get_database():
    return database


def init_db() -> None:
    try:
        hosts = ", ".join(f"{host}:{port}" for host, port in parse_uri(MONGODB_URI)["nodelist"])
    except Exception:
        hosts = "the configured MongoDB host"
    logger.info("Checking MongoDB connectivity at %s", hosts)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError as exc:
        try:
            hosts = ", ".join(f"{host}:{port}" for host, port in parse_uri(MONGODB_URI)["nodelist"])
        except Exception:
            hosts = "the configured MongoDB host"
        message = (
            f"Cannot reach MongoDB at {hosts}. Check that MongoDB is running, "
            "that port 27017 is open, and that this backend host has network access."
        )
        logger.error("%s", message)
        raise RuntimeError(message) from exc
    except OperationFailure as exc:
        logger.error(
            "MongoDB is reachable, but authentication failed. Check the database username, "
            "password, and authSource in MONGODB_URI."
        )
        raise RuntimeError(
            "MongoDB is reachable, but authentication failed. Check the database credentials and authSource."
        ) from exc
    else:
        address = client.address
        if address:
            logger.info("MongoDB is running and reachable at %s:%s", address[0], address[1])
        else:
            logger.info("MongoDB ping succeeded; database %s is reachable", MONGODB_DATABASE)

    database.users.create_index([("email", ASCENDING)], unique=True)
    database.jobs.create_index([("id", ASCENDING)], unique=True)
    database.sessions.create_index([("token_hash", ASCENDING)], unique=True)
    database.sessions.create_index([("user_id", ASCENDING)])
    database.password_resets.create_index([("token_hash", ASCENDING)], unique=True)
    database.password_resets.create_index([("user_id", ASCENDING)])
    database.users.update_many({"role": {"$exists": False}}, {"$set": {"role": "member"}})


def store_job_sheets(job_id: str, sheets: dict) -> None:
    """Store potentially large worksheet payloads in GridFS, outside the 16 MB document limit."""
    new_file_id = None
    if sheets:
        payload = json.dumps(sheets, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        new_file_id = gridfs.put(gzip.compress(payload), filename=f"{job_id}.sheets.json.gz", content_type="application/gzip", metadata={"jobId": job_id})
    for file_record in database.fs.files.find({"metadata.jobId": job_id}, {"_id": 1}):
        if file_record["_id"] != new_file_id:
            gridfs.delete(file_record["_id"])


def load_job_sheets(job_id: str) -> dict:
    file_record = database.fs.files.find_one({"metadata.jobId": job_id}, sort=[("uploadDate", -1)])
    if not file_record:
        return {}
    content = gridfs.get(file_record["_id"]).read()
    return json.loads(gzip.decompress(content).decode("utf-8"))

