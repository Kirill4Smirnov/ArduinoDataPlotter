import glob
import re
import sys
import tkinter as tk
import matplotlib.pyplot
import serial
import threading
import time
import numpy as np
from matplotlib.animation import FuncAnimation

matplotlib.use('TkAgg')

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.trans = ArduinoTransceiver()

        self.variable = tk.StringVar(self)
        self.title('Chromatograph plotter')

        self.display_plot()
        self.display_buttons()

    def display_buttons(self):
        self.variable = tk.StringVar(self)
        self.variable.set(None)  # default value

        ports = self.trans.list_available_serial_ports()

        w = tk.OptionMenu(self, self.variable, None, *ports)
        w.pack()

        button_frame = tk.Frame(self)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        btn1 = tk.Button(
            button_frame,
            text="Establish a connection",
            command=self.establish_connection
        )
        btn1.grid(row=0, column=0, sticky=tk.W + tk.E)

        btn2 = tk.Button(
            button_frame,
            text="Read and print buffer",
            command=self.print_variable
        )
        btn2.grid(row=0, column=1, sticky=tk.W + tk.E)
        button_frame.pack(fill=tk.X)

        btn3 = tk.Button(
            text="Quit",
            width=10,
            command=self.destroy
        )
        btn3.pack()

    def display_plot(self):
        figure = Figure(figsize=(6, 4), dpi=100)
        figure_canvas = FigureCanvasTkAgg(figure, self)
        NavigationToolbar2Tk(figure_canvas, self)
        self.axes = figure.add_subplot()

        # self.axes.plot(data.keys(), data.values())

        figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        anim = FuncAnimation(figure,
                             self.update_plot,
                             frames=20,
                             interval=50)

        anim.save(r'animation.gif', fps=10)
        matplotlib.pyplot.show()

    def print_variable(self):
        print(self.trans.read())

    def update_plot(self, i):
        # data = {1: 2, 2: 2, 3: 3, 4: 5}
        # self.axes.plot(data.keys(), data.values())

        pass

    def establish_connection(self):
        if self.variable.get() != None:
            self.trans.connect(self.variable.get())
        else:
            print("Your chosen port is None, please chose another")

    def start_plotting(self):
        pass


class ArduinoTransceiver:
    def __init__(self):
        self.i = 0
        self.data = np.array([])

    def connect(self, port):
        try:
            self.realport = serial.Serial(port=port)
            print(f"Real port name is: {self.realport}")
            self.line_reader = ReadLine(self.realport)

        except Exception as e:
            print(e)

    def read(self):
        buffer_size = self.realport.in_waiting
        val = self.realport.read(buffer_size).decode()
        raw_list = np.array(re.split(r'\r\n|\n\r', val))
        raw_list.
        print(raw_list)
        float_list = raw_list.astype(float)


        return float_list

    def read_quick(self):
        return self.line_reader.readline()

    def read_stub(self):
        pass

    @staticmethod
    def list_available_serial_ports():
        """ Lists serial port names

            :raises EnvironmentError:
                On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result


class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()
        self.s = s

    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i + 1]
            self.buf = self.buf[i + 1:]
            return r
        while True:
            i = max(1, min(2048, self.s.in_waiting))
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i + 1]
                self.buf[0:] = data[i + 1:]
                return r
            else:
                self.buf.extend(data)


if __name__ == '__main__':
    app = App()
    app.mainloop()
