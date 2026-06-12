"""
publish_instagram.py - Publicacao automatica no Instagram via Meta Graph API.

Le credenciais do .env e publica carrosseis no Instagram Business configurado.
Nao imprime tokens ou chaves.
"""

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None


script_dir = Path(__file__).parent
for i in range(4):
    env_file = script_dir / (".." * i).rstrip("/") / ".env" if i > 0 else script_dir.parent / ".env"
    if env_file.exists():
        if load_dotenv:
            load_dotenv(env_file)
        else:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if not line.strip() or line.lstrip().startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        break


IG_ID = os.getenv("INSTAGRAM_BUSINESS_ID")
PAGE_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
BASE_URL = f"https://graph.facebook.com/{os.getenv('META_API_VERSION', 'v19.0')}"
PUBLIC_IMAGE_BASE_URL = ""


def post_form(url: str, data: dict, timeout: int = 60) -> dict:
    payload = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url: str, params: dict, timeout: int = 15) -> dict:
    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(full_url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_multipart(url: str, fields: dict, file_field: str, file_path: str, timeout: int = 60) -> str:
    boundary = f"----codex{int(time.time() * 1000)}"
    body = bytearray()

    for key, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    path = Path(file_path)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(
        f'Content-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'.encode("utf-8")
    )
    body.extend(f"Content-Type: {mime}\r\n\r\n".encode("utf-8"))
    body.extend(path.read_bytes())
    body.extend(b"\r\n")
    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(url, data=bytes(body), method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def host_image(image_path: str) -> str:
    """Retorna uma URL publica para a imagem."""
    if PUBLIC_IMAGE_BASE_URL:
        url = f"{PUBLIC_IMAGE_BASE_URL.rstrip('/')}/{Path(image_path).name}"
        print(f"  URL publica: {url}")
        return url

    url = post_multipart(
        "https://catbox.moe/user/api.php",
        {"reqtype": "fileupload"},
        "fileToUpload",
        image_path,
        timeout=60,
    ).strip()
    if not url.startswith("https://"):
        raise RuntimeError(f"Falha no upload: {url}")
    print(f"  Hospedada: {url}")
    return url


def create_media_container(image_path: str) -> str:
    result = post_form(f"{BASE_URL}/{IG_ID}/media", {
        "access_token": PAGE_TOKEN,
        "image_url": host_image(image_path),
        "is_carousel_item": "true",
    }, timeout=60)
    if "id" not in result:
        raise RuntimeError(f"Erro container: {result}")
    print(f"  Container: {result['id']}")
    return result["id"]


def create_carousel(media_ids: list, caption: str) -> str:
    result = post_form(f"{BASE_URL}/{IG_ID}/media", {
        "access_token": PAGE_TOKEN,
        "media_type": "CAROUSEL",
        "children": ",".join(media_ids),
        "caption": caption,
    }, timeout=30)
    if "id" not in result:
        raise RuntimeError(f"Erro carrossel: {result}")
    print(f"  Carrossel: {result['id']}")
    return result["id"]


def wait_ready(container_id: str) -> bool:
    for i in range(12):
        result = get_json(f"{BASE_URL}/{container_id}", {
            "fields": "status_code",
            "access_token": PAGE_TOKEN,
        }, timeout=15)
        status = result.get("status_code", "")
        if status == "FINISHED":
            return True
        if status == "ERROR":
            raise RuntimeError(f"Container com erro: {result}")
        print(f"  Processando... {i * 5}s")
        time.sleep(5)
    return False


def publish(container_id: str) -> str:
    result = post_form(f"{BASE_URL}/{IG_ID}/media_publish", {
        "access_token": PAGE_TOKEN,
        "creation_id": container_id,
    }, timeout=30)
    if "id" not in result:
        raise RuntimeError(f"Erro publicar: {result}")
    return result["id"]


def get_permalink(post_id: str) -> str:
    result = get_json(f"{BASE_URL}/{post_id}", {
        "fields": "permalink",
        "access_token": PAGE_TOKEN,
    }, timeout=15)
    return result.get("permalink", "")


def run(images: list, caption: str, dry_run: bool = False, image_base_url: str = ""):
    global PUBLIC_IMAGE_BASE_URL
    PUBLIC_IMAGE_BASE_URL = image_base_url

    if not IG_ID or not PAGE_TOKEN:
        print("ERRO: Credenciais nao encontradas. Rode /setup-instagram primeiro.")
        sys.exit(1)
    if len(images) < 2:
        print("ERRO: Minimo 2 imagens para carrossel.")
        sys.exit(1)
    if len(images) > 10:
        print("ERRO: Maximo 10 imagens.")
        sys.exit(1)

    for image in images:
        if not Path(image).exists():
            print(f"ERRO: Imagem nao encontrada: {image}")
            sys.exit(1)

    print(f"\nPublicando {len(images)} slides no Instagram...")
    if dry_run:
        print("[DRY RUN] Tudo OK. Remova --dry-run para publicar.")
        return

    print("\nPasso 1/3 - Criando containers...")
    ids = [create_media_container(img) for img in images]

    print("\nPasso 2/3 - Montando carrossel...")
    carousel_id = create_carousel(ids, caption)

    print("\nPasso 3/3 - Publicando...")
    if not wait_ready(carousel_id):
        print("ERRO: Timeout no processamento.")
        sys.exit(1)

    post_id = publish(carousel_id)
    print("\nPublicado com sucesso!")
    print(f"Post ID: {post_id}")
    permalink = get_permalink(post_id)
    if permalink:
        print(f"Permalink: {permalink}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", nargs="+", required=True)
    parser.add_argument("--caption", required=True)
    parser.add_argument("--image-base-url", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(args.images, args.caption, args.dry_run, args.image_base_url)
