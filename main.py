import glob
import re
import sys
import tkinter as tk
import matplotlib.pyplot
import serial
import threading
import time
import numpy as np

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

    def display_buttons(self) -> None:
        self.variable = tk.StringVar(self)
        self.variable.set('None')  # default value

        ports = self.trans.list_available_serial_ports()

        port_frame = tk.Frame(self)
        port_frame.columnconfigure(0, weight=1)
        port_frame.columnconfigure(1, weight=1)
        port_frame.columnconfigure(2, weight=1)

        port_option_menu = tk.OptionMenu(port_frame, self.variable, 'None', *ports)
        port_option_menu.grid(row=0, column=0)

        connect_btn = tk.Button(
            port_frame,
            text="Establish a connection",
            command=self.establish_connection
        )
        connect_btn.grid(row=0, column=1)

        read_btn = tk.Button(
            port_frame,
            text="Read and print buffer",
            command=self.print_variable
        )
        read_btn.grid(row=0, column=2)


        port_frame.pack()

        button_frame = tk.Frame(self)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)


        stop_plot_btn = tk.Button(
            button_frame,
            text="Stop plotting",
            command=self.stop_update_plot
        )
        stop_plot_btn.grid(row=0, column=1, sticky=tk.W + tk.E)

        start_plot_btn = tk.Button(
            button_frame,
            text="Start plotting",
            command=self.start_plotting
        )
        start_plot_btn.grid(row=0, column=0, sticky=tk.W + tk.E)

        clear_plot_btn = tk.Button(
            button_frame,
            text="Clear data",
            command=self.clear_data
        )
        clear_plot_btn.grid(row=1, column=0, sticky=tk.W + tk.E)
        #clear_plot_btn['state'] = tk.DISABLED

        button_frame.pack(fill=tk.X)

        quit_btn = tk.Button(
            text="Quit",
            command=self.destroy_and_end_plotting
        )
        quit_btn.pack()

    def display_plot(self) -> None:
        self.figure = Figure(figsize=(10, 4), dpi=100)
        self.figure_canvas = FigureCanvasTkAgg(self.figure, self)
        NavigationToolbar2Tk(self.figure_canvas, self)
        self.axes = self.figure.add_subplot()

        self.plot, = self.axes.plot([1, 2, 3, 4, 7], [-1, 3, -2, 1, 0])

        self.figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        matplotlib.pyplot.show()

    def print_variable(self) -> None:
        if self.trans.realport is None:
            print("Connection is not set up")
            return

        print(self.trans.read_str_by_str())

    def start_update_plot(self) -> None:
        if self.trans.realport is None:
            print("Connection is not set up")
            return

        self.plotting = True
        while self.plotting == True:
            data = self.trans.read_str_by_str()
            # print(data)
            self.plot.set_ydata(data)
            self.plot.set_xdata(np.arange(data.size))

            self.axes.set_xlim([0, data.size])
            self.axes.set_ylim([0, np.max(data)])

            self.figure_canvas.draw()
            self.figure_canvas.flush_events()
            # matplotlib.pyplot.show()
            time.sleep(0.05)

    def stop_update_plot(self) -> None:
        self.plotting = False

    def destroy_and_end_plotting(self) -> None:
        self.plotting = False
        if self.trans.realport is not None:
            self.trans.realport.close()
        self.destroy()

    def establish_connection(self) -> None:
        if self.variable.get() != 'None':
            self.trans.connect(self.variable.get())

            if self.trans.realport is not None:
                self.trans.clear_input() # a few first messages from Arduino often are spoiled
        else:
            print("Your chosen port is None, please chose another")

    def start_plotting(self) -> None:
        update_thread = threading.Thread(target=self.start_update_plot())
        update_thread.start()

    def clear_data(self) -> None:
        self.trans.data = np.array([])
        self.trans.clear_input()

    def enable_buttons(self):
        pass

class ArduinoTransceiver:
    def __init__(self):
        self.i = 0
        self.data = np.array([])
        self.realport = None

    def connect(self, port):
        try:
            self.realport = serial.Serial(port=port)
            print(f"Real port name is: {self.realport}")
            self.line_reader = ReadLine(self.realport)

        except Exception as e:
            print(e)

    def read_all_buffer(self):
        buffer_size = self.realport.in_waiting
        val = self.realport.read(buffer_size).decode()
        raw_list = np.array(re.split(r'\r\n|\n\r', val))
        raw_list = np.delete(raw_list,
                             -1)  # the last element always contains an artefact due to the line cutting off, so we need to remove it
        raw_list = raw_list[raw_list != '']
        float_list = raw_list.astype(float)

        self.data = np.append(self.data, float_list)
        return self.data.copy()

    def read_str_by_str(self):
        while self.realport.in_waiting > 10:
            try:
                val = self.line_reader.readline().decode()
                raw_list = np.array(re.split(r'\r\n|\n\r', val))
                raw_list = raw_list[raw_list != '']
                print(raw_list)
                if len(raw_list) > 0:
                    for i in range(len(raw_list)):
                        char_count = 0
                        for char in raw_list[i]:
                            if char == '.':
                                char_count += 1
                        if char_count >= 2:
                            raw_list = np.delete[raw_list, i]
                    float_list = raw_list.astype(float)

                    self.data = np.append(self.data, float_list)
            except(UnicodeDecodeError) as e:
                print(e)
                #buffer_size = self.realport.in_waiting
                #self.realport.read(buffer_size)
                self.realport.flush()
                continue


        return self.data.copy()

    def clear_input(self):
        buffer_size = self.realport.in_waiting
        self.realport.read(buffer_size)

        self.data = np.array([])

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
