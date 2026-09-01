import logging
import os
import shutil
import folder_paths

logger = logging.getLogger(__name__)


def resolve_target(path_input: str) -> str | None:
    """
    Resolve the target path.
    - If absolute and exists, use as-is.
    - Otherwise treat as relative to ComfyUI's output directory.
    Returns None if nothing resolves.
    """
    if os.path.isabs(path_input) and os.path.exists(path_input):
        return path_input

    output_dir = folder_paths.get_output_directory()
    candidate = os.path.join(output_dir, path_input)
    if os.path.exists(candidate):
        return candidate

    return None


class OutputCleaner:
    """
    Delete a file or folder from ComfyUI's output directory (or an absolute path).

    - path        : filename, relative subpath, or absolute path to target
    - delete_mode : "file_only" | "folder_and_contents"
    - dry_run     : when True, logs what WOULD be deleted without touching anything
    - any_input   : passthrough — wire anything here, value is forwarded unchanged
    """

    CATEGORY = "utils/file_management"
    FUNCTION = "run"
    RETURN_TYPES = ("*",)
    RETURN_NAMES = ("output",)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "anything": ("*", {
                    "tooltip": "Passthrough — wire any node output here; the value is forwarded unchanged.",
                }),
                "path": ("STRING", {
                    "default": "subfolder_name",
                    "multiline": False,
                    "tooltip": (
                        "Filename, relative subpath (e.g. 'my_batch/img.png' or 'my_batch'), "
                        "or absolute path. Resolved against the ComfyUI output directory "
                        "when not absolute."
                    ),
                }),
                "delete_mode": (["file_only", "folder_and_contents"], {
                    "default": "file_only",
                    "tooltip": (
                        "file_only: delete a single file (errors if target is a directory). "
                        "folder_and_contents: recursively delete a directory and everything in it."
                    ),
                }),
                "dry_run": ("BOOLEAN", {
                    "default": True,
                    "tooltip": (
                        "When True, logs what WOULD be deleted without actually deleting anything. "
                        "Always run with dry_run=True first to verify the target."
                    ),
                }),
            },            
        }

    def run(self, path: str, delete_mode: str, dry_run: bool, any_input=None):
        output_dir = folder_paths.get_output_directory()
        prefix = "[DRY RUN] " if dry_run else ""

        # ── resolve target ────────────────────────────────────────────────────
        resolved = resolve_target(path.strip())

        if resolved is None:
            msg = (
                f"ERROR: Target not found.\n"
                f"  Input path : {path!r}\n"
                f"  Output dir : {output_dir}\n"
                f"  Tried      : {os.path.join(output_dir, path.strip())!r}"
            )
            logger.error(msg)
            return any_input

        # ── safety: keep the output root itself ───────────────────────────────
        if os.path.realpath(resolved) == os.path.realpath(output_dir):            
            logger.error("ERROR: Refusing to delete the ComfyUI output root directory.")
            return any_input

        # ── detect what the target actually is ────────────────────────────────
        is_dir  = os.path.isdir(resolved)
        is_file = os.path.isfile(resolved)

        logger.info(f"{prefix}Target   : {resolved}")
        logger.info(f"Type     : {'directory' if is_dir else 'file'}")
        logger.info(f"Mode     : {delete_mode}")

        # ── validate mode vs target type ──────────────────────────────────────
        if is_file and delete_mode == "folder_and_contents":
            msg = (
                f"ERROR: delete_mode is 'folder_and_contents' but target is a file.\n"
                f"  Target: {resolved}\n"
                f"  Switch to delete_mode='file_only' or point at a directory."
            )
            logger.error(msg)
            return any_input

        if is_dir and delete_mode == "file_only":
            msg = (
                f"ERROR: delete_mode is 'file_only' but target is a directory.\n"
                f"  Target: {resolved}\n"
                f"  Switch to delete_mode='folder_and_contents' to delete a directory."
            )
            logger.error(msg)
            return any_input

        # ── execute (or skip if dry_run) ──────────────────────────────────────
        if dry_run:
            logger.warning("No files were deleted. Set dry_run=False to execute.")
        else:
            try:
                if is_file:
                    os.remove(resolved)
                    logger.info("Result   : File deleted successfully.")
                elif is_dir:
                    shutil.rmtree(resolved)
                    logger.info("Result   : Directory and all contents deleted successfully.")
            except Exception as e:
                logger.error(f"Result   : ERROR during deletion — {e}")

        return any_input