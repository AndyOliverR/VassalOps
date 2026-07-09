import os

class GMDocumentReader:
    def __init__(self, doc_dir=r"C:\VassalOps\storage\documents"):
        self.doc_dir = doc_dir
        if not os.path.exists(doc_dir):
            os.makedirs(doc_dir)

    def read_all_documents(self) -> str:
        """Scan documents directory and join text outputs into a structural context block."""
        if not os.path.exists(self.doc_dir):
            return ""
            
        compiled_context = ""
        files = [f for f in os.listdir(self.doc_dir) if f.endswith(('.txt', '.md', '.json'))]
        
        if not files:
            return ""
            
        compiled_context += "\n=== EXTRACTED LOCAL KNOWLEDGE BASE ===\n"
        for file_name in files:
            file_path = os.path.join(self.doc_dir, file_name)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        compiled_context += f"[FILE: {file_name}]\n{content}\n\n"
            except Exception as e:
                compiled_context += f"[FILE ERROR: {file_name}] Could not parse: {str(e)}\n\n"
                
        compiled_context += "=======================================\n"
        return compiled_context

