"""
Zylos-Inspired Five-Layer Inside-Out Memory & 75% Context Safeguard Engine for MaxIM.
Repository reference: https://github.com/zylos-ai/zylos-core

The Five Layers:
- Layer 1: Identity & Persona (Permanent grounding: soul.md + LifeOS TELOS)
- Layer 2: State & Perception (Active window, screen resolution, session status)
- Layer 3: References & Obsidian Graph (Vault markdown notes, [[wikilinks]], #tags)
- Layer 4: Sessions & Episodic Dialogue (Turn ledger, Meta Muse execution receipts)
- Layer 5: Long-term Semantic Archive (Continuous facts, ReMe dream distillations, Checkpoints)

Also provides:
- SQLite FTS5 BM25 ranked search across all layers.
- Zylos 75% Context Safeguard compaction hook preventing LLM context cliff degradation.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from config import config
from memory import memory_store, MessageRecord, SQLiteMemoryStore
from telos import telos_engine, LifeOSEngine
from tools.vault_tool import vault_synapse, ObsidianVaultSynapse
from tools.screen_tool import screen_tool

logger = logging.getLogger("maxim.five_layer_memory")

def utc_now_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class FiveLayerMemorySystem:
    def __init__(
        self,
        memory: Optional[SQLiteMemoryStore] = None,
        vault: Optional[ObsidianVaultSynapse] = None,
        lifeos: Optional[LifeOSEngine] = None,
        max_context_tokens: int = 6000,
        safeguard_threshold: float = 0.75,
    ):
        self.memory = memory or memory_store
        self.vault = vault or vault_synapse
        self.lifeos = lifeos or telos_engine
        self.max_context_tokens = max_context_tokens
        self.safeguard_threshold = safeguard_threshold

    # =========================================================================
    # LAYER 1: Identity & Persona (Grounding)
    # =========================================================================
    def get_layer_1_identity(self) -> Dict[str, Any]:
        """Returns the immutable core persona contracts and LifeOS TELOS grounding."""
        soul_text = config.soul_path.read_text(encoding="utf-8") if config.soul_path.exists() else ""
        telos_summary = self.lifeos.get_context_injection()
        telos_raw = self.lifeos.load_telos()
        telos_data = telos_raw.model_dump() if hasattr(telos_raw, "model_dump") else dict(telos_raw)

        return {
            "layer": 1,
            "name": "Identity & Persona",
            "soul_contract_loaded": bool(soul_text),
            "soul_length": len(soul_text),
            "telos_targets": telos_data.get("targets", []),
            "telos_execution": telos_data.get("execution", []),
            "telos_summary": telos_summary,
        }

    # =========================================================================
    # LAYER 2: Real-time State & Perception (Working Context)
    # =========================================================================
    def get_layer_2_state(self, session_id: str = "default_session") -> Dict[str, Any]:
        """Captures active user environment: focused window, resolution, session ID, and recent tool receipts."""
        active_win = screen_tool.get_active_window()
        res = screen_tool.get_screen_resolution()
        receipts = self.memory.get_receipts(session_id, limit=3)
        receipt_summaries = [
            {"tool": r["tool_name"], "timestamp": r["timestamp"], "status": "executed"}
            for r in receipts
        ]
        
        return {
            "layer": 2,
            "name": "State & Perception",
            "session_id": session_id,
            "active_window": active_win,
            "resolution": res,
            "recent_actions": receipt_summaries,
            "timestamp": utc_now_iso(),
        }

    # =========================================================================
    # LAYER 3: References & Obsidian Knowledge Graph (Semantic Web)
    # =========================================================================
    def get_layer_3_references(
        self,
        query: Optional[str] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Retrieves linked Obsidian vault notes and indexes them for BM25 search."""
        vault_files = self.vault.list_notes()
        results = []
        if query and query.strip():
            results = self.vault.search_vault(query)[:limit]
        else:
            # Return recent notes
            for vf in vault_files[:limit]:
                note_title = vf.get("title", "") if isinstance(vf, dict) else str(vf)
                note_data = self.vault.read_note(note_title)
                if "error" not in note_data:
                    results.append({
                        "title": note_data.get("title", note_title),
                        "tags": note_data.get("tags", []),
                        "wikilinks": note_data.get("wikilinks", []),
                        "preview": note_data.get("content", "")[:200],
                    })

        return {
            "layer": 3,
            "name": "References & Obsidian Graph",
            "vault_note_count": len(vault_files),
            "references": results,
        }

    # =========================================================================
    # LAYER 4: Sessions & Episodic Dialogue (Turn Ledger)
    # =========================================================================
    def get_layer_4_sessions(
        self,
        session_id: str = "default_session",
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Retrieves chronological dialogue turns and execution receipts."""
        messages = self.memory.get_messages(session_id, limit=limit)
        receipts = self.memory.get_receipts(session_id, limit=limit)
        estimated_tokens = self.estimate_context_tokens(session_id)

        return {
            "layer": 4,
            "name": "Sessions & Episodic Dialogue",
            "session_id": session_id,
            "turn_count": len(messages),
            "receipt_count": len(receipts),
            "estimated_tokens": estimated_tokens,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at,
                }
                for m in messages
            ],
            "receipts": receipts,
        }

    # =========================================================================
    # LAYER 5: Long-term Semantic Archive & Experience Distillation (ReMe / Dream)
    # =========================================================================
    def get_layer_5_archive(
        self,
        query: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Retrieves learned facts, dream reflection notes, and safeguard checkpoints."""
        facts = self.memory.get_facts()
        
        # Discover checkpoint notes in vault
        checkpoints = []
        for n in self.vault.list_notes():
            title = n.get("title", "") if isinstance(n, dict) else str(n)
            if "checkpoint" in title.lower() or "reflection" in title.lower():
                checkpoints.append(title)

        return {
            "layer": 5,
            "name": "Long-term Semantic Archive",
            "fact_count": len(facts),
            "facts": [{"category": f.category, "key": f.key, "value": f.value} for f in facts[:limit]],
            "checkpoints_and_reflections": checkpoints[:limit],
        }

    # =========================================================================
    # UNIFIED 5-LAYER CONTEXT SNAPSHOT
    # =========================================================================
    def get_all_layers(
        self,
        session_id: str = "default_session",
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compiles a complete 5-layer snapshot for diagnostic or UI inspection."""
        return {
            "layer_1_identity": self.get_layer_1_identity(),
            "layer_2_state": self.get_layer_2_state(session_id),
            "layer_3_references": self.get_layer_3_references(query),
            "layer_4_sessions": self.get_layer_4_sessions(session_id),
            "layer_5_archive": self.get_layer_5_archive(query),
            "safeguard_status": self.check_context_safeguard(session_id),
        }

    # =========================================================================
    # BM25 FTS5 SEARCH ACROSS ALL MEMORY & VAULT
    # =========================================================================
    def search_all_layers(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Executes an integrated BM25 search across SQLite FTS5 and the Obsidian vault.
        """
        if not query or not query.strip():
            return []

        # 1. Search SQLite FTS5 (messages, facts, receipts)
        fts_matches = self.memory.search_fts(query, limit=limit)
        results = []
        for m in fts_matches:
            results.append({
                "source": "sqlite_fts",
                "layer": 4 if m["item_type"] in ["message", "receipt"] else 5,
                "type": m["item_type"],
                "title": m["title"],
                "content": m["content"][:250],
                "rank": m.get("rank", 0.0),
            })

        # 2. Search Obsidian Vault (Layer 3)
        vault_matches = self.vault.search_vault(query)[:limit]
        for vm in vault_matches:
            results.append({
                "source": "obsidian_vault",
                "layer": 3,
                "type": "vault_note",
                "title": vm.get("title", ""),
                "content": vm.get("preview", "")[:250],
                "rank": -0.5, # Boost vault notes
            })

        return results[:limit]

    # =========================================================================
    # ZYLOS 75% CONTEXT SAFEGUARD ENGINE
    # =========================================================================
    def estimate_context_tokens(self, session_id: str) -> int:
        """
        Heuristic token estimator across identity, working state, messages, and receipts.
        """
        total_chars = 0
        
        # Identity chars
        if config.soul_path.exists():
            total_chars += config.soul_path.stat().st_size
        total_chars += len(self.lifeos.get_context_injection())

        # Session messages chars
        messages = self.memory.get_messages(session_id, limit=50)
        for m in messages:
            total_chars += len(m.content)
            if m.tool_calls:
                total_chars += len(m.tool_calls)

        # Recent receipts chars
        receipts = self.memory.get_receipts(session_id, limit=10)
        for r in receipts:
            total_chars += len(r.get("arguments", "")) + len(r.get("result", ""))

        # ~3.8 characters per token heuristic
        return max(1, int(total_chars / 3.8))

    def check_context_safeguard(
        self,
        session_id: str,
        threshold: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates context load against the safeguard threshold (default 75% of max budget).
        """
        limit = max_tokens or self.max_context_tokens
        thresh = threshold or self.safeguard_threshold
        estimated = self.estimate_context_tokens(session_id)
        ratio = estimated / float(limit)

        triggered = ratio >= thresh
        return {
            "triggered": triggered,
            "estimated_tokens": estimated,
            "max_tokens": limit,
            "threshold_ratio": thresh,
            "capacity_ratio": round(ratio, 4),
            "capacity_percent": round(ratio * 100, 1),
            "status": "warning_critical_compaction_required" if triggered else "healthy",
        }

    def execute_safeguard_compaction(
        self,
        session_id: str,
        reason: str = "75% context safeguard threshold reached",
    ) -> Dict[str, Any]:
        """
        Executes Zylos Context Safeguard Compaction:
        1. Compiles existing conversation turns and execution receipts.
        2. Synthesizes an episodic checkpoint note in vault/01 - Memory/Checkpoint_{timestamp}.md.
        3. Indexes the checkpoint note in FTS5.
        4. Prunes earlier messages from active working buffer (retaining last 4 turns).
        5. Inserts an anchor system notice into the session.
        """
        messages = self.memory.get_messages(session_id, limit=100)
        if not messages:
            return {"status": "skipped", "reason": "No messages to compact."}

        receipts = self.memory.get_receipts(session_id, limit=20)
        timestamp_slug = utc_now_compact()
        note_title = f"Checkpoint_{timestamp_slug}"

        # 1. Build Checkpoint Note Content with frontmatter and wikilinks
        user_queries = [m.content for m in messages if m.role == "user"]
        assistant_summaries = [m.content[:150] for m in messages if m.role == "assistant"]
        tool_names = list({r.get("tool_name") for r in receipts if r.get("tool_name")})

        checkpoint_content = (
            f"# {note_title}\n\n"
            f"> **Compacted at:** {utc_now_iso()}  \n"
            f"> **Session:** `{session_id}`  \n"
            f"> **Reason:** {reason}  \n"
            f"> **Turns Compacted:** {len(messages)} turns | **Receipts Compacted:** {len(receipts)}  \n\n"
            f"## 1. Dialogue Trajectory\n"
            + "\n".join(f"- **User Objective:** {q}" for q in user_queries[:6])
            + "\n\n"
            f"## 2. Salient Assistant Syntheses\n"
            + "\n".join(f"- {a}..." for a in assistant_summaries[:4])
            + "\n\n"
            f"## 3. Dispatched Tools & System Operations\n"
            + (", ".join(f"`{t}`" for t in tool_names) if tool_names else "None")
            + "\n\n"
            f"## 4. Grounding Backlinks & References\n"
            f"- [[00 - LifeOS/TELOS]]\n"
            f"- [[Master MOC]]\n"
            f"- `#checkpoint` `#safeguard` `#zylos` `#memory`\n"
        )

        # 2. Write note to Obsidian vault
        vault_res = self.vault.write_note(
            title=note_title,
            content=checkpoint_content,
            folder="01 - Memory",
            tags=["#checkpoint", "#safeguard", "#zylos", f"#{session_id}"],
        )

        # 3. Index checkpoint in FTS5
        self.memory.index_fts(
            item_id=note_title,
            item_type="vault_note",
            title=f"Memory Checkpoint: {note_title}",
            content=checkpoint_content,
            tags="checkpoint safeguard zylos",
        )

        # 4. Prune earlier messages from SQLite session (retain last 4 turns)
        pruned_count = self.memory.prune_messages(session_id, keep_last=4)

        # 5. Insert anchor note into active message buffer
        anchor_message = (
            f"[Zylos Context Safeguard: Successfully compacted {pruned_count} earlier turns into "
            f"[[{note_title}]]. Context buffer stabilized and cleared of memory clutter.]"
        )
        self.memory.add_message(
            MessageRecord(session_id=session_id, role="system", content=anchor_message)
        )

        # 6. Recalculate token metrics
        new_estimated = self.estimate_context_tokens(session_id)

        logger.info(
            f"Zylos Safeguard Compaction completed for session {session_id}: "
            f"{pruned_count} messages pruned, new tokens: {new_estimated}."
        )

        return {
            "status": "compacted",
            "checkpoint_title": note_title,
            "vault_path": vault_res.get("path"),
            "pruned_turns": pruned_count,
            "new_estimated_tokens": new_estimated,
            "anchor_injected": True,
        }

    # =========================================================================
    # HINDSIGHT EPISTEMIC PRIMITIVES: RETAIN, RECALL, REFLECT
    # =========================================================================

    def retain(
        self,
        content: str,
        category: str = "observation",
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: str = "default_session",
    ) -> Dict[str, Any]:
        """
        Hindsight Retain Primitive: Ingests observation/fact into durable memory with provenance.
        """
        now = utc_now_iso()
        meta = metadata or {}

        # 1. If it's an explicit preference or heuristic, create/update Mental Model
        from mental_models import mental_models
        cat_lower = category.lower()
        if cat_lower in ["preference", "heuristic", "constraint", "opinion"]:
            name = meta.get("name") or f"learned_{now.replace(':', '').replace('-', '')[:15]}"
            m = mental_models.upsert_mental_model(
                name=name,
                disposition=content,
                category=cat_lower,
                confidence=meta.get("confidence", 0.6),
                observation=content,
            )
            return {
                "status": "retained",
                "primitive": "retain",
                "network": "opinion",
                "item_id": m.id,
                "name": m.name,
                "confidence": m.confidence,
            }

        # 2. Store in SQLite memory facts
        fact_key = meta.get("key") or f"{category}_{now.replace(':', '').replace('-', '').replace('.', '')[:15]}"
        self.memory.remember_fact(
            category=category,
            key=fact_key,
            value=content,
            session_id=session_id,
        )

        return {
            "status": "retained",
            "primitive": "retain",
            "network": "experience" if category == "experience" else "observation",
            "key": fact_key,
            "content": content,
            "category": category,
        }

    def recall(
        self,
        query: str,
        top_k: int = 5,
        include_mental_models: bool = True,
        session_id: str = "default_session",
        rerank: bool = False,
    ) -> Dict[str, Any]:
        """
        Hindsight Recall Primitive: Hybrid multi-network search across:
        - Active Mental Models (Opinions/Dispositions)
        - SQLite FTS5 ranked facts & observations
        - Obsidian vault semantic notes
        - Optional Qwen3-Reranker neural reranking pass
        """
        results: Dict[str, Any] = {
            "query": query,
            "mental_models": [],
            "observations": [],
            "vault_notes": [],
        }

        # 1. Search Mental Models
        if include_mental_models:
            from mental_models import mental_models
            m_list = mental_models.search_models(query, limit=top_k)
            results["mental_models"] = [m.model_dump() for m in m_list]

        # 2. Search FTS5 BM25 ranked index
        fts_hits = self.memory.search_fts(query, limit=top_k * 2 if rerank else top_k)
        results["observations"] = fts_hits

        # 3. Search Obsidian Vault Synapse
        vault_hits = self.vault.search_vault(query, max_results=top_k * 2 if rerank else top_k)
        results["vault_notes"] = vault_hits

        # 4. Optional Neural Reranking pass via Qwen3-Reranker
        if rerank and (fts_hits or vault_hits):
            try:
                from retrieval_engine import retrieval_engine
                if fts_hits:
                    obs_texts = [f"{h.get('title', '')} {h.get('content', '')}" for h in fts_hits]
                    reranked_obs = retrieval_engine.rerank(query, obs_texts, top_k=top_k)
                    results["observations"] = [fts_hits[r["index"]] for r in reranked_obs if r["index"] < len(fts_hits)]

                if vault_hits:
                    vh_texts = [f"{v.get('title', '')} {v.get('snippet', '')}" for v in vault_hits]
                    reranked_vh = retrieval_engine.rerank(query, vh_texts, top_k=top_k)
                    results["vault_notes"] = [vault_hits[r["index"]] for r in reranked_vh if r["index"] < len(vault_hits)]
            except Exception:
                pass

        total_matches = len(results["mental_models"]) + len(results["observations"]) + len(results["vault_notes"])
        return {
            "status": "success",
            "primitive": "recall",
            "query": query,
            "total_matches": total_matches,
            "results": results,
        }

    def reflect(
        self,
        topic: Optional[str] = None,
        session_id: str = "default_session",
    ) -> Dict[str, Any]:
        """
        Hindsight Reflect Primitive: Runs an epistemic reflection pass.
        Gathers recent episodic messages, facts, and tool errors to crystallize Mental Models.
        """
        messages = self.memory.get_messages(session_id, limit=30)
        recent_facts = self.memory.get_facts()[:20]

        observations: List[str] = [m.content for m in messages if m.role in ["user", "assistant"]]
        observations.extend(f.value for f in recent_facts)

        from mental_models import mental_models
        reflection_result = mental_models.reflect(
            topic=topic,
            observations=observations,
            sync_vault=True,
        )

        return {
            "status": "reflected",
            "primitive": "reflect",
            "session_id": session_id,
            "details": reflection_result,
            "active_models_count": len(mental_models.get_active_models(min_confidence=0.3)),
        }

# Singleton instance
five_layer_memory = FiveLayerMemorySystem()
