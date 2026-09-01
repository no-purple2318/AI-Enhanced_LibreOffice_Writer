"""LibreOffice PyUNO connection manager supporting live socket, pipe, and offline modes."""

import os
import sys
from typing import Any, Optional

from src.utils.logging import get_logger

logger = get_logger("ai_writer.connection")


class LibreOfficeConnection:
    """Manages the PyUNO connection to a running LibreOffice instance."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 2002,
        pipe_name: str = "uno_ai_pipe",
        connection_type: str = "socket",
    ):
        self.host = host
        self.port = port
        self.pipe_name = pipe_name
        self.connection_type = connection_type
        self._local_context: Optional[Any] = None
        self._resolver: Optional[Any] = None
        self._remote_context: Optional[Any] = None
        self._desktop: Optional[Any] = None
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self._desktop is not None

    def connect(self) -> bool:
        """Establish connection to LibreOffice instance via PyUNO."""
        try:
            import uno
            from com.sun.star.connection import NoConnectException

            self._local_context = uno.getComponentContext()
            self._resolver = self._local_context.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", self._local_context
            )

            if self.connection_type == "pipe":
                conn_str = f"uno:pipe,name={self.pipe_name};urp;StarOffice.ComponentContext"
            else:
                conn_str = f"uno:socket,host={self.host},port={self.port};urp;StarOffice.ComponentContext"

            logger.info(f"Attempting PyUNO connection via: {conn_str}")
            self._remote_context = self._resolver.resolve(conn_str)
            smgr = self._remote_context.ServiceManager
            self._desktop = smgr.createInstanceWithContext(
                "com.sun.star.frame.Desktop", self._remote_context
            )
            self._connected = True
            logger.info("Successfully connected to LibreOffice Desktop.")
            return True

        except ImportError:
            logger.warning("PyUNO library ('uno') not found in current Python environment.")
            self._connected = False
            return False
        except Exception as e:
            logger.warning(f"Could not connect to live LibreOffice instance: {e}")
            self._connected = False
            return False

    def get_current_document(self) -> Optional[Any]:
        """Get currently active LibreOffice document component (XTextDocument)."""
        if not self.is_connected:
            return None
        try:
            model = self._desktop.getCurrentComponent()
            if model and hasattr(model, "supportsService"):
                if model.supportsService("com.sun.star.text.TextDocument"):
                    return model
                else:
                    logger.warning("Current active document is not a LibreOffice Writer document.")
            return None
        except Exception as e:
            logger.error(f"Error retrieving current document: {e}")
            return None

    def disconnect(self) -> None:
        """Close connection handles."""
        self._connected = False
        self._desktop = None
        self._remote_context = None
        logger.info("Disconnected from LibreOffice.")
