from distutils.core import setup
import py2exe

setup(
    # Change console to window or windows?
    windows=[
        {
            "script": "laziitv.pyw",
            "icon_resources": [(0, "icon_big.ico")]
        }
    ],
)
