"""PetSoul entry point."""

import logging
import uvicorn
from pet_soul.config import CONFIG
from pet_soul.api.app import app


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    uvicorn.run(app, host=CONFIG.host, port=CONFIG.port)


if __name__ == "__main__":
    main()
