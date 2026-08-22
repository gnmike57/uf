# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
UIA Tree Pruner — Recursive Windows UIA COM tree pruning engine.

Traverses the Windows UI Automation tree and strips invisible, disabled,
off-screen, and non-actionable elements. Returns a pruned dict representation
suitable for LLM consumption with >80% token reduction.

Includes explicit COM handle garbage collection to prevent memory leaks
during sustained automation sessions.

Usage:
    from ufo.automator.ui_pruner import prune_uia_tree, prune_uia_tree_from_root
    
    # From a pywinauto wrapper
    pruned = prune_uia_tree(control_element)
    
    # From a window handle
    pruned = prune_uia_tree_from_root(app_window)
"""

import gc
import logging
import platform
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# Only import Windows-specific packages on Windows
if platform.system() == "Windows":
    from pywinauto.controls.uiawrapper import UIAWrapper
else:
    UIAWrapper = Any  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ACTIONABLE_CONTROL_TYPES: Set[str] = {
    "Button",
    "Edit",
    "MenuItem",
    "TabItem",
    "ListItem",
    "Hyperlink",
    "CheckBox",
    "RadioButton",
    "ComboBox",
    "TreeItem",
    "Spinner",
    "ScrollBar",
    "Document",
    "Text",
    "Group",
}

# Control types that are containers — kept only if they have actionable descendants
CONTAINER_TYPES: Set[str] = {
    "Pane",
    "Window",
    "Group",
    "ToolBar",
    "Menu",
    "MenuBar",
    "StatusBar",
    "Tab",
    "List",
    "Tree",
    "Table",
    "DataGrid",
    "Custom",
}

# Maximum depth to prevent infinite recursion on deeply nested UIA trees
DEFAULT_MAX_DEPTH = 15

# COM GC frequency — run gc.collect() every N nodes to release COM handles
_COM_GC_INTERVAL = 50


# ---------------------------------------------------------------------------
# Core Pruner
# ---------------------------------------------------------------------------

def prune_uia_tree(
    element: "UIAWrapper",
    max_depth: int = DEFAULT_MAX_DEPTH,
    current_depth: int = 0,
    _node_counter: Optional[List[int]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Recursively inspect and prune a Windows UIA control tree.

    Filters out:
      - Invisible elements (is_visible() == False)
      - Disabled elements (is_enabled() == False)
      - Off-screen elements (zero or negative bounding box)
      - Non-actionable elements with no actionable descendants

    Retains:
      - Interactive controls: Button, Edit, MenuItem, TabItem, ListItem,
        Hyperlink, CheckBox, RadioButton, ComboBox, TreeItem, Spinner
      - Container elements that have at least one actionable descendant

    Includes explicit COM handle garbage collection every _COM_GC_INTERVAL
    nodes to prevent memory/handle leaks in sustained sessions.

    :param element: The UIA element (pywinauto UIAWrapper) to prune.
    :param max_depth: Maximum tree depth to traverse.
    :param current_depth: Current recursion depth (internal).
    :param _node_counter: Internal counter for COM GC scheduling.
    :return: Pruned dict representation, or None if element should be pruned.
    """
    if current_depth > max_depth:
        return None

    # Initialize node counter on first call
    if _node_counter is None:
        _node_counter = [0]

    try:
        # --- Visibility and enablement checks ---
        if not element.is_visible():
            return None
        if not element.is_enabled():
            return None

        # --- Extract element info ---
        elem_info = element.element_info
        control_type = elem_info.control_type or "Unknown"
        name = elem_info.name or ""
        auto_id = elem_info.automation_id or ""

        # --- Bounding box sanity check ---
        try:
            rect = element.rectangle()
            if rect.width() <= 0 or rect.height() <= 0:
                return None
            bounding_box = [rect.left, rect.top, rect.right, rect.bottom]
        except Exception:
            # Element may have been destroyed between checks
            bounding_box = [0, 0, 0, 0]

        # --- Build node ---
        node: Dict[str, Any] = {
            "control_type": control_type,
            "name": name.strip(),
            "automation_id": auto_id.strip(),
            "bounding_box": bounding_box,
            "children": [],
        }

        # --- Recursive child traversal ---
        try:
            children = element.children()
        except Exception:
            children = []

        for child in children:
            pruned_child = prune_uia_tree(
                child,
                max_depth=max_depth,
                current_depth=current_depth + 1,
                _node_counter=_node_counter,
            )
            if pruned_child is not None:
                node["children"].append(pruned_child)

        # --- COM GC scheduling ---
        _node_counter[0] += 1
        if _node_counter[0] % _COM_GC_INTERVAL == 0:
            gc.collect()

        # --- Pruning decision ---
        # Keep if: actionable control type, or container with actionable descendants
        if control_type in ACTIONABLE_CONTROL_TYPES:
            return node
        if node["children"]:
            # Container with actionable descendants — keep it
            return node

        # Non-actionable leaf with no actionable children — prune
        return None

    except Exception as e:
        # Silently skip transient/stale COM elements
        logger.debug(f"Skipping stale UIA element at depth {current_depth}: {e}")
        return None


def prune_uia_tree_from_root(
    app_window: "UIAWrapper",
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> Dict[str, Any]:
    """
    Prune the UIA tree starting from an application window root.

    Returns a complete pruned tree dict with metadata about the pruning
    operation (original count, pruned count, reduction percentage).

    :param app_window: The application window UIAWrapper.
    :param max_depth: Maximum tree depth to traverse.
    :return: Dict with 'tree', 'stats' keys.
    """
    # Count original nodes for stats
    original_count = _count_descendants(app_window)

    # Prune
    pruned_tree = prune_uia_tree(app_window, max_depth=max_depth)

    # Count pruned nodes
    pruned_count = _count_dict_nodes(pruned_tree) if pruned_tree else 0

    # Final COM cleanup
    gc.collect()

    reduction = 0.0
    if original_count > 0:
        reduction = (1.0 - pruned_count / original_count) * 100.0

    stats = {
        "original_node_count": original_count,
        "pruned_node_count": pruned_count,
        "reduction_percentage": round(reduction, 1),
        "max_depth": max_depth,
    }

    logger.info(
        f"UIA tree pruned: {original_count} → {pruned_count} nodes "
        f"({reduction:.1f}% reduction)"
    )

    return {
        "tree": pruned_tree,
        "stats": stats,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_descendants(element: "UIAWrapper", max_depth: int = 20) -> int:
    """Count total descendants of a UIA element (for stats)."""
    if max_depth <= 0:
        return 1
    count = 1
    try:
        for child in element.children():
            count += _count_descendants(child, max_depth - 1)
    except Exception:
        pass
    return count


def _count_dict_nodes(tree: Optional[Dict[str, Any]]) -> int:
    """Count nodes in a pruned tree dict."""
    if tree is None:
        return 0
    count = 1
    for child in tree.get("children", []):
        count += _count_dict_nodes(child)
    return count


def tree_to_compact_string(tree: Optional[Dict[str, Any]], indent: int = 0) -> str:
    """
    Convert a pruned tree dict to a compact string representation
    suitable for LLM context injection.

    Example output:
        Button "OK" [100,200,150,230]
          Edit "Username" [110,205,145,225]
    """
    if tree is None:
        return ""

    prefix = "  " * indent
    name_part = f' "{tree["name"]}"' if tree["name"] else ""
    bbox = tree.get("bounding_box", [])
    bbox_part = f" {bbox}" if bbox and bbox != [0, 0, 0, 0] else ""
    aid_part = f" #{tree['automation_id']}" if tree.get("automation_id") else ""

    line = f"{prefix}{tree['control_type']}{name_part}{aid_part}{bbox_part}\n"

    for child in tree.get("children", []):
        line += tree_to_compact_string(child, indent + 1)

    return line
