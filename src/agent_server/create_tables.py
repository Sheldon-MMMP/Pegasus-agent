import agent_server.models
from agent_server.db import Base, engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Created database tables.")


if __name__ == "__main__":
    main()
