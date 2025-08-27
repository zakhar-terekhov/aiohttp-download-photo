import asyncio
from pathlib import Path


async def create_archive(cmd, size, stdout = b''):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    while not process.stdout.at_eof():
        stdout += await process.stdout.read(size)

    Path("smiles.zip").write_bytes(stdout)


async def main():
    cmd = ["zip", "-r", "-","300_3D_Smiles"]
    size = 1024*800
    
    await asyncio.create_task(create_archive(cmd,size))


if __name__ == "__main__":
    asyncio.run(main())
