"""
Demo Python module for PritVis visualization project.
This file is bundled with the project and scanned for security patterns.
It does not run on its own inside PritVis; it serves as project metadata.
"""


def generate_particle_count():
    """Return the number of particles used by the visualization."""
    return 80


def get_project_meta():
    """Return project metadata."""
    return {
        "name": "PritVis Demo",
        "version": "0.1.0",
        "author": "PritVis User",
        "description": "A particle network visualization running inside PritVis."
    }


if __name__ == "__main__":
    meta = get_project_meta()
    print(f"{meta['name']} v{meta['version']}")
    print(f"Particles: {generate_particle_count()}")
