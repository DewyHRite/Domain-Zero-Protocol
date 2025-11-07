#!/usr/bin/env python3
"""
Domain Zero Protocol - Agent Banner System
Version: 1.0.0
Date: November 7, 2025

Color-coded banner system for Domain Zero Protocol agents.
Provides consistent visual identity across terminal, markdown, and web interfaces.
"""

import sys


class ANSIColors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Agent Primary Colors (closest ANSI equivalents)
    GOJO_CYAN = "\033[1;36m"      # Bold Cyan
    YUUJI_RED = "\033[1;31m"      # Bold Red
    MEGUMI_PURPLE = "\033[1;35m"  # Bold Magenta (Purple)
    NOBARA_GOLD = "\033[1;33m"    # Bold Yellow (Gold)


class AgentBanner:
    """Generate color-coded banners for Domain Zero agents."""

    AGENTS = {
        "gojo": {
            "name": "SATORU GOJO",
            "title": "Mission Control & Protocol Guardian",
            "subtitle": "Domain Expansion: Domain Zero",
            "emoji": "🌀",
            "color": ANSIColors.GOJO_CYAN,
            "hex_primary": "#00D9FF",
            "hex_alt": "#0EA5E9",
            "meaning": "Limitless, boundless authority, calm control"
        },
        "yuuji": {
            "name": "YUUJI ITADORI",
            "title": "Implementation Specialist",
            "subtitle": "Test-Driven Delivery, Rapid Iteration",
            "emoji": "⚡",
            "color": ANSIColors.YUUJI_RED,
            "hex_primary": "#EF4444",
            "hex_alt": "#DC2626",
            "meaning": "Energy, determination, weight of responsibility"
        },
        "megumi": {
            "name": "MEGUMI FUSHIGURO",
            "title": "Security & Analysis Specialist",
            "subtitle": "Threat Modeling First, OWASP-Aligned Controls",
            "emoji": "🐺",
            "color": ANSIColors.MEGUMI_PURPLE,
            "hex_primary": "#8B5CF6",
            "hex_alt": "#6366F1",
            "meaning": "Strategic thinking, mystery, analytical precision"
        },
        "nobara": {
            "name": "NOBARA KUGISAKI",
            "title": "Creative Strategy & UX Specialist",
            "subtitle": "User Insight, Narrative, and Delight",
            "emoji": "🔨",
            "color": ANSIColors.NOBARA_GOLD,
            "hex_primary": "#F59E0B",
            "hex_alt": "#F97316",
            "meaning": "Creativity, boldness, user-centered warmth"
        }
    }

    @staticmethod
    def terminal_banner(agent_key: str, include_color: bool = True) -> str:
        """
        Generate terminal banner with ANSI colors.

        Args:
            agent_key: One of 'gojo', 'yuuji', 'megumi', 'nobara'
            include_color: If False, returns plain text banner

        Returns:
            Formatted banner string with ANSI codes (if include_color=True)
        """
        agent = AgentBanner.AGENTS.get(agent_key.lower())
        if not agent:
            raise ValueError(f"Unknown agent: {agent_key}")

        color = agent["color"] if include_color else ""
        reset = ANSIColors.RESET if include_color else ""

        # Format title to fit in banner (max 42 chars)
        title = agent['title'].upper()
        if len(title) > 42:
            title = title[:39] + "..."

        banner = f"""{color}╔═══════════════════════════════════════════════════════════════╗{reset}
{color}║  {agent['emoji']} {agent['name']:<25} - {title:<30} ║{reset}
{color}║     {agent['subtitle']:<58} ║{reset}
{color}╚═══════════════════════════════════════════════════════════════╝{reset}"""

        return banner

    @staticmethod
    def markdown_banner(agent_key: str, use_html: bool = True) -> str:
        """
        Generate Markdown banner (HTML or plain).

        Args:
            agent_key: One of 'gojo', 'yuuji', 'megumi', 'nobara'
            use_html: If True, uses HTML with gradient; if False, plain Markdown

        Returns:
            Markdown-formatted banner
        """
        agent = AgentBanner.AGENTS.get(agent_key.lower())
        if not agent:
            raise ValueError(f"Unknown agent: {agent_key}")

        if use_html:
            # Determine text color based on background
            text_color = "#000" if agent_key in ["gojo", "nobara"] else "#FFF"

            return f"""<div style="background: linear-gradient(135deg, {agent['hex_primary']} 0%, {agent['hex_alt']} 100%); padding: 20px; border-radius: 8px; color: {text_color}; margin: 20px 0;">
  <h2 style="margin: 0; font-weight: bold;">{agent['emoji']} {agent['name']} - {agent['title']}</h2>
  <p style="margin: 5px 0 0 0; opacity: 0.9;">{agent['subtitle']}</p>
</div>"""
        else:
            return f"""> **{agent['emoji']} {agent['name']} - {agent['title']}**
> *{agent['subtitle']}*
>
> Primary Color: {agent['hex_primary']} - {agent['meaning']}"""

    @staticmethod
    def ascii_art_banner(agent_key: str) -> str:
        """
        Generate ASCII art banner (pure text, no color codes).

        Args:
            agent_key: One of 'gojo', 'yuuji', 'megumi', 'nobara'

        Returns:
            ASCII art banner
        """
        agent = AgentBanner.AGENTS.get(agent_key.lower())
        if not agent:
            raise ValueError(f"Unknown agent: {agent_key}")

        return f"""  ╔════════════════════════════════════════════════════════════════════╗
  ║                                                                    ║
  ║   {agent['emoji']}  {agent['name']:<60} ║
  ║      {agent['title']:<62} ║
  ║                                                                    ║
  ║      DOMAIN: {agent['subtitle']:<54} ║
  ║      COLOR:  {agent['hex_primary']:<54} ║
  ║                                                                    ║
  ╚════════════════════════════════════════════════════════════════════╝"""

    @staticmethod
    def get_agent_info(agent_key: str) -> dict:
        """
        Get full agent configuration.

        Args:
            agent_key: One of 'gojo', 'yuuji', 'megumi', 'nobara'

        Returns:
            Dictionary with agent configuration
        """
        agent = AgentBanner.AGENTS.get(agent_key.lower())
        if not agent:
            raise ValueError(f"Unknown agent: {agent_key}")
        return agent.copy()


def main():
    """Demo of all banner types."""

    # Fix Windows console encoding
    if sys.platform == 'win32':
        try:
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        except:
            pass

    print("\n" + "="*70)
    print("Domain Zero Protocol - Agent Banner System Demo")
    print("="*70)

    print("\n### TERMINAL BANNERS (with color) ###\n")
    for agent in ["gojo", "yuuji", "megumi", "nobara"]:
        print(AgentBanner.terminal_banner(agent))
        print()

    print("\n### TERMINAL BANNERS (plain text) ###\n")
    for agent in ["gojo", "yuuji", "megumi", "nobara"]:
        print(AgentBanner.terminal_banner(agent, include_color=False))
        print()

    print("\n### MARKDOWN BANNERS (HTML) ###\n")
    for agent in ["gojo", "yuuji", "megumi", "nobara"]:
        print(AgentBanner.markdown_banner(agent, use_html=True))
        print()

    print("\n### MARKDOWN BANNERS (Plain) ###\n")
    for agent in ["gojo", "yuuji", "megumi", "nobara"]:
        print(AgentBanner.markdown_banner(agent, use_html=False))
        print()

    print("\n### ASCII ART BANNERS ###\n")
    for agent in ["gojo", "yuuji", "megumi", "nobara"]:
        print(AgentBanner.ascii_art_banner(agent))
        print()


if __name__ == "__main__":
    main()
