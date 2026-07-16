import urllib.request
import json
import re
from ingestion.parser import GMInputParser
from ingestion.document_reader import GMDocumentReader
from network.scraper import GMNetworkScraper
from storage.db_manager import GMDatabaseManager
from actions.bridge import GMActionBridge

class GMAIEngine:
    def __init__(self, model_name="gpt-oss:120b-cloud", host="127.0.0.1", port=11434):
        self.model_name = model_name
        self.url = f"http://{host}:{port}/api/generate"
        self.parser = GMInputParser(max_chars=4000)
        self.doc_reader = GMDocumentReader()
        self.web_scraper = GMNetworkScraper()
        self.db = GMDatabaseManager()
        self.action_bridge = GMActionBridge()
        
        self.local_shortcuts = {
            "open config": ("notepad", "C:\\VassalOps\\config.json"),
            "open database": ("explorer", "C:\\VassalOps\\storage"),
            "open engine logs": ("notepad", "C:\\VassalOps\\storage\\gm_core.db")
        }

    def process_message(self, session_id: str, raw_payload: str):
        """Orchestrate parsing, shortcuts, compilation execution, macros, RAG, scraping, and fallback."""
        parsed = self.parser.parse_payload(raw_payload)
        if parsed["status"] != "CLEAN":
            yield f"[SYSTEM BLOCKED] {parsed.get('error', 'Malformed Input')}"
            return

        user_prompt = parsed["prompt"].strip()
        self.db.log_message(session_id, "bot_sitter", user_prompt)
        normalized_prompt = user_prompt.lower()
        
        # 1. Check for application shortcut triggers
        if normalized_prompt in self.local_shortcuts:
            app, arg = self.local_shortcuts[normalized_prompt]
            yield f"Acknowledged. Local system shortcut triggered. Launching {app} with argument '{arg}'..."
            action_result = self.action_bridge.execute_app(app, arg)
            self.db.log_action(session_id, app, f"Shortcut Launch: {action_result['status']} ({arg})")
            yield f"\n[SYSTEM STATUS] Execution result: {action_result['status']}"
            return

        # 2. Advanced Multi-File Compiler & Execution Layer
        # Syntax: compilesuite folder_dir | primary_script.py
        if normalized_prompt.startswith("compilesuite "):
            raw_arguments = user_prompt[13:].strip()
            if "|" in raw_arguments:
                suite_folder, execution_script = raw_arguments.split("|", 1)
                suite_folder = suite_folder.strip()
                execution_script = execution_script.strip()
                
                yield f"[SYSTEM] Accessing compiler pipeline. Initializing runtime suite: '{suite_folder}'...\n"
                result = self.action_bridge.compile_and_run_suite(suite_folder, execution_script)
                self.db.log_action(session_id, "compiler_io", f"{result['status']} (Folder: {suite_folder})")
                yield f"[SYSTEM STATUS] Execution result: {result['status']}"
                if "error" in result:
                    yield f" - Details: {result['error']}"
                return

        # 3. OS Macro Interceptor Layer
        if normalized_prompt.startswith("listfiles"):
            target_subfolder = user_prompt[9:].strip()
            yield f"[SYSTEM] Accessing localized macro layer. Scanning tree index...\n\n"
            result_tree = self.action_bridge.list_directory_contents(target_subfolder)
            yield result_tree
            return
            
        if normalized_prompt.startswith("killtask "):
            target_task = user_prompt[9:].strip()
            yield f"[SYSTEM] Accessing localized macro layer. Terminating task process: '{target_task}'...\n"
            kill_result = self.action_bridge.kill_whitelisted_process(target_task)
            self.db.log_action(session_id, "task_macro", f"{kill_result['status']} (Target: {target_task})")
            yield f"[SYSTEM STATUS] Execution result: {kill_result['status']}"
            return

        # 4. Automated File Writing & Appending Interceptor Layer
        if normalized_prompt.startswith("writefile ") or normalized_prompt.startswith("appendfile "):
            is_append = normalized_prompt.startswith("appendfile ")
            cmd_len = 11 if is_append else 10
            raw_arguments = user_prompt[cmd_len:].strip()
            if "|" in raw_arguments:
                file_path, content = raw_arguments.split("|", 1)
                file_path = file_path.strip()
                content = content.lstrip("\n\r")
                result = self.action_bridge.write_to_file(file_path, content, "a" if is_append else "w")
                self.db.log_action(session_id, "file_io", f"{result['status']} (File: {file_path})")
                yield f"[SYSTEM] Intercepted file manipulation command. Target path: '{file_path}'...\n"
                yield f"[SYSTEM STATUS] File execution result: {result['status']}"
                return

        # 5. Check for manual live web-scraping requests
        if user_prompt.lower().startswith("fetch "):
            target_url = user_prompt[6:].strip()
            if target_url.startswith(("http://", "https://")):
                yield f"[SYSTEM] Intercepted network scraping command. Querying target URL: '{target_url}'...\n\n"
                live_web_data = self.web_scraper.fetch_live_text(target_url)
                yield live_web_data
                yield "\n[SYSTEM] Network extraction complete. Live content ingested safely."
                return

        # 6. Check for local RAG document requests
        if any(keyword in normalized_prompt for keyword in ["document", "knowledge", "file", "budget"]):
            yield "[SYSTEM] Intercepted knowledge request. Querying local storage structures...\n\n"
            local_knowledge = self.doc_reader.read_all_documents()
            if not local_knowledge or "EXTRACTED" not in local_knowledge:
                yield "The local knowledge base folder is currently empty or unreadable."
            else:
                yield local_knowledge
                yield "\n[SYSTEM] Knowledge retrieval complete. Data processed 100% locally."
            return

        # 7. Fallback to conversation loop context
        history = self.db.get_session_history(session_id, limit=6)
        context_string = ""
        for turn in history[:-1]:
            context_string += f"{turn['role'].upper()}: {turn['content']}\n"
        context_string += f"USER: {user_prompt}\nASSISTANT:"

        payload = {"model": self.model_name, "prompt": context_string.strip(), "stream": True}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.url, data=data, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req) as response:
                for line in response:
                    if line:
                        try:
                            line_data = json.loads(line.decode('utf-8').strip())
                            yield line_data.get("response", "")
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            yield f"\n[PIPELINE EXCEPTION] Failed to connect to server: {e}"




