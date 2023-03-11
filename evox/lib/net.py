import sys, os, shutil
from urllib import request
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


def download(link, file_name, dl_log=True):
    if os.path.exists(link):
        if os.path.exists(file_name):
            if not os.path.samefile(link, file_name):
                shutil.copyfile(link, file_name)
        else:
            shutil.copyfile(link, file_name)
        return True

    with open(file_name, "wb") as f:
        with Progress(
                TextColumn("[bold blue]{task.fields[filename]}"),
                BarColumn(bar_width=None),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "[",
                DownloadColumn(),
                "]",
                TransferSpeedColumn(),
                TimeRemainingColumn(),
        ) as progress:

            task_id = progress.add_task('download', filename=file_name, total=None)
            response = request.urlopen(link)
            meta = response.info()
            file_size = int(meta["Content-Length"])
            block_sz = 4096
            file_size_dl = 0

            progress.start_task(task_id)

            while True:
                buffer = response.read(block_sz)

                if not buffer:
                    break

                f.write(buffer)

                if dl_log:
                    progress.update(task_id, total=file_size, advance=int(block_sz))

        if dl_log:
            print('\nDone!')
