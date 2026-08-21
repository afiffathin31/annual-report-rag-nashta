import os
import config
from llama_parse import LlamaParse


parser = LlamaParse(
   api_key=os.environ.get("LLAMA_API_KEY"),
   extract_charts=True,
   auto_mode=True,
   auto_mode_trigger_on_image_in_page=True,
   auto_mode_trigger_on_table_in_page=True,
   result_type="markdown",  # "markdown" and "text" are available
   )

file_name = "docs/AR PDSB 2025.pdf"
extra_info = {"file_name": file_name}

with open(file_name, "rb") as f:
   # must provide extra_info with file_name key with passing file object
   documents = parser.load_data(f, extra_info=extra_info)

# Write the output to a file
with open("output.md", "w", encoding="utf-8") as f:
   for doc in documents:
       f.write(doc.text)