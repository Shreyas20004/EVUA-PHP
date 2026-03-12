"""
Version Control Service
Manages git repositories for tracking code migration versions
"""
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

import git
from git import Repo, GitCommandError

logger = logging.getLogger("evua.version_control_service")

# Default storage root: /app/storage in Docker, backend/storage locally
_default_storage = os.environ.get(
    "STORAGE_DIR",
    str(Path(__file__).resolve().parents[2] / "storage")
)


class VersionControlService:
    """
    Manages git repositories for migration jobs.
    Creates and maintains version history with diffs for each migration state.
    """

    def __init__(self, base_storage_dir: Optional[str] = None):
        """
        Initialize version control service.

        Args:
            base_storage_dir: Base directory for storing git repos.
                              Defaults to STORAGE_DIR env var or backend/storage/
        """
        self.base_storage_dir = Path(base_storage_dir or _default_storage)
        self.versions_dir = self.base_storage_dir / 'versions'
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def _get_job_repo_path(self, job_id: str) -> Path:
        """Get the git repo path for a job"""
        return self.versions_dir / job_id

    def _get_file_path(self, job_id: str, file_path: str) -> Path:
        """Get the output path for a migrated file in the repo"""
        repo_path = self._get_job_repo_path(job_id)
        # Use relative path from repo root
        rel_path = Path(file_path).name
        return repo_path / rel_path

    # -----------------------------------------------------------------------
    # Repo Management
    # -----------------------------------------------------------------------

    def init_repo(self, job_id: str) -> str:
        """
        Initialize a new git repository for a job.

        Args:
            job_id: Unique migration job ID

        Returns:
            Path to the initialized repository
        """
        repo_path = self._get_job_repo_path(job_id)

        if repo_path.exists():
            logger.debug(f"Repository already exists at {repo_path}")
            return str(repo_path)

        try:
            Repo.init(repo_path)
            logger.info(f"Initialized git repo for job {job_id} at {repo_path}")
            return str(repo_path)
        except Exception as e:
            logger.error(f"Failed to initialize repo: {e}")
            raise

    def repo_exists(self, job_id: str) -> bool:
        """Check if a repository exists for a job"""
        repo_path = self._get_job_repo_path(job_id)
        try:
            Repo(repo_path)
            return True
        except (git.InvalidGitRepositoryError, git.NoSuchPathError):
            return False

    def get_repo(self, job_id: str) -> Repo:
        """Get or create a git repository for a job"""
        repo_path = str(self._get_job_repo_path(job_id))

        if not self.repo_exists(job_id):
            self.init_repo(job_id)

        return Repo(repo_path)

    # -----------------------------------------------------------------------
    # File Operations
    # -----------------------------------------------------------------------

    def save_file(self, job_id: str, file_path: str, content: str) -> None:
        """
        Save a migrated file to the repo.

        Args:
            job_id: Migration job ID
            file_path: Original file path (for reference)
            content: File content to save
        """
        try:
            repo = self.get_repo(job_id)
            output_path = self._get_file_path(job_id, file_path)

            # Write content
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding='utf-8')

            logger.debug(f"Saved file {output_path}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise

    def get_file(self, job_id: str, file_path: str, commit: Optional[str] = None) -> str:
        """
        Get file content from repository.

        Args:
            job_id: Migration job ID
            file_path: File path
            commit: Commit hash (latest if None)

        Returns:
            File content as string
        """
        try:
            repo = self.get_repo(job_id)
            output_path = self._get_file_path(job_id, file_path)

            if commit:
                # Get from specific commit
                return repo.commit(commit).tree[output_path.name].data_stream.read().decode('utf-8')
            else:
                # Get from working tree
                if output_path.exists():
                    return output_path.read_text(encoding='utf-8')
                else:
                    raise FileNotFoundError(f"File not found: {output_path}")
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise

    # -----------------------------------------------------------------------
    # Versioning
    # -----------------------------------------------------------------------

    def create_version(
        self,
        job_id: str,
        message: str,
        stage: str = 'migration',
        files_changed: Optional[int] = None,
    ) -> str:
        """
        Create a new version (git commit) of the migrated code.

        Args:
            job_id: Migration job ID
            message: Commit message
            stage: Migration stage (initial, risk_assessed, ai_verified, reverted)
            files_changed: Number of files changed

        Returns:
            Commit hash
        """
        try:
            repo = self.get_repo(job_id)

            # Stage all changes
            repo.index.add('*')

            # Check if there are changes to commit
            if not repo.index.diff('HEAD') and not repo.untracked_files:
                logger.debug(f"No changes to commit for job {job_id}")
                return repo.head.commit.hexsha if repo.head.is_valid() else None

            # Create commit
            author = git.Actor("evua-system", "evua@example.com")
            commit = repo.index.commit(
                message,
                author=author,
                committer=author,
            )

            logger.info(f"Created version for job {job_id}: {commit.hexsha}")
            return commit.hexsha
        except Exception as e:
            logger.error(f"Error creating version: {e}")
            raise

    def get_versions(self, job_id: str) -> List[Dict]:
        """
        Get all versions (commits) for a job.

        Args:
            job_id: Migration job ID

        Returns:
            List of version info dicts
        """
        try:
            repo = self.get_repo(job_id)
            versions = []

            for idx, commit in enumerate(repo.iter_commits()):
                versions.append({
                    'index': idx,
                    'hash': commit.hexsha,
                    'message': commit.message.strip(),
                    'author': str(commit.author),
                    'timestamp': datetime.fromtimestamp(commit.committed_date).isoformat(),
                    'files_changed': len(commit.stats.files) if commit.parents else 0,
                    'insertions': sum(f['insertions'] for f in commit.stats.files.values()),
                    'deletions': sum(f['deletions'] for f in commit.stats.files.values()),
                })

            return versions
        except Exception as e:
            logger.error(f"Error getting versions: {e}")
            return []

    # -----------------------------------------------------------------------
    # Diff & Comparison
    # -----------------------------------------------------------------------

    def get_diff(
        self,
        job_id: str,
        commit1: Optional[str] = None,
        commit2: Optional[str] = None,
    ) -> str:
        """
        Get unified diff between two commits.

        Args:
            job_id: Migration job ID
            commit1: First commit hash (earlier)
            commit2: Second commit hash (later, or HEAD if None)

        Returns:
            Unified diff string
        """
        try:
            repo = self.get_repo(job_id)

            if commit1 and commit2:
                return repo.git.diff(commit1, commit2)
            elif commit1:
                return repo.git.diff(commit1, 'HEAD')
            else:
                return repo.git.diff('HEAD~1', 'HEAD')
        except Exception as e:
            logger.error(f"Error getting diff: {e}")
            return ""

    def get_file_diff(
        self,
        job_id: str,
        file_path: str,
        commit1: Optional[str] = None,
        commit2: Optional[str] = None,
    ) -> str:
        """
        Get diff for a specific file between commits.

        Args:
            job_id: Migration job ID
            file_path: File path
            commit1: Earlier commit
            commit2: Later commit (or HEAD)

        Returns:
            Unified diff string
        """
        try:
            repo = self.get_repo(job_id)
            output_path = self._get_file_path(job_id, file_path)
            file_name = output_path.name

            if commit1 and commit2:
                return repo.git.diff(commit1, commit2, '--', file_name)
            elif commit1:
                return repo.git.diff(commit1, 'HEAD', '--', file_name)
            else:
                return repo.git.diff('HEAD~1', 'HEAD', '--', file_name)
        except Exception as e:
            logger.error(f"Error getting file diff: {e}")
            return ""

    # -----------------------------------------------------------------------
    # Revert
    # -----------------------------------------------------------------------

    def revert_to_version(self, job_id: str, commit_hash: str) -> str:
        """
        Create a new commit reverting to a previous version (branch-like).

        Args:
            job_id: Migration job ID
            commit_hash: Commit to revert to

        Returns:
            New commit hash of revert
        """
        try:
            repo = self.get_repo(job_id)

            # Get diff between current HEAD and target commit
            diff = repo.git.diff(commit_hash, 'HEAD')

            # Create a new commit that reverts the changes
            repo.git.revert('HEAD', '--no-edit')

            logger.info(f"Reverted job {job_id} to commit {commit_hash}")
            return repo.head.commit.hexsha
        except GitCommandError as e:
            logger.error(f"Error reverting: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during revert: {e}")
            raise

    def get_changes_for_revert(self, job_id: str, target_commit: str) -> Dict:
        """
        Get detailed changes that would happen if reverting to a commit.
        Allows user to select which changes to keep/discard.

        Args:
            job_id: Migration job ID
            target_commit: Target commit hash

        Returns:
            Dict with file changes details
        """
        try:
            repo = self.get_repo(job_id)
            current = 'HEAD'

            # Get all file changes
            diffs = repo.commit(target_commit).diff(current)

            changes = {
                'added_files': [],
                'modified_files': [],
                'deleted_files': [],
                'total_changes': 0,
            }

            for diff in diffs:
                if diff.new_file:
                    changes['added_files'].append(diff.b_path)
                elif diff.deleted_file:
                    changes['deleted_files'].append(diff.a_path)
                elif diff.renamed_file:
                    changes['modified_files'].append({
                        'from': diff.rename_from,
                        'to': diff.rename_to,
                    })
                else:
                    changes['modified_files'].append(diff.a_path)

            changes['total_changes'] = len(diffs)
            return changes
        except Exception as e:
            logger.error(f"Error getting revert changes: {e}")
            return {}


# Global singleton
_vc_service: Optional[VersionControlService] = None


def get_version_control_service() -> VersionControlService:
    """Get or create global version control service instance"""
    global _vc_service
    if _vc_service is None:
        _vc_service = VersionControlService()
    return _vc_service
