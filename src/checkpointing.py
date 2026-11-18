"""PostgreSQL checkpointing so a run survives restarts and can wait days at a gate."""
from contextlib import contextmanager


@contextmanager
def get_checkpointer(dsn: str | None):
    if dsn:
        from langgraph.checkpoint.postgres import PostgresSaver
        with PostgresSaver.from_conn_string(dsn) as saver:
            saver.setup()  # creates checkpoint tables on first run
            yield saver
    else:  # local dev and tests only. State is lost on restart.
        try:
            from langgraph.checkpoint.memory import InMemorySaver as Saver
        except ImportError:
            from langgraph.checkpoint.memory import MemorySaver as Saver
        yield Saver()
