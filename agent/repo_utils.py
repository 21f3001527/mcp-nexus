import re
import shutil
from pathlib import Path

from git import Repo
from git.exc import GitCommandError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLONE_DIR = PROJECT_ROOT / "data" / "cloned_repos"

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$"
)


def is_valid_github_url(url: str) -> bool:
    return bool(GITHUB_URL_PATTERN.match(url.strip()))


def _repo_name_from_url(url: str) -> str:
    name = url.strip().rstrip("/")
    if name.endswith(".git"):
        name = name[:-4]
    return name.split("/")[-1]


def clone_repo(url: str, force: bool = False) -> Path:
    """
    Clone a GitHub repo (shallow, depth=1) into data/cloned_repos/<repo_name>.
    If the repo already exists locally and force=False, reuse it instead of
    re-cloning. Returns the local path to the cloned repo.
    """
    if not is_valid_github_url(url):
        raise ValueError(f"'{url}' is not a valid GitHub repository URL.")

    repo_name = _repo_name_from_url(url)
    target_path = CLONE_DIR / repo_name

    if target_path.exists():
        if force:
            shutil.rmtree(target_path)
        else:
            return target_path

    CLONE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        Repo.clone_from(url, target_path, depth=1)
    except GitCommandError as e:
        if target_path.exists():
            shutil.rmtree(target_path, ignore_errors=True)
        raise RuntimeError(f"Failed to clone '{url}': {e}")

    return target_path