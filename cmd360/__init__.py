################################################################################
"""
360 Systems File Conversion and Upload Utility
© 2025 | Stanley Solutions | Joe Stanley
MIT License
"""
################################################################################

import os
import ftplib
from tempfile import TemporaryDirectory
from pathlib import Path

import typer
from ffmpeg import FFmpeg
from ffmpeg.errors import FFmpegError

__version__ = "0.1.0"

app = typer.Typer(help="360 Systems File Conversion and Upload Utility")

@app.command()
def put(
    host: str = typer.Argument(
        ..., help="IPv4 address of 360 Systems Instant Replay"
    ),
    files: list[str] = typer.Argument(
        ..., help="list of files to convert and send"
    ),
    username: str = typer.Option(
        "360USER", help="360 Systems Instant Replay FTP username"
    ),
    password: str = typer.Option(
        "PASSWORD", help="360 Systems Instant Replay FTP password"
    ),
):
    """Send a File to 360 Systems Instant Replay after Conversion"""
    # Contextual Temporary Directory for the Modified File
    with TemporaryDirectory() as temp_dir:

        with ftplib.FTP(host, username, password) as session:

            if "." in files:
                root = Path(os.getcwd())
                for item in os.listdir(str(root)):
                    path = root / item
                    if path.is_file():
                        files.append(str(path))

            # Convert and Send Files
            for src in files:
                if src == ".":
                    continue # Skip the folder
                if Path(src).suffix in [".pk", ".xmp"]:
                    continue

                file_name = Path(src).with_suffix(".wav").name.upper()
                dst = Path(temp_dir) / file_name
                # Convert
                try:
                    print(f"Converting: {Path(src).name}")
                    FFmpeg().input(src).output(
                        str(dst),
                        ar="44100",
                        ac=2,
                        af="loudnorm=tp=-0.1",
                    ).execute()
                except FFmpegError as err:
                    raise ValueError(f"Failed for '{src}'") from err
                except UnicodeDecodeError:
                    continue # Skip

                # Send File
                with open(dst, 'rb') as file:
                    resp = session.storbinary(f"STOR {file_name}", file)
                    if "Transfer succeeded" in resp:
                        print(f"Successfully Transferred: {file_name}")

@app.command()
def get(
    host: str = typer.Argument(
        ..., help="IPv4 address of 360 Systems Instant Replay"
    ),
    username: str = typer.Option(
        "360USER", help="360 Systems Instant Replay FTP username"
    ),
    password: str = typer.Option(
        "PASSWORD", help="360 Systems Instant Replay FTP password"
    ),
    file_name: str = typer.Argument(
        ..., help="Name of the file to retrieve"
    ),
):
    """Retrieve a File from 360 Systems Instant Replay"""
    with ftplib.FTP(host, username, password) as session:
        print(f"Retrieving: {file_name}")
        local_path = Path.cwd() / "dump" / file_name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, 'wb') as file:
            session.retrbinary(f"RETR {file_name}", file.write)
        print(f"Successfully Retrieved: {file_name}")

@app.command()
def list(
    host: str = typer.Argument(
        ..., help="IPv4 address of 360 Systems Instant Replay"
    ),
    username: str = typer.Option(
        "360USER", help="360 Systems Instant Replay FTP username"
    ),
    password: str = typer.Option(
        "PASSWORD", help="360 Systems Instant Replay FTP password"
    ),
):
    """Retrieve a File from 360 Systems Instant Replay"""
    files = []
    try:
        with ftplib.FTP(host, username, password) as session:
            session.retrlines('LIST', files.append)
    except ftplib.error_perm:
        pass
    for file_name in files:
        print(file_name)
