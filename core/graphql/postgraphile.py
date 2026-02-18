'''
Copyright 2019-Present The OpenUBA Platform Authors
postgraphile integration for graphql api

Note: In Kubernetes deployments, PostGraphile runs as a separate container
using the official graphile/postgraphile Docker image. This module is only
used for local development where PostGraphile runs as a subprocess.
'''

import os
import logging
import subprocess
import threading
from typing import Optional

logger = logging.getLogger(__name__)


class PostGraphileServer:
    '''
    manages postgraphile subprocess for graphql api
    '''

    def __init__(
        self,
        database_url: str,
        schema: str = "public",
        host: str = "0.0.0.0",
        port: int = 5000
    ):
        self.database_url = database_url
        self.schema = schema
        self.host = host
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.thread: Optional[threading.Thread] = None

    def start(self) -> None:
        '''
        start postgraphile server as subprocess
        '''
        if self.process:
            logger.warning("postgraphile already running")
            return

        # check if postgraphile is installed
        try:
            subprocess.run(
                ["npx", "--version"],
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("npx not found - postgraphile requires node.js")
            logger.info("graphql api will not be available")
            return

        # build postgraphile command
        cmd = [
            "npx",
            "postgraphile",
            "-c", self.database_url,
            "-s", self.schema,
            "--host", self.host,
            "--port", str(self.port),
            "--cors",
            "--enhance-graphiql",
            "--watch",
            "--subscriptions",  # enable subscriptions
            "--simple-subscriptions"  # use simple subscriptions (no live queries)
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"postgraphile started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"failed to start postgraphile: {e}")
            self.process = None

    def stop(self) -> None:
        '''
        stop postgraphile server
        '''
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            logger.info("postgraphile stopped")

    def is_running(self) -> bool:
        '''
        check if postgraphile is running
        '''
        return self.process is not None and self.process.poll() is None


def get_graphql_url() -> str:
    '''
    get graphql endpoint url
    '''
    host = os.getenv("POSTGRAPHILE_HOST", "localhost")
    port = int(os.getenv("POSTGRAPHILE_PORT", "5000"))
    return f"http://{host}:{port}/graphql"


def get_graphiql_url() -> str:
    '''
    get graphiql interface url
    '''
    host = os.getenv("POSTGRAPHILE_HOST", "localhost")
    port = int(os.getenv("POSTGRAPHILE_PORT", "5000"))
    return f"http://{host}:{port}/graphiql"

