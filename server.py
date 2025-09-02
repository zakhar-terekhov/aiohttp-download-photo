import asyncio
import logging
from pathlib import Path

import aiofiles
from aiohttp import web
from environs import Env

CHUNK_SIZE = 1024 * 800

logger = logging.getLogger("logger")


async def handle_index_page(request):
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


async def prepare_headers(request, archive_name):
    response = web.StreamResponse()

    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{archive_name}.zip"'
    )

    await response.prepare(request)

    return response


async def download_archive(request, archive_name, photos_dir):
    response = await prepare_headers(request, archive_name)

    process = await asyncio.create_subprocess_exec(
        *["zip", "-r", "-", "."],
        cwd=photos_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        while not process.stdout.at_eof():
            chunk = await process.stdout.read(CHUNK_SIZE)
            logger.info("Sending archive chunk ...")
            await response.write(chunk)
            await asyncio.sleep(5)

    except asyncio.CancelledError:
        logger.warning("Download was interrupted")
        raise

    finally:
        if process.returncode != 0:
            process.kill()

    return response


async def respond_to_request_download_archive(request):
    archive_hash = request.match_info.get("archive_hash")
    archive_name = "archive.part1" if archive_hash == "7kna" else "archive.part2"

    photos_dir = Path.cwd().joinpath(f"{env.str('PHOTOS_DIR_PATH')}{archive_hash}")

    if not photos_dir.exists():
        raise web.HTTPNotFound(text="Архив не существует или был удален")

    response = await download_archive(request, archive_name, photos_dir)

    return response


if __name__ == "__main__":
    env = Env()
    env.read_env()

    logging.basicConfig(level=logging.INFO)
    logger.disabled = env.bool("LOGGING")


    app = web.Application()
    app.add_routes(
        [
            web.get("/", handle_index_page, name="index"),
            web.get("/archive/{archive_hash}/", respond_to_request_download_archive),
        ]
    )
    web.run_app(app)
