import os
import json

output_folder = "output_blocks"
final_file = "investigadores_detalle_final.json"

data = []
for filename in sorted(os.listdir(output_folder)):
    if filename.endswith(".json"):
        with open(os.path.join(output_folder, filename), "r", encoding="utf-8") as file:
            data.extend(json.load(file))

with open(final_file, "w", encoding="utf-8") as file:
    json.dump(data, file, ensure_ascii=False, indent=4)

print(f"Datos combinados guardados en {final_file}")
