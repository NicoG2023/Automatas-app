"""Desktop application for building and simulating finite automata."""


def main() -> int:
    """Run the desktop application through the project entry point."""
    from app_automatas.main import main as run_application

    return run_application()


__all__ = ["main"]
