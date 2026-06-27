#!/usr/bin/env python3
"""Deterministic validator for NeuroWorkflow node files.

Why this exists
---------------
The engine in `Node.process()` *swallows* exceptions (it prints and returns
False) and leaves an output port as `None` when a method's return-dict key does
not match the declared output port name. A node can therefore "look fine" and
silently emit nothing. A small-model agent has no way to notice this by reading
the code. This script gives a deterministic PASS/FAIL signal so an agent (or a
participant) can loop a node to correctness without human judgement.

Usage
-----
    python check_node.py my_nodes/MyNode.py            # check every node in the file
    python check_node.py my_nodes/MyNode.py MyNodeName # check one class

Exit code is 0 only if every checked node passes. Non-zero on any failure, so
this is safe to use in a verify loop.
"""

import argparse
import importlib.util
import inspect
import os
import sys
from typing import List, Type

try:
    from neuroworkflow.core.node import Node
    from neuroworkflow.core.schema import MethodDefinition
except ImportError:
    sys.exit(
        "ERROR: cannot import neuroworkflow. Activate the venv first "
        "(e.g. `source venv/bin/activate`) so the package is on the path."
    )


def _load_module(path: str):
    """Import a .py file by path, with its own directory on sys.path."""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        sys.exit(f"ERROR: file not found: {path}")
    folder = os.path.dirname(path)
    if folder not in sys.path:
        sys.path.insert(0, folder)
    mod_name = "nw_check_target_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _find_node_classes(mod, only: str = None) -> List[Type[Node]]:
    classes = [
        obj
        for _, obj in inspect.getmembers(mod, inspect.isclass)
        if issubclass(obj, Node) and obj is not Node and obj.__module__ == mod.__name__
    ]
    if only:
        classes = [c for c in classes if c.__name__ == only]
        if not classes:
            sys.exit(f"ERROR: class '{only}' not found in the file.")
    return classes


def _check_class(cls: Type[Node]) -> bool:
    """Run all checks for one node class. Return True if it passes."""
    fails: List[str] = []
    warns: List[str] = []
    nd = getattr(cls, "NODE_DEFINITION", None)

    print(f"\n=== {cls.__name__} ===")

    if nd is None or nd.type == "base_node":
        print("  [FAIL] NODE_DEFINITION is missing (class did not set its own schema).")
        return False

    # ---- Metadata expected by NODE_CREATION_GUIDE.md (warnings, not hard fails)
    for field_name in ("stage", "tool", "model_source"):
        if not getattr(nd, field_name, None):
            warns.append(f"NODE_DEFINITION.{field_name} is not set.")
    if not nd.description or len(nd.description.split()) < 3:
        warns.append("description is empty or too short for an agent to use.")

    out_ports = set(nd.outputs.keys())
    in_ports = set(nd.inputs.keys())
    produced = set()

    # ---- Method/port wiring (static) ----------------------------------------
    for mname, mdef in nd.methods.items():
        outs = mdef.outputs if isinstance(mdef, MethodDefinition) else mdef.get("outputs", [])
        ins = mdef.inputs if isinstance(mdef, MethodDefinition) else mdef.get("inputs", [])
        for o in outs:
            produced.add(o)
            if o not in out_ports:
                fails.append(
                    f"method '{mname}' declares output '{o}' that is not an output port."
                )
        for i in ins:
            if i not in in_ports and i not in produced and i not in nd.parameters:
                warns.append(
                    f"method '{mname}' input '{i}' is neither an input port, an "
                    f"earlier method output, nor a parameter."
                )

    for o in out_ports - produced:
        warns.append(
            f"output port '{o}' is never produced by any method "
            f"(it will stay None — a silent-failure trap)."
        )

    # ---- Instantiation -------------------------------------------------------
    try:
        node = cls("check")
    except Exception as e:  # noqa: BLE001
        fails.append(f"instantiation failed: {e!r}")
        _report(fails, warns)
        return not fails

    if not node._process_steps:
        warns.append("no process steps registered (did _define_process_steps run?).")

    # ---- Runtime smoke test (only when we can run without fabricating inputs)-
    required_inputs = [
        n for n, p in node._input_ports.items() if not p.optional
    ]
    if not required_inputs:
        try:
            ok = node.process()
        except Exception as e:  # noqa: BLE001
            ok = False
            fails.append(f"process() raised: {e!r}")
        if ok is False:
            fails.append("process() returned False (a step errored — see output above).")
        else:
            for name in out_ports:
                if node.get_output(name) is None:
                    fails.append(
                        f"after run, output '{name}' is None "
                        f"(return-dict key likely does not match the port name)."
                    )
    else:
        print(
            f"  [NOTE] has required inputs {required_inputs}; ran static checks only. "
            f"Validate end-to-end inside a workflow."
        )

    _report(fails, warns)
    return not fails


def _report(fails: List[str], warns: List[str]) -> None:
    for w in warns:
        print(f"  [WARN] {w}")
    for f in fails:
        print(f"  [FAIL] {f}")
    if not fails:
        print("  [PASS] node checks passed.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a NeuroWorkflow node file.")
    ap.add_argument("node_file", help="path to the node .py file")
    ap.add_argument("class_name", nargs="?", help="optional: check only this class")
    args = ap.parse_args()

    mod = _load_module(args.node_file)
    classes = _find_node_classes(mod, args.class_name)
    if not classes:
        sys.exit("ERROR: no Node subclasses defined in this file.")

    all_ok = all(_check_class(c) for c in classes)
    print("\n" + ("ALL NODES PASSED" if all_ok else "SOME NODES FAILED"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
