import sys
import os
import openai

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QLineEdit,
    QMessageBox,
    QTabWidget,
    QPlainTextEdit
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter
from PyQt5.QtWebEngineWidgets import QWebEngineView


###############################################################################
# 1. Text Generation (OpenAI) Setup
###############################################################################

def create_text_generation_pipeline(api_key, model_name="gpt-3.5-turbo"):
    """
    Creates a function that calls the OpenAI Chat API,
    using the specified GPT model by default.
    """
    if not api_key:
        raise ValueError(
            "No API key provided. Please set the OPENAI_API_KEY environment variable."
        )

    openai.api_key = api_key

    def generator(prompt, max_tokens=50, temperature=1.0):
        """
        Generate text using the OpenAI ChatCompletion API with adjusted parameters
        to simulate a less capable model.
        """
        try:
            response = openai.ChatCompletion.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a simple assistant that provides brief and straightforward answers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return ""

    return generator


###############################################################################
# 2. Syntax Highlighter for the Code Editor
###############################################################################

class PythonHighlighter(QSyntaxHighlighter):
    """
    A basic syntax highlighter for Python code. You can expand the patterns
    and formatting rules to match more advanced syntax.
    """
    def __init__(self, parent=None):
        super(PythonHighlighter, self).__init__(parent)

        # Define formats
        self.keywordFormat = QTextCharFormat()
        self.keywordFormat.setForeground(QColor("#c678dd"))  # Purple
        self.keywordFormat.setFontWeight(QFont.Bold)

        self.stringFormat = QTextCharFormat()
        self.stringFormat.setForeground(QColor("#98c379"))  # Green

        self.commentFormat = QTextCharFormat()
        self.commentFormat.setForeground(QColor("#5c6370"))  # Gray

        # Define regex patterns
        self.keywords = [
            r"\bdef\b", r"\bclass\b", r"\bimport\b", r"\bfrom\b", r"\bas\b",
            r"\bif\b", r"\belif\b", r"\belse\b", r"\bwhile\b", r"\bfor\b",
            r"\bin\b", r"\breturn\b", r"\bwith\b", r"\btry\b", r"\bexcept\b",
            r"\braise\b", r"\bpass\b", r"\bNone\b", r"\bTrue\b", r"\bFalse\b"
        ]
        self.keywordPatterns = [r"{}".format(kw) for kw in self.keywords]

        self.stringPatterns = [
            r"\".*?\"",   # Double quotes
            r"\'.*?\'"    # Single quotes
        ]

        # Comment pattern
        self.commentPatterns = [
            r"#.*",  # Single line
        ]

    def highlightBlock(self, text):
        import re
        # Highlight keywords
        for pattern in self.keywordPatterns:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.keywordFormat)

        # Highlight strings
        for pattern in self.stringPatterns:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.stringFormat)

        # Highlight comments
        for pattern in self.commentPatterns:
            expression = re.compile(pattern)
            for match in expression.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, self.commentFormat)


###############################################################################
# 3. Main Application Window
###############################################################################

class MainWindow(QMainWindow):
    def __init__(self, api_key, model_name="gpt-3.5-turbo"):
        super().__init__()
        self.setWindowTitle("AI + Code Editor + Web Browser Demo (OpenAI ChatCompletion API)")
        self.resize(1000, 700)

        # 3.1 Create the Text Generation pipeline
        try:
            self.generator = create_text_generation_pipeline(
                api_key=api_key,
                model_name=model_name
            )
        except Exception as e:
            QMessageBox.critical(self, "Model Load Error", str(e))
            sys.exit(1)

        # 3.2 Create Tabs
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # Create the three main tabs
        self.tab_text_gen = self.create_text_gen_tab()
        self.tab_code_editor = self.create_code_editor_tab()
        self.tab_browser = self.create_browser_tab()

        self.tab_widget.addTab(self.tab_text_gen, "Text Generation")
        self.tab_widget.addTab(self.tab_code_editor, "Code Editor")
        self.tab_widget.addTab(self.tab_browser, "Web Browser")


    ###########################################################################
    # Tab 1: Text Generation
    ###########################################################################
    def create_text_gen_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.prompt_label = QLabel("Enter Prompt:")
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Type your prompt here...")

        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.handle_generate)

        self.result_label = QLabel("Generated Text:")
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        layout.addWidget(self.prompt_label)
        layout.addWidget(self.prompt_input)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_text)

        widget.setLayout(layout)
        return widget

    def handle_generate(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Warning", "Please enter a prompt.")
            return

        # Using the ChatCompletion API with gpt-3.5-turbo and adjusted parameters
        generated_text = self.generator(prompt, max_tokens=50, temperature=1.0)
        self.result_text.setPlainText(generated_text)


    ###########################################################################
    # Tab 2: Code Editor with Syntax Highlighting
    ###########################################################################
    def create_code_editor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        self.code_editor = QPlainTextEdit()
        self.code_editor.setPlaceholderText("# Write or paste your code here...")
        # Apply syntax highlighter
        self.highlighter = PythonHighlighter(self.code_editor.document())

        layout.addWidget(self.code_editor)
        widget.setLayout(layout)
        return widget


    ###########################################################################
    # Tab 3: Web Browser
    ###########################################################################
    def create_browser_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # A basic navigation bar (address bar + load button)
        nav_layout = QHBoxLayout()
        self.url_input = QLineEdit("https://www.google.com")
        self.load_button = QPushButton("Go")
        self.load_button.clicked.connect(self.load_url)
        nav_layout.addWidget(self.url_input)
        nav_layout.addWidget(self.load_button)

        self.webview = QWebEngineView()
        self.webview.setUrl(QUrl(self.url_input.text()))

        layout.addLayout(nav_layout)
        layout.addWidget(self.webview)
        widget.setLayout(layout)
        return widget

    def load_url(self):
        url = self.url_input.text().strip()
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        self.webview.setUrl(QUrl(url))


###############################################################################
# 4. Application Entry Point
###############################################################################

def main():
    app = QApplication(sys.argv)

    # Securely retrieve your API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        QMessageBox.critical(None, "API Key Error", "Please set the OPENAI_API_KEY environment variable.")
        sys.exit(1)

    # Using the same model as before
    model_name = "gpt-3.5-turbo"

    window = MainWindow(
        api_key=api_key,
        model_name=model_name
    )
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
