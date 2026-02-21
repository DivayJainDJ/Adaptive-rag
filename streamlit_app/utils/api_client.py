import requests

import logging

logger = logging.getLogger(__name__)

import os

print("[ENV]", dict(os.environ))

RUST_BASE_URL = "http://localhost:8080/api"  # adjust if hosted elsewhere


def create_user(username: str, password: str, api_token: str) -> bool:
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }
    logger.info("API Token received is %s", api_token)

    try:
        response = requests.post(
            f"{RUST_BASE_URL}/create_user",
            json={"username": username, "password": password},
            headers=headers,
        )

        logger.info("Calling /create_user, status code: %s", response.status_code)

        if response.status_code == 200:
            try:
                logger.debug("Create user response: %s", response.json())
            except ValueError:
                logger.warning("Create user returned non-JSON response")
            return True
        else:
            logger.error("Create user failed: %s - %s", response.status_code, response.text)
            return False

    except requests.RequestException as e:
        logger.exception("Request to /create_user failed: %s", e)
        return False


def login_user(username: str, password: str, api_token: str) -> str:
    headers = {
        "X-API-TOKEN": api_token,
        "Content-Type": "application/json"
    }
    response = requests.post(
        f"{RUST_BASE_URL}/login",
        json={"username": username, "password": password},
        headers=headers,
    )
    logger.info("Calling /login, status code: %s", response.json())
    if response.status_code == 200:
        return response.json()
    return None


def get_api_token() -> str:
    response = requests.post(f"{RUST_BASE_URL}/init")
    logger.info("Calling /init, status code: %s", response.json())
    if response.status_code == 200:
        return response.json()["api_token"]
    return None


def query_backend(query: str, session_id: str) -> str:
    url = "http://127.0.0.1:8000/rag/query"
    print(f"[query_backend] Calling: {url}")
    response = requests.post(
        url,
        json={"query": query, "session_id": session_id},
        allow_redirects=False
    )
    if response.status_code == 200:
        return response.json()["result"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"


def document_upload_rag(file, description: str):
    headers = {
        "X-Description": description
    }
    url = "http://127.0.0.1:8000/rag/documents/upload"
    if file:
        files = {"file": (file.name, file, file.type)}

        response = requests.post(url, files=files, headers=headers)
        print(response)
        if response.status_code == 200:
            return True
    return False
