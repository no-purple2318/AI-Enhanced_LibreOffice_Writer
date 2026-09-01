"""LibreOffice PyUNO Addon Component for AI-Enhanced Document Assistant."""

import os
import sys

# Ensure src modules are resolvable within LibreOffice Python environment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import uno
    import unohelper
    from com.sun.star.lang import XServiceInfo
    from com.sun.star.task import XJobExecutor
except ImportError:
    # If imported outside LibreOffice runtime
    uno = None
    unohelper = None
    XJobExecutor = object
    XServiceInfo = object

from src.controller.ai_controller import AIController
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.utils.logging import get_logger

logger = get_logger("ai_writer.addon")


class AiAddon(unohelper.Base if unohelper else object, XJobExecutor, XServiceInfo):
    """UNO component implementing menu and toolbar actions in LibreOffice Writer."""

    IMPLEMENTATION_NAME = "org.libreoffice.ai.assistant.AiAddon"
    SERVICES = ("com.sun.star.task.Job",)

    def __init__(self, ctx):
        self.ctx = ctx
        self.controller = AIController()

    def trigger(self, args: str) -> None:
        """Invoked when user clicks menu or toolbar items in LibreOffice."""
        logger.info(f"Addon action triggered with args: {args}")
        try:
            desktop = self.ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.frame.Desktop", self.ctx
            )
            model = desktop.getCurrentComponent()

            if not model or not hasattr(model, "supportsService"):
                logger.warning("No active document found.")
                return

            if not model.supportsService("com.sun.star.text.TextDocument"):
                logger.warning("Active document is not a LibreOffice Writer document.")
                return

            # Convert to domain document
            doc = UNODocumentAdapter.to_domain_document(model)
            if not doc:
                logger.error("Failed to parse active Writer document.")
                return

            if "analyze" in args:
                result = self.controller.analyze(doc)
                logger.info(f"Analysis complete. Score: {result.qualityScore.overallScore:.1f}")

                # Launch interactive assistant dialog
                try:
                    from src.dashboard.quality_dashboard import InteractiveDashboardWindow
                    import threading
                    t = threading.Thread(
                        target=lambda: InteractiveDashboardWindow(self.controller, doc).launch(),
                        daemon=True,
                    )
                    t.start()
                except Exception as ui_err:
                    logger.warning(f"Could not open GUI window: {ui_err}")

            elif "report" in args:
                result = self.controller.analyze(doc)
                report = self.controller.generateReport(result)
                export_path = report.export(format="markdown")
                logger.info(f"Report exported to: {export_path}")

        except Exception as e:
            logger.error(f"Error handling addon trigger: {e}", exc_info=True)

    def getImplementationName(self) -> str:
        return self.IMPLEMENTATION_NAME

    def supportsService(self, service_name: str) -> bool:
        return service_name in self.SERVICES

    def getSupportedServiceNames(self) -> tuple:
        return self.SERVICES


if unohelper:
    g_ImplementationHelper = unohelper.ImplementationHelper()
    g_ImplementationHelper.addImplementation(
        AiAddon,
        AiAddon.IMPLEMENTATION_NAME,
        AiAddon.SERVICES,
    )
