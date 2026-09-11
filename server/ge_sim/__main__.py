"""
ge-sim: Galactic Empire Simulation Engine
Entry point for running as a module: python -m ge_sim
"""
import asyncio
from ge_sim.sim_engine import main

if __name__ == "__main__":
    asyncio.run(main())
