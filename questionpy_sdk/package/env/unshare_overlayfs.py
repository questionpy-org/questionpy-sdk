import importlib.resources
import logging
import multiprocessing
import os
import shutil
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from multiprocessing import Process
from multiprocessing.connection import Connection
from pathlib import Path, PurePosixPath
from subprocess import TimeoutExpired
from types import TracebackType
from typing import Self

from pathspec import PathSpec

from questionpy_sdk.package._helper import create_ignore_file_spec
from questionpy_sdk.package.env import BuildEnvironment
from questionpy_sdk.package.source import PackageSource
from questionpy_sdk.package.target import BuildTarget, ZipBuildTarget

log = logging.getLogger(__name__)


class _Messages:
    Ready = "ready"

    @dataclass
    class WriteToTarget:
        target: BuildTarget

    @dataclass
    class IgnoreFiles:
        path_spec: PathSpec


def _escape_lower_dir(path: Path) -> str:
    return str(path).replace(":", r"\:")


def _mount_overlayfs_fuse(opts: str, mountpoint: Path) -> None:
    with importlib.resources.as_file(
        importlib.resources.files("questionpy_sdk.package.env") / "fuse-overlayfs-x86_64") as fuse_overlayfs:
        subprocess.run((fuse_overlayfs, "-o", opts, mountpoint))


def _mount_overlayfs_kernel(opts: str, mountpoint: Path) -> None:
    # TODO: Test with spaces in dir names
    subprocess.run(("mount", "-t", "overlay", "overlay", "-o", opts, mountpoint), check=True)


_mount_overlayfs = _mount_overlayfs_kernel


def _unshare_current_process() -> None:
    uid = os.geteuid()
    gid = os.getegid()
    os.unshare(os.CLONE_NEWUSER | os.CLONE_NEWNS)
    Path("/proc/self/setgroups").write_text("deny", encoding="ascii")
    Path("/proc/self/uid_map").write_text(f"0 {uid} 1", encoding="ascii")
    Path("/proc/self/gid_map").write_text(f"0 {gid} 1", encoding="ascii")


def _unshared_main(source_path: Path, tempdir: Path, pipe_right: Connection) -> None:
    _unshare_current_process()

    upper_dir = tempdir / "upper"
    work_dir = tempdir / "work"
    mountpoint = tempdir / "merged"
    upper_dir.mkdir()
    work_dir.mkdir()
    mountpoint.mkdir()

    def mask_path(path: Path) -> None:
        path_in_upper = upper_dir / path.relative_to(mountpoint)
        path_in_upper.parent.mkdir(parents=True, exist_ok=True)
        os.mknod(path_in_upper, mode=stat.S_IFCHR, device=os.makedev(0, 0))

    opts = f"lowerdir={_escape_lower_dir(source_path)},upperdir={upper_dir},workdir={work_dir},userxattr"
    _mount_overlayfs(opts, mountpoint)

    while True:
        pipe_right.send(_Messages.Ready)

        target: BuildTarget
        ignore_spec: PathSpec
        match pipe_right.recv():
            case _Messages.WriteToTarget(target):
                target.package_dist_and_source(mountpoint / "dist", source_path)
            case _Messages.IgnoreFiles(ignore_spec):
                for matched_entry in ignore_spec.match_tree_entries(mountpoint):
                    matched_path = mountpoint / matched_entry.path
                    if not matched_path.exists():
                        # Was probably covered by a previous ignore.
                        continue
                    log.debug("Ignoring '%s'", matched_path)
                    if matched_path.is_dir():
                        shutil.rmtree(matched_path)
                    else:
                        matched_path.unlink()

                os.system(f"ls -lha {mountpoint}")


def _format_mount_opts(opts: dict[str, str]) -> str:
    return ",".join(f"{key}={value}" for key, value in opts.items())


class UnshareOverlayFsBuildEnvironment(BuildEnvironment):
    def __init__(self, source: PackageSource, ignore_spec: PathSpec) -> None:
        super().__init__(source, ignore_spec)

        self._tempdir = tempfile.TemporaryDirectory(prefix="qpy-build-")

        pipe = multiprocessing.Pipe()
        self._pipe_left: Connection = pipe[0]

        self._unshared_proc = Process(
            target=_unshared_main, args=(source.path, Path(self._tempdir.name), pipe[1])
        )

    def commit_to_target(self, target: BuildTarget) -> None:
        self._pipe_left.send(_Messages.WriteToTarget(target))
        self._wait_ready()

    def __enter__(self) -> Self:
        self._unshared_proc.start()
        self._wait_ready()
        self._pipe_left.send(_Messages.IgnoreFiles(self._ignore_spec))
        self._wait_ready()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None
    ) -> None:
        self._unshared_proc.terminate()
        try:
            self._unshared_proc.join(timeout=1)
            log.debug("Unshared subprocess has terminated gracefully.")
        except TimeoutExpired:
            log.warning("Unshared subprocess did not terminate gracefully and will be killed.")
            self._unshared_proc.kill()
            self._unshared_proc.join()

        self._unshared_proc.close()

        return self._tempdir.__exit__(exc_type, exc_value, traceback)

    def _wait_ready(self) -> None:
        if (response := self._pipe_left.recv()) != _Messages.Ready:
            raise ValueError(f"Unshared subprocess sent unexpected response: '{response!r}'")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    source = PackageSource(Path(__file__).parent / "../../../examples/minimal")
    ignore_spec = create_ignore_file_spec(source.path, source.config.ignore)
    target = ZipBuildTarget(Path("/tmp/zip.qpy"), ignore_spec)
    with UnshareOverlayFsBuildEnvironment(source, ignore_spec) as env:
        env.commit_to_target(target)
