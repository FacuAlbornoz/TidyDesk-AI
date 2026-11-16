import re
from typing import List, Dict, Any
from app.ai.base import AIProvider
from app.schemas.organize import PlanItem

class SmartRulesProvider(AIProvider):
    """Clasificador inteligente heurístico sin dependencias externas.
    Sirve como motor local instantáneo o fallback de seguridad.
    """

    async def is_available(self) -> bool:
        return True

    def _classify_file(self, name: str, ext: str) -> tuple[str, str]:
        """Determina la carpeta y razón basándose en extensión y patrones de nombre."""
        from app.core.rules_manager import match_custom_rule

        # ==========================================
        # 0. PRIORIDAD MÁXIMA: REGLAS PERSONALIZADAS DEL USUARIO
        # ==========================================
        custom_match = match_custom_rule(name, ext)
        if custom_match:
            return custom_match

        ext = ext.lower()
        name_lower = name.lower()

        # ==========================================
        # 1. ACCESOS DIRECTOS Y APLICACIONES (.LNK / .URL)
        # ==========================================
        if ext in [".lnk", ".url"]:
            # Videojuegos y Launchers
            if any(w in name_lower for w in [
                "steam", "epic", "riot", "league of legends", "lol", "valorant", 
                "minecraft", "cs2", "counter", "gta", "rockstar", "battle.net", 
                "blizzard", "ea app", "origin", "ubisoft", "roblox", "fortnite",
                "genshin", "dota", "tibia", "game", "juego"
            ]):
                return "Juegos", "Acceso directo a videojuego o plataforma de juegos"

            # Desarrollo de Software y Código
            if any(w in name_lower for w in [
                "code", "visual studio", "vscode", "pycharm", "intellij", "git", 
                "github", "dbeaver", "postman", "terminal", "powershell", "cmd", 
                "docker", "android studio", "sublime", "insomnia", "wamp", "xampp"
            ]):
                return "Desarrollo y Programacion", "Herramienta o entorno de desarrollo de software"

            # Diseño Gráfico y Creatividad
            if any(w in name_lower for w in [
                "photoshop", "illustrator", "premiere", "after effects", "lightroom",
                "figma", "canva", "blender", "corel", "inkscape", "gimp", "davinci"
            ]):
                return "Diseno y Creatividad", "Software de diseño, edición multimedia o 3D"

            # Navegadores Web
            if any(w in name_lower for w in [
                "chrome", "firefox", "brave", "edge", "opera", "tor browser", "vivaldi"
            ]):
                return "Navegadores Web", "Acceso directo a navegador de Internet"

            # Multimedia y Streaming
            if any(w in name_lower for w in [
                "spotify", "vlc", "obs", "streamlabs", "netflix", "discord", "whatsapp", "telegram"
            ]):
                return "Multimedia y Comunicacion", "Reproductor multimedia o app de comunicación"

            # Ofimática y Productividad
            if any(w in name_lower for w in [
                "word", "excel", "powerpoint", "notion", "trello", "teams", "zoom", "slack"
            ]):
                return "Productividad y Oficina", "Herramienta de oficina o gestión de tareas"

            return "Accesos Directos", "Acceso directo a aplicación o carpeta"

        # ==========================================
        # 2. DOCUMENTOS DE ESTUDIO / FACULTAD / ITEC
        # ==========================================
        if any(w in name_lower for w in ["tp", "trabajo", "practico", "parcial", "final", "apunte", "clase", "itec", "teoria", "seminario"]):
            return "Facultad/Estudio", "Detectado patrón de estudio, trabajo práctico o materia"
        if any(w in name_lower for w in ["programacion", "backend", "frontend", "codigo", "sql", "python", "fastapi"]):
            return "Facultad/Programacion", "Relacionado con desarrollo de software y programación"

        # ==========================================
        # 3. FINANZAS Y FACTURACIÓN
        # ==========================================
        if any(w in name_lower for w in ["factura", "recibo", "comprobante", "ticket", "pago", "banco", "afip", "resumen"]):
            return "Finanzas y Comprobantes", "Documento de pago, comprobante o factura fiscal"

        # ==========================================
        # 4. DOCUMENTOS POR EXTENSIÓN
        # ==========================================
        if ext in [".pdf", ".docx", ".doc", ".odt"]:
            return "Documentos/Textos", f"Archivo de lectura o procesamiento de texto ({ext})"
        if ext in [".xlsx", ".xls", ".csv"]:
            return "Documentos/Planillas", f"Planilla de cálculo o datos tabulares ({ext})"
        if ext in [".pptx", ".ppt"]:
            return "Documentos/Presentaciones", f"Diapositivas y presentaciones ({ext})"

        # ==========================================
        # 5. IMÁGENES Y DISEÑO
        # ==========================================
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]:
            if any(w in name_lower for w in ["screenshot", "captura", "screen"]):
                return "Imagenes/Capturas", "Captura de pantalla detectada"
            return "Imagenes", f"Archivo gráfico o fotografía ({ext})"
        if ext in [".psd", ".ai", ".fig"]:
            return "Diseno Grafico", f"Proyecto de diseño ({ext})"

        # ==========================================
        # 6. INSTALADORES Y EJECUTABLES
        # ==========================================
        if ext in [".exe", ".msi"]:
            return "Instaladores de Programas", "Paquete ejecutable o instalador de software"

        # ==========================================
        # 7. ARCHIVOS COMPRIMIDOS
        # ==========================================
        if ext in [".zip", ".rar", ".7z", ".tar", ".gz"]:
            return "Comprimidos y Backups", f"Archivo comprimido de almacenamiento ({ext})"

        # ==========================================
        # 8. MULTIMEDIA (AUDIO Y VIDEO)
        # ==========================================
        if ext in [".mp4", ".mkv", ".mov", ".avi", ".webm"]:
            return "Videos", f"Archivo multimedia de video ({ext})"
        if ext in [".mp3", ".wav", ".flac", ".ogg", ".aac"]:
            return "Musica y Audios", f"Archivo de audio ({ext})"

        # ==========================================
        # 9. CÓDIGO FUENTE
        # ==========================================
        if ext in [".py", ".js", ".ts", ".html", ".css", ".json", ".sql"]:
            return "Codigo y Scripts", f"Archivo de código fuente ({ext})"

        return "Varios", "Clasificación general por extensión"

    async def generate_plan(
        self,
        files: List[Dict[str, Any]],
        model: str | None = None,
        custom_instructions: str | None = None
    ) -> List[PlanItem]:
        plan_items: List[PlanItem] = []

        for f in files:
            name = f.get("name", "")
            ext = f.get("extension", "")
            folder, reason = self._classify_file(name, ext)

            plan_items.append(
                PlanItem(
                    file_id=f.get("id", ""),
                    original_path=f.get("path", ""),
                    original_name=name,
                    suggested_folder=folder,
                    suggested_name=name,
                    reason=reason,
                    selected=True,
                )
            )

        return plan_items
