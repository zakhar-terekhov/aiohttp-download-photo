from pathlib import Path
from aiohttp import web
import aiofiles
import asyncio

CHUNK_SIZE = 1024 * 800


async def prepare_archive_for_downloading(request):
    response = web.StreamResponse()

    archive_hash = request.match_info.get('archive_hash')

    archive_name = "archive.part1" if archive_hash == "7kna" else "archive.part2"

    response.headers['Content-Type'] = 'application/zip'
    response.headers['Content-Disposition'] = f'attachment; filename="{archive_name}.zip"'

    await response.prepare(request)

    return response, archive_hash


async def download_archive(request):
    response, archive_hash = await prepare_archive_for_downloading(request)

    photos_dir = Path.cwd().joinpath(f"test_photos/{archive_hash}")

    command = ["zip", "-r", "-", "."]

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=photos_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    while not process.stdout.at_eof():
        chunk = await process.stdout.read(CHUNK_SIZE)
        await response.write(chunk)

    return response


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


if __name__ == '__main__':
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', download_archive),
    ])
    web.run_app(app)
