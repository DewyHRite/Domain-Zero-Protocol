#!/usr/bin/env python3
"""
AI Collaboration Protocol Setup Wizard
Version: 1.0.0

Generates a customized protocol configuration for any software project.
Supports multiple themes: JJK, AOT, Naruto, Professional
"""

import os
import sys
import shutil
import yaml
from pathlib import Path
from datetime import datetime

# Theme Registry
THEMES = {
    "1": {
        "name": "jjk",
        "display": "Jujutsu Kaisen",
        "description": "Yuuji (Heart), Megumi (Mind), Gojo (Observer)",
        "style": "Enthusiastic, supernatural anime vibes",
        "roles": {
            "implementer": "Yuuji Itadori - The Heart",
            "analyst": "Megumi Fushiguro - The Mind",
            "observer": "Satoru Gojo - The Observer"
        }
    },
    "2": {
        "name": "aot",
        "display": "Attack on Titan",
        "description": "Eren (Will), Armin (Strategist), Levi (Commander)",
        "style": "Determined, strategic, disciplined",
        "roles": {
            "implementer": "Eren Yeager - The Relentless Will",
            "analyst": "Armin Arlert - The Brilliant Strategist",
            "observer": "Levi Ackerman - The Uncompromising Commander"
        }
    },
    "3": {
        "name": "naruto",
        "display": "Naruto",
        "description": "Naruto (Dreamer), Sasuke (Perfectionist), Kakashi (Mentor)",
        "style": "Optimistic, perfectionist, wise",
        "roles": {
            "implementer": "Naruto Uzumaki - The Unpredictable Dreamer",
            "analyst": "Sasuke Uchiha - The Perfectionist Genius",
            "observer": "Kakashi Hatake - The Copy Ninja Mentor"
        }
    },
    "4": {
        "name": "professional",
        "display": "Professional",
        "description": "Developer, Architect, Manager",
        "style": "Corporate, formal, business-focused",
        "roles": {
            "implementer": "Senior Developer - Implementation Specialist",
            "analyst": "Solutions Architect - Strategic Analyst",
            "observer": "Engineering Manager - Project Overseer"
        }
    }
}

PROJECT_TYPES = {
    "1": "web",
    "2": "mobile", 
    "3": "backend",
    "4": "fullstack",
    "5": "ml",
    "6": "desktop",
    "7": "game",
    "8": "embedded",
    "9": "other"
}

def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def banner():
    """Display welcome banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     AI COLLABORATION PROTOCOL SETUP WIZARD                ║
║     Universal Coding Assistant System v1.0.0              ║
║                                                           ║
║     Transform your AI into specialized development roles  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

def print_section(title):
    """Print section header."""
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print('─' * 60)

def get_project_info():
    """Gather project information."""
    print_section("📋 PROJECT INFORMATION")
    
    name = input("\nProject name: ").strip()
    if not name:
        name = "My Project"
        print(f"  → Using default: {name}")
    
    print("\nProject type:")
    print("  1. Web application (React, Vue, Angular, etc.)")
    print("  2. Mobile application (React Native, Flutter, etc.)")
    print("  3. Backend API (REST, GraphQL, etc.)")
    print("  4. Full-stack application")
    print("  5. Machine Learning / AI")
    print("  6. Desktop application")
    print("  7. Game development")
    print("  8. Embedded systems / IoT")
    print("  9. Other")
    
    type_choice = input("\nSelect project type [1-9]: ").strip() or "1"
    project_type = PROJECT_TYPES.get(type_choice, "other")
    
    description = input("\nBrief description (optional): ").strip()
    if not description:
        description = f"A {project_type} project"
        print(f"  → Using default: {description}")
    
    return {
        "name": name,
        "type": project_type,
        "description": description
    }

def get_tech_stack():
    """Gather technology stack information."""
    print_section("💻 TECHNOLOGY STACK")
    
    print("\nEnter technologies (comma-separated, or press Enter to skip)")
    
    languages_input = input("\nProgramming languages (e.g., Python, JavaScript, Go): ").strip()
    languages = [l.strip() for l in languages_input.split(",")] if languages_input else []
    
    frameworks_input = input("Frameworks (e.g., React, Django, Express): ").strip()
    frameworks = [f.strip() for f in frameworks_input.split(",")] if frameworks_input else []
    
    databases_input = input("Databases (e.g., PostgreSQL, MongoDB, Redis): ").strip()
    databases = [d.strip() for d in databases_input.split(",")] if databases_input else []
    
    other_input = input("Other tools (e.g., Docker, Kubernetes, AWS): ").strip()
    other = [o.strip() for o in other_input.split(",")] if other_input else []
    
    return {
        "languages": languages,
        "frameworks": frameworks,
        "databases": databases,
        "other": other
    }

def display_theme_details(theme_key):
    """Display detailed information about a theme."""
    theme = THEMES[theme_key]
    
    print(f"\n┌─ {theme['display']} Theme ─────────────────────────")
    print(f"│")
    print(f"│  Style: {theme['style']}")
    print(f"│")
    print(f"│  Roles:")
    print(f"│    🔨 Implementer: {theme['roles']['implementer']}")
    print(f"│    🔍 Analyst:     {theme['roles']['analyst']}")
    print(f"│    👁️  Observer:    {theme['roles']['observer']}")
    print(f"│")
    print(f"└────────────────────────────────────────────────────")

def get_theme():
    """Select personality theme."""
    print_section("🎨 PERSONALITY THEME")
    
    print("\nChoose your AI assistant personalities:\n")
    
    for key, theme in THEMES.items():
        print(f"  {key}. {theme['display']:<20} - {theme['description']}")
    
    print("\n  5. Preview theme details")
    
    while True:
        choice = input("\nSelect theme [1-4] or 5 to preview: ").strip()
        
        if choice == "5":
            preview = input("Which theme to preview? [1-4]: ").strip()
            if preview in THEMES:
                display_theme_details(preview)
            continue
        
        if choice in THEMES:
            selected = THEMES[choice]
            print(f"\n✓ Selected: {selected['display']} theme")
            return selected["name"]
        
        if not choice:
            print("  → Using default: Jujutsu Kaisen")
            return "jjk"
        
        print("  ✗ Invalid choice. Please select 1-4.")

def get_custom_roles():
    """Configure custom role names."""
    print_section("🎭 CUSTOM ROLE NAMES (Optional)")
    
    print("\nWould you like to customize role names?")
    print("This overrides the theme names with your own.")
    
    customize = input("Customize roles? [y/N]: ").strip().lower()
    
    if customize not in ["y", "yes"]:
        return {"enabled": False}
    
    print("\nEnter custom names (or press Enter to keep theme defaults):")
    
    implementer = input("  Implementer name: ").strip()
    analyst = input("  Analyst name: ").strip()
    observer = input("  Observer name: ").strip()
    
    if not (implementer or analyst or observer):
        print("  → No custom names provided, using theme defaults")
        return {"enabled": False}
    
    custom = {"enabled": True}
    
    if implementer:
        invocation = input(f"  Invocation phrase for {implementer}: ").strip().lower() or implementer.lower()
        custom["implementer"] = {
            "name": implementer,
            "invocation": invocation,
            "emoji": "🔨"
        }
    
    if analyst:
        invocation = input(f"  Invocation phrase for {analyst}: ").strip().lower() or analyst.lower()
        custom["analyst"] = {
            "name": analyst,
            "invocation": invocation,
            "emoji": "🔍"
        }
    
    if observer:
        invocation = input(f"  Invocation phrase for {observer}: ").strip().lower() or observer.lower()
        custom["observer"] = {
            "name": observer,
            "invocation": invocation,
            "emoji": "👁️"
        }
    
    return custom

def yes_no(prompt, default="y"):
    """Helper for yes/no questions."""
    choices = "Y/n" if default == "y" else "y/N"
    response = input(f"{prompt} [{choices}]: ").strip().lower()
    
    if not response:
        return default == "y"
    
    return response in ["y", "yes"]

def get_workflow_preferences():
    """Configure workflow preferences."""
    print_section("⚙️  WORKFLOW PREFERENCES")
    
    print("\nConfigure how the protocol operates:\n")
    
    return {
        "require_security_review": yes_no("Require security reviews before production?", "y"),
        "auto_backup_before_changes": yes_no("Auto-backup code before changes?", "y"),
        "enforce_isolation": yes_no("Enforce strict role isolation?", "y"),
        "passive_monitoring": yes_no("Enable passive monitoring (observer always watching)?", "y"),
        "require_tests": yes_no("Require tests with implementations?", "y")
    }

def get_output_preferences():
    """Configure output preferences."""
    print_section("📄 OUTPUT PREFERENCES")
    
    print("\nConfigure output format and style:\n")
    
    emoji = yes_no("Use emoji in outputs?", "y")
    detailed = yes_no("Generate detailed logs?", "y")
    comments = yes_no("Include code comments in implementations?", "y")
    
    print("\nOutput style:")
    print("  1. Themed (full personality, recommended)")
    print("  2. Professional (formal, business-friendly)")
    print("  3. Minimal (concise, less personality)")
    
    style_choice = input("Select style [1-3]: ").strip() or "1"
    styles = {"1": "themed", "2": "professional", "3": "minimal"}
    style = styles.get(style_choice, "themed")
    
    return {
        "style": style,
        "emoji": emoji,
        "detailed_logs": detailed,
        "include_comments": comments,
        "format": "markdown"
    }

def get_monitoring_preferences():
    """Configure monitoring preferences."""
    print_section("📊 MONITORING PREFERENCES")
    
    print("\nConfigure what the observer tracks:\n")
    
    return {
        "track_quality": yes_no("Track code quality metrics?", "y"),
        "track_coverage": yes_no("Monitor test coverage?", "y"),
        "log_violations": yes_no("Log all protocol violations?", "y"),
        "pattern_analysis": yes_no("Compile behavioral pattern analysis?", "y")
    }

def get_notification_preferences():
    """Configure notification preferences."""
    print_section("🔔 NOTIFICATION PREFERENCES")
    
    print("\nConfigure when you receive reports:\n")
    
    violation_alerts = yes_no("Alert on protocol violations?", "y")
    session_summaries = yes_no("Generate session summaries?", "y")
    security_alerts = yes_no("Alert on security findings?", "y")
    
    print("\nProgress report frequency:")
    print("  1. Daily")
    print("  2. Weekly")
    print("  3. On-demand only")
    print("  4. Never")
    
    freq_choice = input("Select frequency [1-4]: ").strip() or "1"
    frequencies = {"1": "daily", "2": "weekly", "3": "on-demand", "4": "never"}
    frequency = frequencies.get(freq_choice, "daily")
    
    return {
        "violation_alerts": violation_alerts,
        "session_summaries": session_summaries,
        "progress_reports": frequency,
        "security_alerts": security_alerts
    }

def generate_config(project, tech_stack, theme, custom_roles, workflow, output, monitoring, notifications):
    """Generate complete configuration dictionary."""
    
    config = {
        "project": {
            **project,
            "tech_stack": tech_stack
        },
        "theme": theme,
        "custom_roles": custom_roles,
        "workflow": workflow,
        "output": output,
        "notifications": notifications,
        "monitoring": monitoring,
        "security": {
            "review_depth": "standard",
            "auto_scan": True,
            "owasp_check": True,
            "dependency_scan": False
        },
        "documentation": {
            "auto_dev_notes": True,
            "session_logs": True,
            "architecture_docs": False,
            "api_docs": False
        },
        "advanced": {
            "max_session_duration": 240,
            "auto_save_interval": 15,
            "violation_threshold": "medium",
            "experimental_features": False
        }
    }
    
    return config

def create_directory_structure(base_path):
    """Create protocol directory structure."""
    print("\n📁 Creating directory structure...")
    
    protocol_dir = Path(base_path) / "ai-protocol"
    
    # Create main directories
    dirs = [
        protocol_dir,
        protocol_dir / "core",
        protocol_dir / "roles",
        protocol_dir / "bindings",
        protocol_dir / "domains",
        protocol_dir / "themes",
        protocol_dir / "templates",
        protocol_dir / "logs"
    ]
    
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory.relative_to(base_path)}")
    
    return protocol_dir

def save_config(config, protocol_dir):
    """Save configuration to YAML file."""
    config_path = protocol_dir / "config.yml"
    
    print(f"\n💾 Saving configuration...")
    
    with open(config_path, 'w') as f:
        f.write("# AI Collaboration Protocol Configuration\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# Edit this file to customize your setup\n\n")
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    print(f"  ✓ Configuration saved: {config_path}")
    return config_path

def create_readme(protocol_dir, theme, project_name):
    """Create project-specific README."""
    
    theme_info = {
        "jjk": ("Jujutsu Kaisen", "Yuuji", "Megumi", "Gojo"),
        "aot": ("Attack on Titan", "Eren", "Armin", "Levi"),
        "naruto": ("Naruto", "Naruto", "Sasuke", "Kakashi"),
        "professional": ("Professional", "Developer", "Architect", "Manager")
    }
    
    theme_name, impl, anal, obs = theme_info.get(theme, ("Custom", "Implementer", "Analyst", "Observer"))
    
    readme_content = f"""# AI Protocol for {project_name}

## Quick Start

Your AI collaboration protocol is ready! You're using the **{theme_name}** theme.

### Your Roles

- **{impl}** (Implementer): Builds features and writes code
- **{anal}** (Analyst): Reviews security and architecture  
- **{obs}** (Observer): Monitors patterns and provides insights

### Getting Started

1. **Start a session** by invoking a role:
   ```
   "{impl}, help me implement user authentication"
   ```

2. **Review code** with the analyst:
   ```
   "{anal}, review this code for security issues"
   ```

3. **Get insights** from the observer:
   ```
   "{obs}, show me the session report"
   ```

### Configuration

Edit `config.yml` to customize:
- Role names and invocations
- Workflow preferences
- Output formats
- Monitoring settings

### Documentation

- See `core/quick-start.md` for detailed usage
- See `core/configuration-guide.md` for all options
- See `themes/{theme}/` for theme-specific guidance

### Next Steps

1. Read the quick start guide
2. Try invoking your first role
3. Customize config.yml if needed
4. Start building with AI assistance!

---

**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Theme**: {theme_name}
**Version**: 1.0.0
"""
    
    readme_path = protocol_dir / "README.md"
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    print(f"  ✓ README created: {readme_path}")

def create_templates(protocol_dir):
    """Create template files."""
    
    templates_dir = protocol_dir / "templates"
    
    # project-state.json template
    project_state = {
        "version": "1.0.0",
        "last_updated": datetime.now().isoformat(),
        "current_sprint": "Initial setup",
        "active_features": [],
        "known_issues": [],
        "last_review": None
    }
    
    with open(templates_dir / "project-state.json", 'w') as f:
        import json
        json.dump(project_state, f, indent=2)
    
    # dev-notes.md template
    dev_notes = """# Development Notes

## Current Sprint

**Sprint Goal**: [Define your sprint goal]

### Active Features
- [ ] Feature 1
- [ ] Feature 2

### Completed
- [x] Protocol setup

## Implementation Log

### YYYY-MM-DD - [Feature Name]
**Implementer**: [Role Name]
**Status**: [In Progress / Complete / Blocked]

**Changes**:
- Change 1
- Change 2

**Notes**:
- Important context
- Trade-offs made

---

## Testing Log

### [Feature Name]
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security review

---

## Security Review Log

### [Date] - [Feature]
**Analyst**: [Role Name]
**Severity**: [Critical / High / Medium / Low]

**Findings**:
1. Finding 1
2. Finding 2

**Status**: [Open / Fixed / Deferred]
"""
    
    with open(templates_dir / "dev-notes.md", 'w') as f:
        f.write(dev_notes)
    
    print("  ✓ Templates created")

def show_next_steps(config, protocol_dir):
    """Display next steps and usage instructions."""
    
    theme = config["theme"]
    project_name = config["project"]["name"]
    
    theme_invocations = {
        "jjk": ("Yuuji", "Megumi", "Gojo"),
        "aot": ("Eren", "Armin", "Levi"),
        "naruto": ("Naruto", "Sasuke", "Kakashi"),
        "professional": ("Developer", "Architect", "Manager")
    }
    
    impl, anal, obs = theme_invocations.get(theme, ("Implementer", "Analyst", "Observer"))
    
    if config["custom_roles"]["enabled"]:
        custom = config["custom_roles"]
        if "implementer" in custom:
            impl = custom["implementer"]["invocation"]
        if "analyst" in custom:
            anal = custom["analyst"]["invocation"]
        if "observer" in custom:
            obs = custom["observer"]["invocation"]
    
    clear_screen()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                  🎉 SETUP COMPLETE! 🎉                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n{'═' * 60}")
    print(f"  Project: {project_name}")
    print(f"  Theme: {theme.upper()}")
    print(f"  Location: {protocol_dir}")
    print(f"{'═' * 60}")
    
    print(f"\n🎭 YOUR ROLES")
    print(f"{'─' * 60}")
    print(f"  Implementer: {impl}")
    print(f"  Analyst:     {anal}")
    print(f"  Observer:    {obs}")
    
    print(f"\n💡 QUICK START")
    print(f"{'─' * 60}")
    print(f"  1. Start building:")
    print(f'     "{impl}, help me implement user authentication"')
    print(f"\n  2. Review your code:")
    print(f'     "{anal}, review this for security issues"')
    print(f"\n  3. Get session insights:")
    print(f'     "{obs}, show me the session report"')
    
    print(f"\n📁 KEY FILES")
    print(f"{'─' * 60}")
    print(f"  Configuration:    {protocol_dir}/config.yml")
    print(f"  Quick Start:      {protocol_dir}/README.md")
    print(f"  Dev Notes:        {protocol_dir}/templates/dev-notes.md")
    print(f"  Project State:    {protocol_dir}/templates/project-state.json")
    
    print(f"\n⚙️  CUSTOMIZATION")
    print(f"{'─' * 60}")
    print(f"  Edit config.yml to:")
    print(f"    - Change workflow settings")
    print(f"    - Adjust output preferences")
    print(f"    - Enable/disable features")
    print(f"    - Customize role names")
    
    print(f"\n📚 DOCUMENTATION")
    print(f"{'─' * 60}")
    print(f"  - System architecture: core/system-architecture.md")
    print(f"  - Configuration guide: core/configuration-guide.md")
    print(f"  - Theme guide: themes/{theme}/README.md")
    
    print(f"\n🚀 NEXT STEPS")
    print(f"{'─' * 60}")
    print(f"  1. Navigate to your project directory")
    print(f"  2. Review ai-protocol/README.md")
    print(f"  3. Start your first session!")
    
    print(f"\n{'═' * 60}")
    print(f"  Happy coding with AI collaboration! 🤖✨")
    print(f"{'═' * 60}\n")

def main():
    """Main setup wizard flow."""
    
    try:
        clear_screen()
        banner()
        
        input("\nPress Enter to begin setup...")
        clear_screen()
        banner()
        
        # Gather all information
        project = get_project_info()
        tech_stack = get_tech_stack()
        theme = get_theme()
        custom_roles = get_custom_roles()
        workflow = get_workflow_preferences()
        output = get_output_preferences()
        monitoring = get_monitoring_preferences()
        notifications = get_notification_preferences()
        
        # Generate configuration
        clear_screen()
        banner()
        print_section("⚙️  GENERATING CONFIGURATION")
        
        config = generate_config(
            project, tech_stack, theme, custom_roles,
            workflow, output, monitoring, notifications
        )
        
        # Create directory structure
        base_path = input("\nInstall location (press Enter for current directory): ").strip()
        if not base_path:
            base_path = "."
        
        protocol_dir = create_directory_structure(base_path)
        
        # Save files
        save_config(config, protocol_dir)
        create_readme(protocol_dir, theme, project["name"])
        create_templates(protocol_dir)
        
        # Show completion
        show_next_steps(config, protocol_dir)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.")
        return 1
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
