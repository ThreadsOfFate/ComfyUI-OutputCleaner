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
    RETURN_TYPES = ("*", "STRING")
    RETURN_NAMES = ("passthrough", "log")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
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
            "optional": {
                "any_input": ("*", {
                    "tooltip": "Passthrough — wire any node output here; the value is forwarded unchanged.",
                }),
            },
        }

    def run(self, path: str, delete_mode: str, dry_run: bool, any_input=None):
        output_dir = folder_paths.get_output_directory()
        log_lines = []
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
            return (any_input, msg)

        # ── safety: keep the output root itself ───────────────────────────────
        if os.path.realpath(resolved) == os.path.realpath(output_dir):
            msg = "ERROR: Refusing to delete the ComfyUI output root directory."
            logger.error(msg)
            return (any_input, msg)

        # ── detect what the target actually is ────────────────────────────────
        is_dir  = os.path.isdir(resolved)
        is_file = os.path.isfile(resolved)

        log_lines.append(f"{prefix}Target   : {resolved}")
        log_lines.append(f"Type     : {'directory' if is_dir else 'file'}")
        log_lines.append(f"Mode     : {delete_mode}")

        # ── validate mode vs target type ──────────────────────────────────────
        if is_file and delete_mode == "folder_and_contents":
            msg = (
                f"ERROR: delete_mode is 'folder_and_contents' but target is a file.\n"
                f"  Target: {resolved}\n"
                f"  Switch to delete_mode='file_only' or point at a directory."
            )
            logger.error(msg)
            return (any_input, msg)

        if is_dir and delete_mode == "file_only":
            msg = (
                f"ERROR: delete_mode is 'file_only' but target is a directory.\n"
                f"  Target: {resolved}\n"
                f"  Switch to delete_mode='folder_and_contents' to delete a directory."
            )
            logger.error(msg)
            return (any_input, msg)

        # ── enumerate what will be affected ───────────────────────────────────
        if is_dir:
            items = []
            for root, dirs, files in os.walk(resolved):
                for f in files:
                    items.append(os.path.join(root, f))
            log_lines.append(f"Contains : {len(items)} file(s)")
            for item in items:
                log_lines.append(f"  - {item}")
        else:
            size = os.path.getsize(resolved)
            log_lines.append(f"Size     : {size:,} bytes")

        # ── execute (or skip if dry_run) ──────────────────────────────────────
        if dry_run:
            log_lines.append("")
            log_lines.append("No files were deleted. Set dry_run=False to execute.")
            log = "\n".join(log_lines)
            logger.warning(log)
        else:
            try:
                if is_file:
                    os.remove(resolved)
                    log_lines.append("Result   : File deleted successfully.")
                elif is_dir:
                    shutil.rmtree(resolved)
                    log_lines.append("Result   : Directory and all contents deleted successfully.")
                log = "\n".join(log_lines)
                logger.info(log)
            except Exception as e:
                log_lines.append(f"Result   : ERROR during deletion — {e}")
                log = "\n".join(log_lines)
                logger.error(log)

        return (any_input, log)