"""
Checkpoint system for resumable pipeline operations
Based on the timeout mitigation strategy for idempotent, resumable processing
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class CheckpointManager:
    """
    Simple checkpoint manager for resumable operations

    Stores checkpoint state as JSON files in logs/checkpoints/
    Each phase has its own checkpoint file (p1.json, p2.json, etc.)
    """

    def __init__(self, phase_name: str, project_root: Optional[Path] = None):
        """
        Initialize checkpoint manager for a specific phase

        Args:
            phase_name: Phase identifier (e.g., "p1", "p2", "p3", "p4")
            project_root: Project root path (auto-detected if None)
        """
        if project_root is None:
            project_root = Path(__file__).parent.parent

        self.phase_name = phase_name
        self.checkpoint_dir = project_root / "logs" / "checkpoints"
        self.checkpoint_file = self.checkpoint_dir / f"{phase_name}.json"

        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def load_checkpoint(self) -> Dict[str, Any]:
        """
        Load checkpoint state from file

        Returns:
            Checkpoint state dict, or empty dict if no checkpoint exists
        """
        if not self.checkpoint_file.exists():
            logger.debug(f"No checkpoint found for {self.phase_name}")
            return {}

        try:
            with open(self.checkpoint_file, "r") as f:
                state = json.load(f)
            logger.info(f"Loaded checkpoint for {self.phase_name}: {state}")
            return state
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load checkpoint for {self.phase_name}: {e}")
            return {}

    def save_checkpoint(self, state: Dict[str, Any]) -> None:
        """
        Save checkpoint state to file atomically

        Args:
            state: Checkpoint state to save
        """
        try:
            # Atomic write using temp file
            temp_file = self.checkpoint_file.with_suffix(".tmp")
            with open(temp_file, "w") as f:
                json.dump(state, f, indent=2, default=str)
            temp_file.replace(self.checkpoint_file)

            logger.debug(f"Saved checkpoint for {self.phase_name}: {state}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save checkpoint for {self.phase_name}: {e}")

    def clear_checkpoint(self) -> None:
        """
        Clear/remove checkpoint file (e.g., after successful completion)
        """
        try:
            if self.checkpoint_file.exists():
                self.checkpoint_file.unlink()
                logger.info(f"Cleared checkpoint for {self.phase_name}")
        except OSError as e:
            logger.warning(f"Failed to clear checkpoint for {self.phase_name}: {e}")

    def update_progress(self, **kwargs) -> None:
        """
        Update checkpoint with current progress

        Args:
            **kwargs: Progress state to update (e.g., last_id=123, processed_count=45)
        """
        current_state = self.load_checkpoint()
        current_state.update(kwargs)
        self.save_checkpoint(current_state)


def get_checkpoint_manager(phase_name: str) -> CheckpointManager:
    """
    Factory function to get checkpoint manager for a phase

    Args:
        phase_name: Phase identifier (e.g., "p1", "p2", "p3", "p4")

    Returns:
        CheckpointManager instance
    """
    return CheckpointManager(phase_name)
