import sys
from Debugger import Debugger
import threading
from PyQt5.QtCore import QBasicTimer, Qt
from PyQt5.QtWidgets import QMainWindow, QWidget,QSplitter,QInputDialog, QFrame, QApplication, QPushButton,\
    QAction, qApp, QApplication, QFileDialog, QTextEdit, QHBoxLayout,QLabel
from PyQt5.QtGui import QPainter, QImage, QColor, \
    QFont, QMouseEvent, QTransform, QBitmap, QCursor, QPixmap, QIcon, QKeyEvent


class BPMap(QFrame):
    def __init__(self):
        super().__init__()


    def mouse_press_event(self):
        self.debugger.add_breakpoint(25)


class View(QMainWindow):

    def __init__(self):
        super().__init__()
        self.debugger = Debugger()
        self.file_name = None
        self.setWindowTitle('Python Debugger')

        self.textEdit = QTextEdit()
        self.textEdit.setFrameShape(QFrame.StyledPanel)

        self.console = QLabel()
        self.console.setWordWrap(True)
        self.console.setFixedSize(400,1200)


        self.breakpoints_map = BPMap()
        self.breakpoints_map.setFixedSize(200, 1200)
        self.breakpoints_map.setFrameShape(QFrame.StyledPanel)
        self.console.setFrameShape(QFrame.StyledPanel)

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

        set_bp_action = QAction(QIcon('breakpoint.png'),'set_bp',self)
        set_bp_action.setShortcut('Space')
        set_bp_action.setStatusTip(r'install\uninstall bp')
        set_bp_action.triggered.connect(self.show_bp_dialog)

        start_debug = QAction(QIcon('debug.png'),'Debug',self)
        start_debug.setShortcut('Ctrl+S')
        start_debug.setStatusTip('Start debugging')
        start_debug.triggered.connect(self.start_debugging)

        continue_debug = QAction(QIcon('debug.png'), 'Continue', self)
        continue_debug.setShortcut('Ctrl+D')
        continue_debug.setStatusTip('Continue debugging')
        continue_debug.triggered.connect(self.continue_debugging)

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
            self.textEdit.setAlignment(Qt.AlignHCenter)
            self.textEdit.setFontPointSize(13)
            self.debugger.open(self.text, self.file_name)

    def start_debugging(self):
        if self.file is None:
            return
        self.wait_event = threading.Event()
        self.print_event = threading.Event()
        debug = threading.Thread(target=self.debugger.debug,args=(self.wait_event,self.print_event))
        console_update = threading.Thread(target=self.update_console)
        debug.start()
        console_update.start()
        self.wait_event.set()

    def update_console(self):
        while self.debugger.is_running:

            result = ''
            self.print_event.wait()
            self.print_event.clear()
            for name in self.debugger.watch.keys():
                result += name + self.debugger.watch[name] + '\n'
            self.console.setText(result)

    def continue_debugging(self):
        self.wait_event.set()
        self.print_event.clear()

    def show_bp_dialog(self):
        if self.file_name is None:
            return
        number, ok = QInputDialog.getText(self,'install breakpoint','Select line number')
        if ok:
            self.debugger.set_breakpoint(int(number))

    def mousePressEvent(self, QMouseEvent):
        pass

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        for breakpoint in self.debugger.breakpoints:
            pass
            #matrix = painter.transform()
            #painter.translate(50, breakpoint.Y)
            #painter.drawImage(-self.breakpoint_image.width()/2, -self.breakpoint_image.height()/2,
                    #          self.breakpoint_image)
            #painter.setTransform(matrix)
        painter.end()


    def exit(self):
        if self.file is not None:
            self.file.close()
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.file_name is not None:
                self.file.close()
            self.close()



if __name__ == '__main__':
    app = QApplication(sys.argv)
    debugger = View()
    sys.exit(app.exec_())



