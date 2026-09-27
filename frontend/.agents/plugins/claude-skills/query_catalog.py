#!/usr/bin/env python3
"""
CLI Query Tool for the Claude Skills Dynamic Catalog.
Categorized using the AgenticSkills.io 16-Category Taxonomy.

Usage:
  python query_catalog.py --search <keyword>
  python query_catalog.py --category <category>
  python query_catalog.py --categories
  python query_catalog.py --type <skill|agent>
  python query_catalog.py --inspect <id>
  python query_catalog.py --stats
"""
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

PLUGIN_DIR = Path(__file__).resolve().parent
CATALOG_FILE = PLUGIN_DIR / "catalog.json"

CATEGORIES_META = {
    "web-development": {
        "title": "Web Development",
        "description": "Frontend frameworks, React, Next.js, and modern web tooling"
    },
    "backend": {
        "title": "Backend & APIs",
        "description": "Server-side development, databases, and API integration patterns"
    },
    "devops": {
        "title": "DevOps & Infrastructure",
        "description": "Deployment, CI/CD, cloud infrastructure, and automation"
    },
    "testing": {
        "title": "Code Quality & Testing",
        "description": "Testing methodologies, debugging, code review, and quality assurance"
    },
    "ai-ml": {
        "title": "AI/ML Development",
        "description": "Machine learning, model training, AI research, and generative AI"
    },
    "data-science": {
        "title": "Data Science",
        "description": "Data visualization, scientific computing, and analytics"
    },
    "marketing": {
        "title": "Content & Marketing",
        "description": "Copywriting, content strategy, and marketing automation"
    },
    "seo": {
        "title": "SEO & Growth",
        "description": "Search engine optimization, GEO/AEO, analytics, and growth strategies"
    },
    "design": {
        "title": "Design & UI/UX",
        "description": "UI design systems, accessibility, and user experience patterns"
    },
    "productivity": {
        "title": "Productivity",
        "description": "Workflow optimization, ideation, and developer productivity tools"
    },
    "documents": {
        "title": "Document Creation",
        "description": "PDF generation, documentation, and structured content creation"
    },
    "security": {
        "title": "Security",
        "description": "Security auditing, static analysis, and vulnerability detection"
    },
    "database": {
        "title": "Database",
        "description": "Database optimization, migrations, and data modeling"
    },
    "mobile": {
        "title": "Mobile Development",
        "description": "React Native, iOS, Android, and cross-platform development"
    },
    "agents": {
        "title": "Agent Architecture",
        "description": "Multi-agent systems, MCP servers, and agent orchestration"
    },
    "official": {
        "title": "Official Partners",
        "description": "Skills from official platform teams and verified partners"
    }
}

CATEGORY_ALIASES = {
    "web": "web-development",
    "web-dev": "web-development",
    "web-development": "web-development",
    "backend": "backend",
    "backend-api": "backend",
    "backend-apis": "backend",
    "api": "backend",
    "apis": "backend",
    "devops": "devops",
    "devops-infra": "devops",
    "devops-infrastructure": "devops",
    "cloud": "devops",
    "infra": "devops",
    "testing": "testing",
    "test": "testing",
    "code-quality": "testing",
    "code-quality-testing": "testing",
    "qa": "testing",
    "ai-ml": "ai-ml",
    "ai": "ai-ml",
    "ml": "ai-ml",
    "ai-ml-development": "ai-ml",
    "data-science": "data-science",
    "data": "data-science",
    "datascience": "data-science",
    "marketing": "marketing",
    "content": "marketing",
    "content-marketing": "marketing",
    "seo": "seo",
    "growth": "seo",
    "seo-growth": "seo",
    "design": "design",
    "ui": "design",
    "ux": "design",
    "ui-ux": "design",
    "design-ui-ux": "design",
    "productivity": "productivity",
    "workflow": "productivity",
    "tools": "productivity",
    "documents": "documents",
    "docs": "documents",
    "document-creation": "documents",
    "pdf": "documents",
    "security": "security",
    "sec": "security",
    "auth": "security",
    "database": "database",
    "db": "database",
    "databases": "database",
    "storage": "database",
    "mobile": "mobile",
    "mobile-development": "mobile",
    "ios": "mobile",
    "android": "mobile",
    "agents": "agents",
    "agent": "agents",
    "agent-architecture": "agents",
    "mcp": "agents",
    "official": "official",
    "partners": "official",
    "official-partners": "official"
}

def resolve_category(cat_input):
    if not cat_input:
        return None
    cleaned = cat_input.lower().strip()
    return CATEGORY_ALIASES.get(cleaned, cleaned)

def load_catalog():
    if not CATALOG_FILE.exists():
        print(f"Error: Catalog file not found at {CATALOG_FILE}")
        sys.exit(1)
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def show_categories(catalog):
    counts = defaultdict(int)
    for v in catalog.values():
        cat = v.get("category", "productivity")
        counts[cat] += 1
        # also check categories list
        for c in v.get("categories", []):
            if c != cat:
                counts[c] += 1

    print("=" * 80)
    print(" AgenticSkills.io 16-Category Taxonomy")
    print("=" * 80)
    print(f"{'Category Key':<18} {'Title':<26} {'Items':<7} {'Description'}")
    print("-" * 80)
    for cat_key, meta in CATEGORIES_META.items():
        cnt = counts.get(cat_key, 0)
        print(f"{cat_key:<18} {meta['title']:<26} {cnt:<7} {meta['description']}")
    print("=" * 80)
    print("Query any category with: python query_catalog.py --category <category-key>")

def show_stats(catalog):
    skills = [v for v in catalog.values() if v.get("type") == "skill"]
    agents = [v for v in catalog.values() if v.get("type") == "agent"]
    installed = [v for v in catalog.values() if v.get("installed_core")]
    agentic = [v for v in catalog.values() if v.get("source") == "agenticskills.io"]
    
    by_category = defaultdict(int)
    for v in catalog.values():
        c = v.get("category", "productivity")
        by_category[c] += 1
        
    print("=" * 70)
    print(" Claude Skills & AgenticSkills Catalog Overview")
    print("=" * 70)
    print(f"Total Indexed Items:       {len(catalog)}")
    print(f"  - Skills:                {len(skills)}")
    print(f"  - Agents:                {len(agents)}")
    print(f"  - Active Core Installed: {len(installed)}")
    print(f"  - From AgenticSkills.io: {len(agentic)}")
    print("")
    print("Breakdown by AgenticSkills 16 Categories:")
    print("-" * 70)
    for cat_key, meta in CATEGORIES_META.items():
        cnt = by_category.get(cat_key, 0)
        print(f"  * {cat_key:<18} ({meta['title']:<24}): {cnt} items")
    print("=" * 70)

def search_catalog(catalog, term=None, category=None, domain=None, item_type=None, limit=25):
    results = []
    t = term.lower() if term else None
    cat_filter = resolve_category(category) if category else None
    
    for item_id, data in catalog.items():
        if cat_filter:
            item_cats = [c.lower() for c in data.get("categories", [data.get("category", "")])]
            if cat_filter.lower() not in item_cats and data.get("category", "").lower() != cat_filter.lower():
                continue
        if domain and data.get("domain", "").lower() != domain.lower():
            continue
        if item_type and data.get("type", "").lower() != item_type.lower():
            continue
        if t:
            searchable = f"{item_id} {data.get('name', '')} {data.get('description', '')} {data.get('author', '')}".lower()
            if t not in searchable:
                continue
        results.append(data)
        
    print("")
    filter_desc = []
    if cat_filter:
        cat_title = CATEGORIES_META.get(cat_filter, {}).get("title", cat_filter)
        filter_desc.append(f"Category: {cat_title} [{cat_filter}]")
    if term:
        filter_desc.append(f"Term: '{term}'")
    if item_type:
        filter_desc.append(f"Type: {item_type}")
    filter_str = f" ({', '.join(filter_desc)})" if filter_desc else ""
    
    print(f"Found {len(results)} matching items{filter_str} (showing up to {limit}):")
    print("-" * 85)
    for r in results[:limit]:
        status = "[CORE]" if r.get("installed_core") else "[ON-DEMAND]"
        t_label = r.get("type", "item").upper()
        cat_name = r.get("category", "misc")
        rank = f"[{r['rank']}] " if r.get("rank") else ""
        desc = (r.get("description", "") or "").replace("\n", " ")[:60]
        print(f"{status:<11} [{t_label}] {r['id']:<28} {rank}({cat_name})")
        print(f"   {desc}...")
    print("-" * 85)
    if len(results) > limit:
        print(f"... and {len(results) - limit} more. Refine your query with --category or --search.")

def inspect_item(catalog, item_id):
    item = catalog.get(item_id)
    if not item:
        # try case-insensitive and dash-insensitive
        for k, v in catalog.items():
            if k.lower() == item_id.lower() or k.replace("-", "") == item_id.replace("-", ""):
                item = v
                break
    if not item:
        print(f"Item '{item_id}' not found in catalog.")
        print("Tip: Run 'python query_catalog.py --search <keyword>' or '--categories' to discover items.")
        return
        
    lib_path = PLUGIN_DIR / item.get("library_file", "")
    cat_key = item.get("category", "misc")
    cat_title = CATEGORIES_META.get(cat_key, {}).get("title", cat_key)
    
    print("=" * 75)
    print(f" ID:             {item['id']}")
    print(f" Name:           {item.get('name')}")
    print(f" Type:           {item.get('type')}")
    print(f" Category:       {cat_title} (`{cat_key}`)")
    if item.get("categories"):
        print(f" All Categories: {', '.join(item.get('categories'))}")
    if item.get("author"):
        print(f" Author:         {item.get('author')}")
    if item.get("rank"):
        print(f" Rank:           {item.get('rank')}")
    if item.get("platforms"):
        print(f" Platforms:      {', '.join(item.get('platforms'))}")
    if item.get("install_command"):
        print(f" Install CLI:    {item.get('install_command')}")
    print(f" Source:         {item.get('source')}")
    print(f" Active Core:    {item.get('installed_core')}")
    if item.get("url"):
        print(f" Directory URL:  {item.get('url')}")
    print(f" Description:    {item.get('description')}")
    print("=" * 75)
    
    if lib_path.exists():
        print(f"\n--- [Documentation from {item.get('library_file')}] ---\n")
        content = lib_path.read_text(encoding="utf-8", errors="replace")
        print(content[:3000])
        if len(content) > 3000:
            print(f"\n... [truncated {len(content) - 3000} bytes. Full file: {lib_path}]")
    else:
        print(f"Library file not found at {lib_path}")

def main():
    parser = argparse.ArgumentParser(description="Claude Skills & AgenticSkills Catalog CLI")
    parser.add_argument("--search", "-s", type=str, help="Search keyword in id, name, description, author")
    parser.add_argument("--category", "-c", type=str, help="Filter by AgenticSkills category (e.g. web-development, backend, devops, design, testing, etc.)")
    parser.add_argument("--categories", action="store_true", help="List all 16 AgenticSkills categories with descriptions and counts")
    parser.add_argument("--domain", "-d", type=str, help="Legacy domain filter")
    parser.add_argument("--type", "-t", type=str, choices=["skill", "agent"], help="Filter by type")
    parser.add_argument("--inspect", "-i", type=str, help="Inspect full documentation and install command for an item")
    parser.add_argument("--stats", action="store_true", help="Show catalog summary statistics")
    parser.add_argument("--limit", "-l", type=int, default=25, help="Max results to display")
    
    args = parser.parse_args()
    catalog = load_catalog()
    
    if args.categories:
        show_categories(catalog)
    elif args.stats or (len(sys.argv) == 1):
        show_stats(catalog)
    elif args.inspect:
        inspect_item(catalog, args.inspect)
    else:
        search_catalog(catalog, term=args.search, category=args.category, domain=args.domain, item_type=args.type, limit=args.limit)

if __name__ == "__main__":
    main()
