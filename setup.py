from distutils.core import setup
import py2exe
setup(
    # Change console to window or windows?
    console = [
        {
            "script": "laziitv.pyw",
            "icon_resources": [(0, "D:\Andrew\Python Workspace\LaziiTV\Source\icon_big.ico")]
        }
    ],
)
