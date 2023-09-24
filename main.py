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
        self.plotting = False
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

        connect_btn = tk.Button(
            button_frame,
            text="Establish a connection",
            command=self.establish_connection
        )
        connect_btn.grid(row=0, column=0, sticky=tk.W + tk.E)

        read_btn = tk.Button(
            button_frame,
            text="Read and print buffer",
            command=self.print_variable
        )
        read_btn.grid(row=0, column=1, sticky=tk.W + tk.E)

        stop_plot_btn = tk.Button(
            button_frame,
            text="Stop plotting",
            width=10,
            command=self.stop_update_plot
        )
        stop_plot_btn.grid(row=1, column=1, sticky=tk.W+tk.E)

        start_plot_btn = tk.Button(
            button_frame,
            text="Start plotting",
            command=self.start_plotting
        )
        start_plot_btn.grid(row=1, column=0, sticky=tk.W + tk.E)

        button_frame.pack(fill=tk.X)

        quit_btn = tk.Button(
            text="Quit",
            width=10,
            command=self.destroy_and_end_plotting
        )
        quit_btn.pack()

    def display_plot(self):
        self.figure = Figure(figsize=(10, 4), dpi=100)
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self)
        NavigationToolbar2Tk(self.figure_canvas, self)
        self.axes = self.figure.add_subplot()

        self.plot,  = self.axes.plot([1, 2, 3, 4, 7], [-1, 3, -2, 1, 0])

        self.figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        matplotlib.pyplot.show()

    def print_variable(self):
        print(self.trans.read())

    def start_update_plot(self):
        self.plotting = True
        while self.plotting == True:
            data = self.trans.read()
            #print(data)
            self.plot.set_ydata(data)
            self.plot.set_xdata(np.arange(data.size))

            self.axes.set_xlim([0, data.size])
            self.axes.set_ylim([0, None])

            self.figure_canvas.draw()
            self.figure_canvas.flush_events()
            #matplotlib.pyplot.show()
            time.sleep(0.05)

    def stop_update_plot(self) -> None:
        self.plotting = False

    def destroy_and_end_plotting(self):
        self.plotting = False
        self.destroy()

    def establish_connection(self):
        if self.variable.get() != None:
            self.trans.connect(self.variable.get())
        else:
            print("Your chosen port is None, please chose another")

    def start_plotting(self):
        update_thread = threading.Thread(target=self.start_update_plot())
        update_thread.start()



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
        raw_list = np.delete(raw_list, -1) # the last element always contains an artefact due to the line cutting off, so we need to remove it
        raw_list = raw_list[raw_list != '']
        float_list = raw_list.astype(float)

        self.data = np.append(self.data, float_list)
        return self.data.copy()

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
            data = self.s. read(i)
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
