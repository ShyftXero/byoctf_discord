from time import sleep, time
import math

from dashing import *

if __name__ == '__main__':

    ui = HSplit(
        VSplit(
            Text("text"), 
            Log(title='Logs')
        ),
        title="Dashboard"
    )

    ui.display()
    