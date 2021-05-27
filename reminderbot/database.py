###############################################################################
# Project: Mort de Gana Bot
# Authors:
# - Ytturi
# Descr: PostgreSQL database connection
###############################################################################
from __future__ import annotations
from typing import Optional
from sqlalchemy.engine import create_engine, Engine
from sqlalchemy import Table, Column, MetaData
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.types import BigInteger, DateTime, Text


class Database:
    def __init__(self, psql_connection: Optional[str]) -> None:
        """
        Initialize the local variables according to the conf
        """
        self.psql_connection = psql_connection

        # Init engine and tables as None for lazy-load
        self._engine = None
        self._chat_table = None
        self._reminder_table = None

    def __del__(self) -> None:
        """
        When this object is destroy we also want to close the connection engine
        """

        if self._engine is not None:
            del self._engine

    @property
    def enabled(self) -> bool:
        """Return wether the database can be used or not

        Returns:
            bool: True if there is a connection, False otherwise
        """

        return True if self.psql_connection else False

    @property
    def engine(self) -> Engine:
        """Return the database engine with the psql connection from the confs.

        The engine will be created if it hasn't been created yet
        and will be cached.

        Returns:
            Engine: Engine connection to the psql database
        """
        if self._engine is not None:
            return self._engine

        if not self.enabled:
            raise Exception(
                "Trying to retrieve the database engine but there is no connection"
            )

        self._engine = create_engine(self.psql_connection)
        return self._engine

    @property
    def reminder(self) -> Table:
        """
        Get the `motos_counter` table definition.

        Returns:
            Table: `motos_counter` table definition
        """

        if self._reminder_table is None:
            self._build_reminder_table()

        return self._reminder_table

    def _build_reminder_table(self, init: bool = False) -> None:
        """
        Create the Table with the connection metadata
        """

        metadata = MetaData(self.engine)
        self._reminder_table = Table(
            "reminder",
            metadata,
            Column("id", Integer, primary_key=True, index=True),
            Column("chat_id", Integer, index=True, nullable=False),
            Column("title", Text, nullable=False),
            Column("date", DateTime, nullable=False),
            Column("text", Text, nullable=False),
        )

        if init:
            metadata.create_all()

    @property
    def chat(self) -> Table:
        """
        Get the `motos_counter` table definition.

        Returns:
            Table: `motos_counter` table definition
        """

        if self._chat_table is None:
            self._build_chat_table()

        return self._chat_table

    def _build_chat_table(self, init: bool = False) -> None:
        """
        Create the Table with the connection metadata
        """

        metadata = MetaData(self.engine)
        self._chat_table = Table(
            "chat",
            metadata,
            Column("id", Integer, primary_key=True, index=True),
            Column("chat_id", BigInteger, index=True, nullable=False),
            Column("name", Text, nullable=False),
        )

        if init:
            metadata.create_all()

    def init_database(self) -> None:
        """
        Create all the database Tables

        Warning: This method does not update existing tables
        """

        if self.enabled is False:
            raise Exception(
                "Trying to initialize the database without database connection"
            )

        self._build_reminder_table(init=True)
        self._build_chat_table(init=True)
