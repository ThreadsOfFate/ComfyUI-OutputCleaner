# ComfyUI-OutputCleaner

A minimal ComfyUI custom node for deleting files and folders from the output directory, with dry-run protection and any-type passthrough.

## Installation

```
cd ComfyUI/custom_nodes
git clone <this repo>
```

Restart ComfyUI. The node appears under **utils/file_management** as **Output Cleaner 🗑️**.

## Inputs

| Input | Type | Description |
|---|---|---|
| `path` | STRING | Filename, relative subpath (e.g. `my_batch` or `my_batch/img.png`), or absolute path. Resolved against the ComfyUI output directory when not absolute. |
| `delete_mode` | ENUM | `file_only` — delete a single file. `folder_and_contents` — recursively delete a directory and everything in it (`shutil.rmtree`). |
| `dry_run` | BOOLEAN | When `True` (default), logs exactly what would be deleted without touching anything. **Always verify with dry_run=True before executing.** |
| `any_input` | \* (optional) | Passthrough — wire any node output here; the value is forwarded unchanged to `passthrough`. |

## Outputs

| Output | Type | Description |
|---|---|---|
| `passthrough` | \* | The `any_input` value forwarded unchanged. Use to chain this node into your workflow. |
| `log` | STRING | Human-readable report of what was (or would be) deleted. Wire to a ShowText node to read it inline. |

## Behavior

- **Path resolution**: absolute paths are used as-is if they exist; everything else is resolved relative to ComfyUI's output directory.
- **Type checking**: the node detects whether the target is a file or directory and errors clearly if `delete_mode` doesn't match (e.g. pointing `file_only` at a directory).
- **Safety guard**: refuses to delete the output root directory itself.
- **Dry run output**: lists every file inside a targeted directory so you know exactly what `rmtree` would remove.

## Example usage

**Delete a subfolder and its contents:**
```
path             = "my_batch"
delete_mode      = folder_and_contents
dry_run          = True   ← verify first
```
Check the log, then flip `dry_run` to `False` and re-run.

**Delete a single file:**
```
path             = "ComfyUI_00123_.png"
delete_mode      = file_only
dry_run          = False
```
