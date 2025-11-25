"""
Spinner animation module for CustomTkinter GUI.
Provides a reusable spinner widget and control functions.
"""

# Spinner frames for animation (braille characters)
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

class Spinner:
    """Animated spinner for CustomTkinter labels."""
    
    def __init__(self, label_widget, root_widget, interval=100):
        """
        Initialize the spinner.
        
        Args:
            label_widget: CTkLabel widget to display spinner animation
            root_widget: Root CTk window (for root.after scheduling)
            interval (int): Animation update interval in milliseconds (default 100ms)
        """
        self.label = label_widget
        self.root = root_widget
        self.interval = interval
        self.is_active = False
        self.frame_index = 0
    
    def start(self):
        """Start the spinner animation."""
        if not self.is_active:
            self.is_active = True
            self.frame_index = 0
            self.label.configure(text=SPINNER_FRAMES[0])
            self._animate()
    
    def stop(self):
        """Stop the spinner animation and hide it."""
        self.is_active = False
        self.label.configure(text="")
    
    def _animate(self):
        """Internal method to update spinner frame."""
        if self.is_active:
            self.frame_index = (self.frame_index + 1) % len(SPINNER_FRAMES)
            self.label.configure(text=SPINNER_FRAMES[self.frame_index])
            self.root.after(self.interval, self._animate)
    
    def is_spinning(self):
        """Check if spinner is currently active."""
        return self.is_active