import asyncio
import logging
from pathlib import Path

import aiofiles
from aiohttp import web
from environs import Env

CHUNK_SIZE = 1024 * 800

logger = logging.getLogger("logger")


async def handle_index_page(request) -> web.Response:
    """Отображение главной страницы."""
    async with aiofiles.open("index.html", mode="r") as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type="text/html")


async def download_archive(
        request, 
        process: asyncio.subprocess.Process, 
        response: web.StreamResponse
) -> web.StreamResponse:
    """Процесс скачивания архива.
    
    Обработка исключений в случае ошибки или прерывания пользователем скачивания.
    """
    try:
        while not process.stdout.at_eof():
            chunk = await process.stdout.read(CHUNK_SIZE)
            logger.info("Sending archive chunk ...")
            await response.write(chunk)
            await asyncio.sleep(0)

    except asyncio.CancelledError:
        logger.warning("Download was interrupted")
        raise

    finally:
        if process.returncode != 0:
            process.kill()
        return response


async def respond_to_request_download_archive(request) -> web.StreamResponse:
    """Обработка запроса на скачивание архива."""
    archive_hash = request.match_info.get("archive_hash")
    
    photos_dir = Path(env.str("PHOTOS_DIR_PATH")).joinpath(archive_hash)

    response = web.StreamResponse()

    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = (
        f'attachment; filename="photos_{archive_hash}.zip"'
    )

    if not photos_dir.exists():
        logger.error("Archive does not exist")
        raise web.HTTPNotFound(text="Архив не существует или был удален")

    else:
        await response.prepare(request)

        process = await asyncio.create_subprocess_exec(
            *["zip", "-r", "-", "."],
            cwd=photos_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await download_archive(request, process, response)
        
        return response


if __name__ == "__main__":
    env = Env()
    env.read_env()

    logger.disabled = env.bool("LOGGING_DISABLED")
    if not logger.disabled:
        logging.basicConfig(level=logging.INFO)

    app = web.Application()
    app.add_routes(
        [
            web.get("/", handle_index_page, name="index"),
            web.get("/archive/{archive_hash}/", respond_to_request_download_archive),
        ]
    )
    web.run_app(app)
