from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Optional

from aleya.aleya import Aleya


@dataclass
class FlowStepLog:
    id: str
    status_flowelt: str
    msg_flowelt: str
    extra: Dict[str, Any] = field(default_factory=dict)


class Tiferet(Aleya):
    """
    Tiferet: Agente de automatización con IA para ejecutar flujos definidos en Sheets/JSON.

    Responsabilidades iniciales:
    - load_flow: cargar definiciones desde JSON o Google Sheets.
    - run_flow: invocar Shekina para ejecutar el flujo (dry-run o execute).
    - log_step: registrar status_flowelt y msg_flowelt por cada paso.
    - suggest_remediation: generar hojas flowelt__daath_std_cols/__std_vlrs cuando falten
      sinónimos/valores y devolver instrucciones.

    Nota: Implementación mínima (esqueleto). Integraremos Mirror.BackendGSuite y formateadores
    en épicas siguientes.
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()
        self.set_context(context or {})
        self.logs: List[FlowStepLog] = []

    def load_flow(self, source: str, kind: str = "json", **kwargs) -> Dict[str, Any]:
        """
        Carga un flujo desde:
        - kind=json: ruta a archivo JSON ya generado desde Sheets.
        - kind=gsheet: especificación de Sheet (spreadsheet_id, range o named ranges).

        Devuelve un dict con la definición de flujo (process_table o equivalente).
        """
        if kind == "json":
            import json, os
            if not os.path.exists(source):
                raise FileNotFoundError(f"Flow JSON not found: {source}")
            with open(source, "r", encoding="utf-8") as f:
                return json.load(f)
        elif kind == "gsheet":
            # Placeholder: se conectará con Mirror.BackendGSuite en épicas siguientes
            raise NotImplementedError("load_flow from gsheet pending BackendGSuite integration")
        else:
            raise ValueError(f"Unknown kind: {kind}")

    def run_flow(self, flow_def: Dict[str, Any], mode: str = "dry-run") -> Dict[str, Any]:
        """
        Ejecuta/valida un flujo documental/definiciones.
        - mode=dry-run: no persiste, solo planifica/valida.
        - mode=execute: ejecuta acciones documentales (p. ej., crear hojas de remediación)
        """
        try:
            self.log_step("s0", "Ok", "Inicio ejecución del flujo")

            # Aquí Tiferet no orquesta ETL (eso es Shekina). Tiferet opera sobre
            # definiciones/documentación y puede disparar utilidades de Aleya/Mirror.
            result = {"status": "dry-run" if mode == "dry-run" else "executed", "engine": "Tiferet"}

            self.log_step("s1", "Ok", f"Flujo ejecutado en modo: {mode}")
            return {"ok": True, "result": result, "logs": [l.__dict__ for l in self.logs]}
        except Exception as ex:  # noqa: BLE001
            self.log_step("s2", "Error", str(ex))
            return {"ok": False, "error": str(ex), "logs": [l.__dict__ for l in self.logs]}

    def log_step(self, step_id: str, status: str, message: str, **extra: Any) -> None:
        self.logs.append(FlowStepLog(id=step_id, status_flowelt=status, msg_flowelt=message, extra=extra))

    def suggest_remediation(self, kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera sugerencias de remediación:
        - kind=std_cols: crear hoja flowelt__daath_std_cols__{timestamp}
        - kind=std_vlrs: crear hoja flowelt__daath_std_vlrs__{timestamp}
        Devuelve instrucciones/plantilla; la creación efectiva se hará con BackendGSuite.
        """
        import datetime as _dt

        timestamp = _dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        sheet_name = f"flowelt__daath_{'std_cols' if kind=='std_cols' else 'std_vlrs'}__{timestamp}"
        template = {
            "sheet": sheet_name,
            "columns": ["context-init", "#enf_table#", "flow", "#enf_table#", "input_data_0", "colFlag"],
            "notes": "Complete los sinónimos/estándares y reejecute el flujo."
        }
        self.log_step("s_remediate", "Ok", f"Sugerida hoja {sheet_name}", kind=kind)
        return template

    # --- Integración documental mínima ---
    def sync_md_to_gdoc_tab(self, document_id: str, tab_name: str, md_path: str) -> Dict[str, Any]:
        """Sincroniza un archivo MD a una Tab de GDoc (requiere BackendGSuite y front gdoc)."""
        try:
            from mirror.backend_gsuite import BackendGSuite
            from alchemist import gdoc_front

            with open(md_path, "r", encoding="utf-8") as f:
                md_text = f.read()

            cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            backend = BackendGSuite(credentials_path=cred)
            gdoc_front.upsert_tab_from_md(backend, document_id, tab_name, md_text)
            self.log_step("s_gdoc_sync", "Ok", f"Sync MD→GDoc tab '{tab_name}'")
            return {"ok": True}
        except Exception as ex:  # noqa: BLE001
            self.log_step("s_gdoc_sync", "Error", str(ex))
            return {"ok": False, "error": str(ex)}

