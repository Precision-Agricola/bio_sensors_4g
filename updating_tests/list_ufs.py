# list_ufs.py
from pico_lte.core import PicoLTE
from pico_lte.utils.status import Status

lte  = PicoLTE()
files = lte.file.get_file_list("*")

if files["status"] == Status.SUCCESS:
    print("Archivos en la UFS:")
    for line in files["response"]:
        if line.startswith("+QFLST:"):
            # +QFLST: "UFS:foo.bin",1234
            print("  ", line.split(":")[1].strip())
else:
    print("Error:", files["response"])
