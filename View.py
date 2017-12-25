import sys

from PyQt5.QtWidgets import QScrollArea

from Debugger import Debugger
import threading
from PyQt5.QtCore import QBasicTimer, Qt
from PyQt5.QtWidgets import QMainWindow, QSplitter, QInputDialog, QFrame,\
    QAction, QApplication, QFileDialog, QTextEdit, QLabel
from PyQt5.QtGui import QPainter, QImage, QIcon


class BPMap(QFrame):
    def __init__(self):
        super().__init__()
        self.line_count = 40
        self.breakpoints = {}
        self.bp_image = QImage()
        self.bp_image.load("breakpoint.png")
        self.point_image = QImage()
        self.point_image.load("point1.png")
        self.last_line = 1

    def mouse_press_event(self):
        self.debugger.add_breakpoint(25)

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.translate(13, 20)
        painter.drawText(0, 0, str(1))
        painter.translate(0, 21)
        for i in range(2, self.line_count):
            if i == self.last_line:
                painter.drawImage(5 - self.point_image.width() / 2,
                                  -3 - self.point_image.height() / 2, self.point_image)
            elif i in self.breakpoints:
                painter.drawImage(5 - self.bp_image.width() / 2, -3 - self.bp_image.height() / 2, self.bp_image)
            else:
                painter.drawText(0, 0, str(i))
            painter.translate(0, 21)
        painter.end()


class View(QMainWindow):
    def __init__(self):
        super().__init__()
        self.debugger = Debugger()
        self.file_name = None
        self.setWindowTitle('Python Debugger')
        self.textEdit = QTextEdit()
        scroll_bar = QScrollArea(self)
        self.textEdit.setFrameShape(QFrame.StyledPanel)

        self.console = QLabel()
        self.console.setWordWrap(True)
        self.console.setFixedSize(400, 1200)

        self.breakpoints_map = BPMap()
        self.breakpoints_map.setFixedSize(25, 1200)
        self.breakpoints_map.setFrameShape(QFrame.StyledPanel)
        self.console.setFrameShape(QFrame.StyledPanel)

        scroll_bar.setWidget(self.breakpoints_map)
        self.textEdit.setVerticalScrollBar(scroll_bar.verticalScrollBar())

        self.breakpoint_image = QImage()

        self.breakpoint_image.load('breakpoint.png')

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.breakpoints_map)
        self.splitter.addWidget(self.textEdit)
        self.splitter.addWidget(self.console)
        self.setCentralWidget(self.splitter)
        self.file = None

        exit_action = QAction(QIcon('exit.png'), 'Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.exit)

        open_file_action = QAction(QIcon('open.png'), 'Open file', self)
        open_file_action.setShortcut('Ctrl+O')
        open_file_action.setStatusTip('Open python file')
        open_file_action.triggered.connect(self.show_dialog)

        set_bp_action = QAction(QIcon('breakpoint.png'), 'set_bp', self)
        set_bp_action.setShortcut('Ctrl+R')
        set_bp_action.setStatusTip(r'install\uninstall bp')
        set_bp_action.triggered.connect(self.show_bp_dialog)

        start_debug = QAction(QIcon('de bug.png'), 'Debug', self)
        start_debug.setShortcut('Ctrl+S')
        start_debug.setStatusTip('Start debugging')
        start_debug.triggered.connect(self.start_debugging)

        continue_debug = QAction(QIcon('debug.png'), 'Continue', self)
        continue_debug.setShortcut('Ctrl+D')
        continue_debug.setStatusTip('Continue debugging')
        continue_debug.triggered.connect(self.continue_debugging)

        break_action = QAction(QIcon('open.png'), 'Stop Debug', self)
        break_action.setShortcut('Ctrl+B')
        break_action.setStatusTip('Stop debug process')

        menu_Bar = self.menuBar()
        self.menu = menu_Bar.addMenu('Menu')
        self.menu.addAction(exit_action)
        self.menu.addAction(open_file_action)
        self.menu.addAction(set_bp_action)
        self.menu.addAction(start_debug)
        self.menu.addAction(continue_debug)

        self.timer = QBasicTimer()
        self.timer.start(20, self)
        self.showFullScreen()

    def show_dialog(self):
        self.file_name, ok = QFileDialog.getOpenFileName(self, 'Open file', '/home')
        if not ok:
            return
        self.file = open(self.file_name, 'r')
        with self.file:
            self.text = self.file.read()
            self.textEdit.setText(self.text)
            self.textEdit.selectAll()
            self.textEdit.setAlignment(Qt.AlignLeft)
            self.textEdit.setFontPointSize(13)
            self.breakpoints_map.line_count =  self.text.count('\n') + 5

    def start_debugging(self):
        if self.file is None:
            return
        self.wait_event = threading.Event()
        self.print_event = threading.Event()
        self.text = self.textEdit.toPlainText()
        self.breakpoints_map.line_count = self.text.count('\n') + 5
        self.debug = threading.Thread(target=self.debugger.open,
                                      args=(self.text,
                                            self.file_name, self.wait_event,
                                            self.print_event))
        self.console_update = threading.Thread(target=self.update_console)
        self.debug.start()
        self.console_update.start()
        self.wait_event.set()

    def update_console(self):
        if not self.debug.isAlive:
            self.console.setText('')
        while self.debug.isAlive:
            self.print_event.wait()
            self.print_event.clear()
            result = 'Line Number:   {}\n'.format(self.debugger.last_line)
            self.breakpoints_map.last_line = self.debugger.last_line
            for name in self.debugger.watch.keys():
                result += name + '\n'
                for value in self.debugger.watch[name]:
                    result += '\t' + value + '\n'
            result += '\n\nCall Stack:\n'
            for function in self.debugger.call_stack:
                result += '\t'+ function + '\n'
            self.console.setText(result)

    def continue_debugging(self):
        self.wait_event.set()
        self.print_event.clear()

    def show_bp_dialog(self):
        if self.file_name is None:
            return
        number, ok = QInputDialog.getText(self, 'install breakpoint', 'Select line number')
        if ok:
            self.debugger.set_breakpoint(int(number))
            self.breakpoints_map.breakpoints = self.debugger.breakpoints

    def exit(self):
        if self.file is not None:
            self.file.close()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F2:
            self.debugger.step_into = True
            self.continue_debugging()
        if event.key() == Qt.Key_Escape:
            if self.file_name is not None:
                self.file.close()
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    debugger = View()
    sys.exit(app.exec_())
