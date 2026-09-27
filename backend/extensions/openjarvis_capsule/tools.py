"""
OpenJarvis Bridge Capsule Tools.
Demonstrates standard extension capsule tool definition and execution protocol.
"""
from typing import Dict, List, Any

def get_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "openjarvis_system_diagnostic",
                "description": "Performs an OpenJarvis full-system diagnostic of multimodal UI grounding, active sensor links, and agent telemetry.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subsystem": {
                            "type": "string",
                            "description": "Target subsystem to diagnostic (e.g. 'all', 'grounding', 'vision', 'audio', 'telemetry')",
                            "default": "all"
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "Whether to return full subsystem telemetry metrics",
                            "default": False
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "openjarvis_grounding_probe",
                "description": "Probes desktop UI element coordinate grounding using OpenJarvis visual anchors.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_element": {
                            "type": "string",
                            "description": "Description of the UI element to ground (e.g. 'search bar', 'submit button')"
                        }
                    },
                    "required": ["target_element"]
                }
            }
        }
    ]

def execute_tool(name: str, args: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    if name == "openjarvis_system_diagnostic":
        subsystem = args.get("subsystem", "all")
        detailed = bool(args.get("detailed", False))
        return {
            "status": "online",
            "capsule": "openjarvis_bridge",
            "subsystem": subsystem,
            "latency_ms": 14.2,
            "protocols": ["JARVIS-GROUNDING-V2", "ARK-TELEMETRY", "NEURAL-PROBE"],
            "metrics": {
                "grounding_confidence": 0.98,
                "active_anchors": 12,
                "memory_overhead_mb": 42.5
            } if detailed else None,
            "message": f"OpenJarvis protocol online. Subsystem '{subsystem}' operating at 100% efficiency."
        }
    elif name == "openjarvis_grounding_probe":
        target = args.get("target_element", "unknown")
        return {
            "status": "grounded",
            "capsule": "openjarvis_bridge",
            "target": target,
            "coordinates": {"x": 512, "y": 384, "width": 120, "height": 36},
            "confidence": 0.96,
            "anchor_type": "visual_semantic_box"
        }
    raise ValueError(f"Unknown OpenJarvis tool: {name}")
