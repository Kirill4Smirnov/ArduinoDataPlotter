import glob
import sys
import tkinter as tk
import matplotlib
import serial

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
        self.title('Tkinter Matplotlib Demo')

        data = {
            'Python': 11.27,
            'C': 11.16,
            'Java': 10.46,
            'C++': 7.5,
            'C#': 5.26
        }

        self.display_plot(data)
        self.display_buttons()

    def display_plot(self, data):
        languages = data.keys()
        popularity = data.values()

        # create a figure
        figure = Figure(figsize=(6, 4), dpi=100)

        # create FigureCanvasTkAgg object
        figure_canvas = FigureCanvasTkAgg(figure, self)

        # create the toolbar
        NavigationToolbar2Tk(figure_canvas, self)

        # create axes
        axes = figure.add_subplot()

        # create the barchart
        axes.bar(languages, popularity)
        axes.set_title('Top 5 Programming Languages')
        axes.set_ylabel('Popularity')

        figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def display_buttons(self):
        self.variable = tk.StringVar(self)
        self.variable.set(None)  # default value

        ports = self.trans.list_available_serial_ports()

        w = tk.OptionMenu(self, self.variable, ports)
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
            text="Print variable",
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

    def print_variable(self):
        print(self.variable.get())


    def establish_connection(self):
        if self.variable.get() != None:
            self.trans.connect(self.variable.get())

    def start_plotting(self):
        pass


class ArduinoTransceiver:
    def connect(self, port):
        try:
            self.realport = serial.Serial(port=port)
            print(f"Real port name is: {self.realport}")
        except Exception as e:
            print(e)

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


if __name__ == '__main__':

    app = App()
    app.mainloop()
