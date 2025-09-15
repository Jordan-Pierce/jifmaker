import os
import sys
import math 

import subprocess
import json
import tempfile
import shutil  # Added for checking if ffprobe is available

from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QSpinBox, QComboBox, QCheckBox, QGroupBox,
                             QFileDialog, QTextEdit, QMessageBox, QSlider,
                             QGridLayout, QTabWidget, QProgressBar,
                             QSizePolicy, QFormLayout) 


# ----------------------------------------------------------------------------------------------------------------------
# Classes
# ----------------------------------------------------------------------------------------------------------------------


class JIFMaker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("Jordan Pierce", "JIFMaker")
        self.setWindowTitle("JIFMaker - Video to GIF Converter")
        
        # Add window icon
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "peanut-butter.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setGeometry(100, 100, 100, 100)
        
        # Disable maximize button
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        
        # Enable drag and drop for the main window
        self.setAcceptDrops(True)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for preview
        left_panel = QVBoxLayout()
        left_panel.setContentsMargins(0, 0, 10, 0)
        
        # Preview section
        preview_group = QGroupBox("Output Preview")
        preview_layout = QFormLayout(preview_group)  # Changed to QFormLayout
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)  # Ensure centered alignment
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setMaximumSize(400, 300)  # Fix size to prevent resizing
        self.preview_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Prevent expansion
        self.preview_label.setStyleSheet("border: 1px solid gray; background-color: black;")
        self.preview_label.setText("Output preview will appear here")
        preview_layout.addRow("", self.preview_label)  # Empty label for the preview
        
        left_panel.addWidget(preview_group)
        
        # New group box for output info
        info_group = QGroupBox("Output Info")
        info_layout = QFormLayout(info_group)  # Changed to QFormLayout
        self.dimensions_label = QLabel("Not set")
        self.size_label = QLabel("Unknown")
        info_layout.addRow("Output Dimensions:", self.dimensions_label)
        info_layout.addRow("Estimated Size:", self.size_label)
        
        left_panel.addWidget(info_group)
        
        # File info
        file_info_group = QGroupBox("File Information")
        file_info_layout = QFormLayout(file_info_group)  # Changed to QFormLayout
        self.file_info = QTextEdit()
        self.file_info.setMaximumHeight(150)
        self.file_info.setReadOnly(True)
        file_info_layout.addRow("", self.file_info)  # Removed label
        
        left_panel.addWidget(file_info_group)
        
        # Output log (moved from right panel)
        log_group = QGroupBox("Output Log")
        log_layout = QFormLayout(log_group)  # Changed to QFormLayout
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        log_layout.addRow("", self.output_log)  # Removed label
        
        left_panel.addWidget(log_group)
        
        main_layout.addLayout(left_panel)
        
        # Right panel for controls
        right_panel = QVBoxLayout()
        
        # Create tabs
        self.tabs = QTabWidget()
        right_panel.addWidget(self.tabs)
        
        # Create basic processing tab
        self.basic_tab = QWidget()
        self.tabs.addTab(self.basic_tab, "Basic Processing")
        self.setup_basic_tab()
        
        # Create advanced compression tab
        self.compression_tab = QWidget()
        self.tabs.addTab(self.compression_tab, "Advanced Compression")
        self.setup_compression_tab()
        
        # Command preview
        command_group = QGroupBox("FFmpeg Command")
        command_layout = QFormLayout(command_group)  # Changed to QFormLayout
        self.command_preview = QTextEdit()
        self.command_preview.setMaximumHeight(100)
        self.command_preview.setReadOnly(True)
        command_layout.addRow("", self.command_preview)  # Removed label
        
        right_panel.addWidget(command_group)
        
        # Process button
        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.process_file)
        right_panel.addWidget(self.process_button)
        
        # Removed progress bar entirely
        
        # Removed log_group from right_panel
        
        main_layout.addLayout(right_panel)
        
        # Variables
        self.temp_dir = tempfile.mkdtemp()
        self.current_pixmap = None
        self.original_width = 0
        self.original_height = 0
        self.original_duration = 0
        self.original_fps = 0
        
        # Connect signals
        self.connect_signals()
        
        # Initial command preview
        self.update_command_preview()
    
    def setup_basic_tab(self):
        layout = QVBoxLayout(self.basic_tab)
        
        # Input file selection
        input_group = QGroupBox("Input File")
        input_layout = QFormLayout(input_group)  # Changed to QFormLayout
        input_file_layout = QHBoxLayout()
        self.input_file_edit = QLineEdit()
        input_file_button = QPushButton("Browse...")
        input_file_button.clicked.connect(self.browse_input_file)
        input_file_layout.addWidget(self.input_file_edit)
        input_file_layout.addWidget(input_file_button)
        input_layout.addRow("Input File:", input_file_layout)
        
        layout.addWidget(input_group)
        
        # Output file selection
        output_group = QGroupBox("Output File")
        output_layout = QFormLayout(output_group)  # Changed to QFormLayout
        output_file_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit()
        output_file_button = QPushButton("Browse...")
        output_file_button.clicked.connect(self.browse_output_file)
        output_file_layout.addWidget(self.output_file_edit)
        output_file_layout.addWidget(output_file_button)
        output_layout.addRow("Output File:", output_file_layout)
        
        layout.addWidget(output_group)
        
        # Processing options
        options_group = QGroupBox("Basic Processing Options")
        options_layout = QFormLayout(options_group)  # Changed to QFormLayout
        self.width_spin = QSpinBox()
        self.width_spin.setRange(10, 3840)
        self.width_spin.setValue(800)
        self.width_spin.valueChanged.connect(self.update_dimensions)
        options_layout.addRow("Output Width:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(10, 2160)
        self.height_spin.setValue(-1)  # Will be calculated based on aspect ratio
        self.height_spin.setSpecialValueText("Auto")
        self.height_spin.valueChanged.connect(self.update_dimensions)
        options_layout.addRow("Height:", self.height_spin)
        
        self.maintain_aspect_check = QCheckBox("Maintain Aspect Ratio")
        self.maintain_aspect_check.setChecked(True)
        options_layout.addRow("", self.maintain_aspect_check)  # Empty label for checkbox
        
        # Margin controls
        margin_group = QGroupBox("Margins (Cropping)")
        margin_layout = QGridLayout(margin_group)
        
        margin_layout.addWidget(QLabel("Top:"), 0, 0)
        self.top_margin_spin = QSpinBox()
        self.top_margin_spin.setRange(0, 1000)
        self.top_margin_spin.setValue(0)
        self.top_margin_spin.valueChanged.connect(self.update_preview)
        margin_layout.addWidget(self.top_margin_spin, 0, 1)
        
        margin_layout.addWidget(QLabel("Bottom:"), 0, 2)
        self.bottom_margin_spin = QSpinBox()
        self.bottom_margin_spin.setRange(0, 1000)
        self.bottom_margin_spin.setValue(0)
        self.bottom_margin_spin.valueChanged.connect(self.update_preview)
        margin_layout.addWidget(self.bottom_margin_spin, 0, 3)
        
        margin_layout.addWidget(QLabel("Left:"), 1, 0)
        self.left_margin_spin = QSpinBox()
        self.left_margin_spin.setRange(0, 1000)
        self.left_margin_spin.setValue(0)
        self.left_margin_spin.valueChanged.connect(self.update_preview)
        margin_layout.addWidget(self.left_margin_spin, 1, 1)
        
        margin_layout.addWidget(QLabel("Right:"), 1, 2)
        self.right_margin_spin = QSpinBox()
        self.right_margin_spin.setRange(0, 1000)
        self.right_margin_spin.setValue(0)
        self.right_margin_spin.valueChanged.connect(self.update_preview)
        margin_layout.addWidget(self.right_margin_spin, 1, 3)
        
        options_layout.addRow("Margins (Cropping):", margin_group)  # Sub-group
        
        # FPS selection
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("FPS:"))
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(1, 60)
        self.fps_spin.setValue(15)
        fps_layout.addWidget(self.fps_spin)
        fps_layout.addStretch()
        options_layout.addRow("FPS:", self.fps_spin)
        
        # Color reduction
        colors_layout = QHBoxLayout()
        colors_layout.addWidget(QLabel("Max Colors:"))
        self.colors_spin = QSpinBox()
        self.colors_spin.setRange(2, 256)
        self.colors_spin.setValue(256)
        colors_layout.addWidget(self.colors_spin)
        colors_layout.addStretch()
        options_layout.addRow("Max Colors:", self.colors_spin)
        
        # Dithering algorithm
        dither_layout = QHBoxLayout()
        dither_layout.addWidget(QLabel("Dithering:"))
        self.dither_combo = QComboBox()
        self.dither_combo.addItems(["bayer", "heckbert", "floyd_steinberg", "sierra2", "sierra2_4a", "none"])
        dither_layout.addWidget(self.dither_combo)
        dither_layout.addStretch()
        options_layout.addRow("Dithering:", self.dither_combo)
        
        # Loop option
        loop_layout = QHBoxLayout()
        self.loop_check = QCheckBox("Loop infinitely")
        self.loop_check.setChecked(True)
        loop_layout.addWidget(self.loop_check)
        loop_layout.addStretch()
        options_layout.addRow("", self.loop_check)  # Empty label for checkbox
        
        # Trim options
        trim_group = QGroupBox("Trim Options")
        trim_layout = QVBoxLayout(trim_group)
        
        trim_controls = QHBoxLayout()
        trim_controls.addWidget(QLabel("Start:"))
        self.start_time_edit = QLineEdit("00:00:00")
        self.start_time_edit.setPlaceholderText("HH:MM:SS")
        trim_controls.addWidget(self.start_time_edit)
        
        trim_controls.addWidget(QLabel("End:"))
        self.end_time_edit = QLineEdit()
        self.end_time_edit.setPlaceholderText("HH:MM:SS")
        trim_controls.addWidget(self.end_time_edit)
        
        trim_layout.addLayout(trim_controls)
        options_layout.addRow("Trim Options:", trim_group)  # Sub-group
        
        layout.addWidget(options_group)
        layout.addStretch()
    
    def setup_compression_tab(self):
        layout = QVBoxLayout(self.compression_tab)
        
        # Frame optimization
        frame_group = QGroupBox("Frame Optimization")
        frame_layout = QFormLayout(frame_group)  # Changed to QFormLayout
        self.frame_skip_spin = QSpinBox()
        self.frame_skip_spin.setRange(1, 10)
        self.frame_skip_spin.setValue(1)
        self.frame_skip_spin.setToolTip("Process only every Nth frame (1 = all frames)")
        frame_layout.addRow("Frame Skip:", self.frame_skip_spin)
        
        diff_layout = QHBoxLayout()
        diff_layout.addWidget(QLabel("Min Frame Difference:"))
        self.frame_diff_slider = QSlider(Qt.Horizontal)
        self.frame_diff_slider.setRange(0, 100)
        self.frame_diff_slider.setValue(10)
        self.frame_diff_label = QLabel("10%")
        diff_layout.addWidget(self.frame_diff_slider)
        diff_layout.addWidget(self.frame_diff_label)
        self.frame_diff_slider.valueChanged.connect(
            lambda: self.frame_diff_label.setText(f"{self.frame_diff_slider.value()}%"))
        frame_layout.addRow("Min Frame Difference:", diff_layout)  # Horizontal layout
        
        layout.addWidget(frame_group)
        
        # Advanced compression
        advanced_group = QGroupBox("Advanced Compression")
        advanced_layout = QFormLayout(advanced_group)  # Changed to QFormLayout
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(["Low", "Medium", "High", "Very High"])
        self.compression_combo.setCurrentIndex(1)
        advanced_layout.addRow("Compression Level:", self.compression_combo)
        
        # Optimization options
        opt_layout = QHBoxLayout()
        self.optimize_transparency_check = QCheckBox("Optimize Transparency")
        self.optimize_transparency_check.setChecked(True)
        opt_layout.addWidget(self.optimize_transparency_check)
        
        self.no_extensions_check = QCheckBox("No GIF Extensions")
        self.no_extensions_check.setChecked(False)
        self.no_extensions_check.setToolTip("Disable GIF extensions (can reduce size but limit functionality)")
        opt_layout.addWidget(self.no_extensions_check)
        advanced_layout.addRow("", opt_layout)  # Horizontal layout for checkboxes
        
        layout.addWidget(advanced_group)
        
        # Post-processing
        post_group = QGroupBox("Post-Processing")
        post_layout = QFormLayout(post_group)  # Changed to QFormLayout
        self.gifsicle_check = QCheckBox("Use Gifsicle Optimization")
        self.gifsicle_check.setChecked(False)
        self.gifsicle_check.setToolTip("Use gifsicle for additional optimization (must be installed)")
        post_layout.addRow("Use Gifsicle Optimization:", self.gifsicle_check)
        
        self.gifsicle_level_combo = QComboBox()
        self.gifsicle_level_combo.addItems(["O1 (Fast)", "O2", "O3 (Best)"])
        self.gifsicle_level_combo.setCurrentIndex(2)
        post_layout.addRow("Level:", self.gifsicle_level_combo)
        
        layout.addWidget(post_group)
        layout.addStretch()
    
    def connect_signals(self):
        # Connect all UI elements that should update the command preview
        signals = [
            self.input_file_edit.textChanged,
            self.output_file_edit.textChanged,
            self.fps_spin.valueChanged,
            self.width_spin.valueChanged,
            self.height_spin.valueChanged,
            self.colors_spin.valueChanged,
            self.dither_combo.currentTextChanged,
            self.loop_check.stateChanged,
            self.start_time_edit.textChanged,
            self.end_time_edit.textChanged,
            self.top_margin_spin.valueChanged,
            self.bottom_margin_spin.valueChanged,
            self.left_margin_spin.valueChanged,
            self.right_margin_spin.valueChanged,
            self.frame_skip_spin.valueChanged,
            self.frame_diff_slider.valueChanged,
            self.compression_combo.currentTextChanged,
            self.optimize_transparency_check.stateChanged,
            self.no_extensions_check.stateChanged,
            self.gifsicle_check.stateChanged,
            self.gifsicle_level_combo.currentTextChanged,
        ]
        
        for signal in signals:
            signal.connect(self.update_command_preview)
            signal.connect(self.estimate_file_size)
        
        # Connect input file edit to update output filename
        self.input_file_edit.textChanged.connect(self.update_output_filename)
    
    def browse_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Input File", "", 
            "Media Files (*.gif *.mp4 *.avi *.mov *.mkv *.webm *.webp);;All Files (*)"
        )
        if file_path:
            self.input_file_edit.setText(file_path)
            self.analyze_input_file(file_path)
            
            # Auto-generate output filename
            if not self.output_file_edit.text():
                base, ext = os.path.splitext(file_path)
                output_path = f"{base}_processed.gif"
                self.output_file_edit.setText(output_path)
    
    def browse_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Select Output File", "", 
            "GIF Files (*.gif);;WebP Files (*.webp);;All Files (*)"
        )
        if file_path:
            self.output_file_edit.setText(file_path)
    
    def analyze_input_file(self, file_path):
        """Get information about the input file"""
        # Check if ffprobe is available before proceeding
        if not shutil.which("ffprobe"):
            self.file_info.setPlainText("Error: ffprobe not found. Please install FFmpeg and ensure it's in your PATH.\n\nDownload from: https://ffmpeg.org/download.html")
            self.preview_label.setText("Could not load preview")
            return
        
        try:
            # Use ffprobe to get file information
            cmd = [
                "ffprobe", 
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            # Extract relevant information
            file_info_text = f"File: {os.path.basename(file_path)}\n"
            
            # Find video stream
            video_stream = None
            for stream in info.get('streams', []):
                if stream.get('codec_type') == 'video':
                    video_stream = stream
                    break
            
            if video_stream:
                width = video_stream.get('width', 'N/A')
                height = video_stream.get('height', 'N/A')
                duration = float(video_stream.get('duration', info.get('format', {}).get('duration', 0)))
                fps_str = video_stream.get('avg_frame_rate', '0/1')
                
                # Calculate FPS safely
                try:
                    if '/' in fps_str:
                        num, den = fps_str.split('/')
                        fps = float(num) / float(den) if float(den) != 0 else 0
                    else:
                        fps = float(fps_str)
                except (ValueError, ZeroDivisionError):
                    fps = 0
                
                codec = video_stream.get('codec_name', 'N/A')
                
                file_info_text += f"Dimensions: {width}x{height}\n"
                file_info_text += f"Duration: {self.format_time(duration)}\n"
                file_info_text += f"FPS: {fps:.2f}\n"
                file_info_text += f"Codec: {codec}\n"
                
                # Set video properties
                self.original_width = int(width)
                self.original_height = int(height)
                self.original_duration = duration
                self.original_fps = fps
                self.width_spin.setValue(self.original_width)
                self.calculate_height()  # Set height based on aspect ratio
                
                # Update margin limits based on original dimensions
                max_margin = min(self.original_width, self.original_height) // 2
                for spin in [self.top_margin_spin, 
                             self.bottom_margin_spin, 
                             self.left_margin_spin, 
                             self.right_margin_spin]:
                    spin.setMaximum(max_margin)
                
                # Update duration label
                self.dimensions_label.setText(f"{self.width_spin.value()}x{self.height_spin.value()}")
                
                # Extract first frame for preview
                self.extract_frame(file_path, 0)
                
                # Estimate file size
                self.estimate_file_size()
            
            self.file_info.setPlainText(file_info_text)
            
        except FileNotFoundError:
            # Specific handling for when ffprobe isn't found (even if the pre-check passes, this is a fallback)
            self.file_info.setPlainText("Error: ffprobe not found. Please install FFmpeg and ensure it's in your PATH.\n\nDownload from: https://ffmpeg.org/download.html")
            self.preview_label.setText("Could not load preview")
        except Exception as e:
            self.file_info.setPlainText(f"Error analyzing file: {str(e)}")
            self.preview_label.setText("Could not load preview")
    
    def estimate_file_size(self):
        """Estimate the output file size based on current settings"""
        if not hasattr(self, 'original_width') or self.original_width == 0:
            self.size_label.setText("Unknown")
            return
        
        # Get current settings
        width = self.width_spin.value()
        # Get height or calculate it if auto
        if self.height_spin.value() > 0:
            height = self.height_spin.value()
        else:
            # Calculate height based on aspect ratio
            height = int(width * (self.original_height / self.original_width))
            
        colors = self.colors_spin.value()
        fps = self.fps_spin.value()
        frame_skip = self.frame_skip_spin.value()
        duration = self.original_duration
        
        # Adjust duration for trim settings
        start_time = self.start_time_edit.text()
        end_time = self.end_time_edit.text()
        
        if start_time and start_time != "00:00:00":
            try:
                start_sec = self.time_to_seconds(start_time)
                duration -= start_sec
            except:
                pass
        
        if end_time:
            try:
                end_sec = self.time_to_seconds(end_time)
                if end_sec > 0:
                    duration = min(duration, end_sec - (start_sec if 'start_sec' in locals() else 0))
            except:
                pass
        
        # Calculate estimated frames
        total_frames = (duration * self.original_fps) / frame_skip
        
        # Calculate estimated size (improved rough estimation for palette-based formats)
        # Use bits per pixel based on color palette: log2(colors)
        pixels = width * height
        bits_per_pixel = math.log2(colors) if colors > 1 else 1
        size_estimate = (pixels * total_frames * bits_per_pixel) / (8 * 1024)  # Convert to KB
        
        # Apply compression factors
        compression_map = {"Low": 1.0, "Medium": 0.7, "High": 0.5, "Very High": 0.3}
        compression_factor = compression_map.get(self.compression_combo.currentText(), 0.7)
        size_estimate *= compression_factor
        
        # Apply frame difference factor
        diff_factor = 1.0 - (self.frame_diff_slider.value() / 300.0)  # Up to 33% reduction
        size_estimate *= diff_factor
        size_estimate /= 10  # Adjusted factor for better realism
        
        # Format the size
        if size_estimate < 1024:
            self.size_label.setText(f"{size_estimate:.1f} KB")
        else:
            self.size_label.setText(f"{size_estimate/1024:.1f} MB")
    
    def time_to_seconds(self, time_str):
        """Convert HH:MM:SS format to seconds"""
        parts = time_str.split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return int(parts[0])
    
    def extract_frame(self, file_path, frame_num):
        """Extract a specific frame from the video for preview"""
        try:
            # Create temporary frame file
            frame_path = os.path.join(self.temp_dir, f"frame_{frame_num}.jpg")
            
            # Extract frame using ffmpeg
            cmd = [
                "ffmpeg",
                "-y",
                "-i", file_path,
                "-vframes", "1",
                "-q:v", "2",
                frame_path
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            # Load and display the frame
            self.current_pixmap = QPixmap(frame_path)
            if not self.current_pixmap.isNull():
                self.update_preview()
            
            # Clean up
            if os.path.exists(frame_path):
                os.remove(frame_path)
                
        except Exception as e:
            self.preview_label.setText(f"Error extracting frame: {str(e)}")
    
    def update_preview(self):
        """Update the preview with the current dimensions and margins - SIMPLIFIED VERSION"""
        if self.current_pixmap and not self.current_pixmap.isNull():
            width = self.width_spin.value()
            height = self.height_spin.value()
            
            # If height is set to auto (value <= 0), calculate based on aspect ratio
            if height <= 0:
                height = int(width * (self.original_height / self.original_width))
            
            # Get margin values
            top = self.top_margin_spin.value()
            bottom = self.bottom_margin_spin.value()
            left = self.left_margin_spin.value()
            right = self.right_margin_spin.value()
            
            # Calculate crop dimensions
            crop_width = self.original_width - left - right
            crop_height = self.original_height - top - bottom
            
            # Create a copy of the original pixmap
            cropped_pixmap = self.current_pixmap.copy(left, top, crop_width, crop_height)
            
            # Scale the cropped pixmap to the output dimensions
            scaled_pixmap = cropped_pixmap.scaled(
                width, 
                height,
                Qt.IgnoreAspectRatio if not self.maintain_aspect_check.isChecked() else Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Scale the output preview to fit the fixed preview label size (400x300)
            preview_width = 400
            preview_height = 300
            output_scaled = scaled_pixmap.scaled(
                preview_width,
                preview_height,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Set the preview to show only the output
            self.preview_label.setPixmap(output_scaled)
            self.dimensions_label.setText(f"{width}x{height} (Cropped from {crop_width}x{crop_height})")
    
    def update_dimensions(self):
        """Update dimensions based on aspect ratio setting"""
        if self.maintain_aspect_check.isChecked():
            # If width was changed, update height
            if self.sender() == self.width_spin:
                self.calculate_height()
            # If height was changed, update width
            elif self.sender() == self.height_spin and self.height_spin.value() > 0:
                self.calculate_width()
        
        self.update_preview()
        self.update_command_preview()
        self.estimate_file_size()
    
    def calculate_height(self):
        """Calculate height based on width and original aspect ratio"""
        if hasattr(self, 'original_width') and hasattr(self, 'original_height') and self.original_width > 0:
            width = self.width_spin.value()
            height = int(width * (self.original_height / self.original_width))
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(height)
            self.height_spin.blockSignals(False)
    
    def calculate_width(self):
        """Calculate width based on height and original aspect ratio"""
        if hasattr(self, 'original_width') and hasattr(self, 'original_height') and self.original_height > 0:
            height = self.height_spin.value()
            width = int(height * (self.original_width / self.original_height))
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(width)
            self.width_spin.blockSignals(False)
    
    def format_time(self, seconds):
        """Format seconds into HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def update_command_preview(self):
        input_file = self.input_file_edit.text()
        output_file = self.output_file_edit.text()
        
        if not input_file or not output_file:
            self.command_preview.setPlainText("Please select input and output files")
            return
        
        cmd = self.generate_ffmpeg_command()
        self.command_preview.setPlainText(" ".join(cmd))
    
    def generate_ffmpeg_command(self):
        input_file = self.input_file_edit.text()
        output_file = self.output_file_edit.text()
        fps = self.fps_spin.value()
        width = self.width_spin.value()
        height = self.height_spin.value()
        colors = self.colors_spin.value()
        dither = self.dither_combo.currentText()
        loop = self.loop_check.isChecked()
        start_time = self.start_time_edit.text()
        end_time = self.end_time_edit.text()
        
        # Get margin values
        top = self.top_margin_spin.value()
        bottom = self.bottom_margin_spin.value()
        left = self.left_margin_spin.value()
        right = self.right_margin_spin.value()
        
        # Get compression settings
        frame_skip = self.frame_skip_spin.value()
        optimize_transparency = self.optimize_transparency_check.isChecked()
        no_extensions = self.no_extensions_check.isChecked()
        use_gifsicle = self.gifsicle_check.isChecked()
        
        # Calculate crop dimensions
        crop_width = self.original_width - left - right
        crop_height = self.original_height - top - bottom
        
        # If height is set to auto (value <= 0), calculate based on aspect ratio
        if height <= 0:
            height = -1  # Let FFmpeg calculate height to preserve aspect ratio
        
        # Build the base command
        cmd = ["ffmpeg", "-y"]
        
        # Add start time if specified
        if start_time and start_time != "00:00:00":
            cmd.extend(["-ss", start_time])
        
        # Add input file
        cmd.extend(["-i", input_file])
        
        # Add end time if specified
        if end_time:
            cmd.extend(["-to", end_time])
        
        # For GIF output, use the two-pass method with palette generation
        if output_file.lower().endswith('.gif'):
            # Use two-pass method: generate palette first, then create GIF
            palette_path = os.path.join(self.temp_dir, "palette.png")
            
            # First pass: generate palette
            palette_cmd = [
                "ffmpeg", "-y", "-i", input_file
            ]
            
            # Add start/end time to palette generation if specified
            if start_time and start_time != "00:00:00":
                palette_cmd.extend(["-ss", start_time])
            if end_time:
                palette_cmd.extend(["-to", end_time])
                
            # Add crop filter if any margins are set
            filters = []
            if any([top, bottom, left, right]):
                filters.append(f"crop={crop_width}:{crop_height}:{left}:{top}")
            
            # For palette generation, we don't scale to output size
            # We just apply crop (if any) and then generate the palette
            filters.append(f"palettegen=max_colors={colors}:stats_mode=diff")
            
            palette_cmd.extend([
                "-vf", ",".join(filters),
                "-frames:v", "1",
                palette_path
            ])
            
            # Second pass: create GIF using palette
            gif_cmd = [
                "ffmpeg", "-y", "-i", input_file
            ]
            
            # Add start/end time to GIF creation if specified
            if start_time and start_time != "00:00:00":
                gif_cmd.extend(["-ss", start_time])
            if end_time:
                gif_cmd.extend(["-to", end_time])
            
            # Add crop filter if any margins are set
            filters = []
            if any([top, bottom, left, right]):
                filters.append(f"crop={crop_width}:{crop_height}:{left}:{top}")
            
            # Add frame skip if needed
            if frame_skip > 1:
                filters.append(f"select='not(mod(n\\,{frame_skip}))'")
            
            filters.append(f"fps={fps},scale={width}:{height}:flags=lanczos")
            
            # FIXED: Removed the unsupported lossy parameter
            gif_cmd.extend([
                "-i", palette_path,
                "-filter_complex", f"{','.join(filters)}[x];[x][1:v]paletteuse=dither={dither}:diff_mode=rectangle"
            ])
            
            # Add compression options
            if optimize_transparency:
                gif_cmd.extend(["-gifflags", "+transdiff"])
            
            if no_extensions:
                gif_cmd.extend(["-gifflags", "-offsetting"])
            
            if loop:
                gif_cmd.extend(["-loop", "0"])
            else:
                gif_cmd.extend(["-loop", "-1"])
            
            gif_cmd.append(output_file)
            
            # Add gifsicle optimization if requested
            if use_gifsicle:
                gifsicle_level = self.gifsicle_level_combo.currentText()
                level_map = {"O1 (Fast)": "-O1", "O2": "-O2", "O3 (Best)": "-O3"}
                gif_cmd.extend(["&&", "gifsicle", level_map[gifsicle_level], output_file, "-o", output_file])
            
            # Return both commands (we'll handle execution differently)
            return palette_cmd + ["&&"] + gif_cmd
        
        # For non-GIF outputs (like WebP)
        else:
            # Add crop filter if any margins are set
            filters = []
            if any([top, bottom, left, right]):
                filters.append(f"crop={crop_width}:{crop_height}:{left}:{top}")
            
            filters.append(f"fps={fps},scale={width}:{height}:flags=lanczos")
            
            cmd.extend(["-vf", ",".join(filters)])
            if loop:
                cmd.extend(["-loop", "0"])
            cmd.append(output_file)
            
            return cmd
    
    def process_file(self):
        input_file = self.input_file_edit.text()
        output_file = self.output_file_edit.text()
        
        if not input_file or not output_file:
            QMessageBox.warning(self, "Error", "Please select input and output files")
            return
        
        if not os.path.exists(input_file):
            QMessageBox.warning(self, "Error", "Input file does not exist")
            return
        
        # Set cursor to busy
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        cmd_parts = self.generate_ffmpeg_command()
        
        # For GIF processing, we need to handle the two commands separately
        if output_file.lower().endswith('.gif'):
            # Check if we need to use gifsicle (which changes the command structure)
            use_gifsicle = self.gifsicle_check.isChecked()
            
            if use_gifsicle:
                # Split the command into palette generation, GIF creation, and gifsicle optimization
                and_indices = [i for i, part in enumerate(cmd_parts) if part == "&&"]
                
                if len(and_indices) == 2:
                    palette_cmd = cmd_parts[:and_indices[0]]
                    gif_cmd = cmd_parts[and_indices[0]+1:and_indices[1]]
                    gifsicle_cmd = cmd_parts[and_indices[1]+1:]
                else:
                    # Fallback if we don't find the expected structure
                    palette_cmd = cmd_parts[:cmd_parts.index("&&")]
                    gif_cmd = cmd_parts[cmd_parts.index("&&")+1:-6]
                    gifsicle_cmd = cmd_parts[-6:]
            else:
                # Split the command into palette generation and GIF creation
                and_index = cmd_parts.index("&&")
                palette_cmd = cmd_parts[:and_index]
                gif_cmd = cmd_parts[and_index + 1:]
            
            # Extract palette path from the GIF command
            palette_path = gif_cmd[gif_cmd.index("-i") + 2]  # The palette path is after the second -i
            
            try:
                # Run palette generation
                self.output_log.append(f"Running palette generation: {' '.join(palette_cmd)}")
                # Removed progress bar visibility and range setting
                QApplication.processEvents()
                
                result1 = subprocess.run(
                    palette_cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                self.output_log.append("Palette generation completed successfully!")
                
                # Run GIF creation
                self.output_log.append(f"Running GIF creation: {' '.join(gif_cmd)}")
                QApplication.processEvents()
                
                result2 = subprocess.run(
                    gif_cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                self.output_log.append("GIF creation completed successfully!")
                
                # Run gifsicle optimization if requested
                if use_gifsicle:
                    self.output_log.append(f"Running gifsicle optimization: {' '.join(gifsicle_cmd)}")
                    QApplication.processEvents()
                    
                    result3 = subprocess.run(
                        gifsicle_cmd, 
                        capture_output=True, 
                        text=True, 
                        check=True
                    )
                    
                    self.output_log.append("Gifsicle optimization completed successfully!")
                
                # Removed progress bar visibility
                self.output_log.append("Processing completed successfully!")
                self.output_log.append("FFmpeg output:")
                
                # Clean up palette file
                if os.path.exists(palette_path):
                    os.remove(palette_path)
                
                # Restore cursor and show success message
                QApplication.restoreOverrideCursor()
                QMessageBox.information(self, "Success", "Processing completed successfully!")
                
            except subprocess.CalledProcessError as e:
                # Removed progress bar visibility
                self.output_log.append(f"Error processing file: {e}")
                if e.stdout:
                    self.output_log.append("FFmpeg output:")
                    self.output_log.append(e.stdout)
                if e.stderr:
                    self.output_log.append("FFmpeg errors:")
                    self.output_log.append(e.stderr)
                
                # Restore cursor and show error message
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Error", f"Processing failed: {str(e)}")
                
            except Exception as e:
                # Removed progress bar visibility
                self.output_log.append(f"Unexpected error: {e}")
                
                # Restore cursor and show error message
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")
        
        # For non-GIF processing
        else:
            try:
                self.output_log.append(f"Running command: {' '.join(cmd_parts)}")
                # Removed progress bar visibility and range setting
                QApplication.processEvents()
                
                result = subprocess.run(
                    cmd_parts, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                
                # Removed progress bar visibility
                self.output_log.append("Processing completed successfully!")
                self.output_log.append("FFmpeg output:")
                self.output_log.append(result.stdout)
                if result.stderr:
                    self.output_log.append("FFmpeg errors/warnings:")
                    self.output_log.append(result.stderr)
                    
                # Restore cursor and show success message
                QApplication.restoreOverrideCursor()
                QMessageBox.information(self, "Success", "Processing completed successfully!")
                    
            except subprocess.CalledProcessError as e:
                # Removed progress bar visibility
                self.output_log.append(f"Error processing file: {e}")
                self.output_log.append("FFmpeg output:")
                self.output_log.append(e.stdout)
                if e.stderr:
                    self.output_log.append("FFmpeg errors:")
                    self.output_log.append(e.stderr)
                
                # Restore cursor and show error message
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, "Error", f"Processing failed: {str(e)}")
                
            except FileNotFoundError:
                # Removed progress bar visibility
                self.output_log.append("Error: FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
                
                # Restore cursor and show error message
                QApplication.restoreOverrideCursor()
                QMessageBox.critical(self, 
                                     "Error", 
                                     "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH.")
    
    def closeEvent(self, event):
        """Clean up temporary files when closing the application"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        event.accept()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event for file drops"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event for file drops"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.input_file_edit.setText(file_path)
                self.analyze_input_file(file_path)
                
                # Auto-generate output filename
                if not self.output_file_edit.text():
                    base, ext = os.path.splitext(file_path)
                    output_path = f"{base}_processed.gif"
                    self.output_file_edit.setText(output_path)
    
    def update_output_filename(self):
        """Auto-generate output filename whenever input changes"""
        input_file = self.input_file_edit.text()
        if input_file:
            base, ext = os.path.splitext(input_file)
            output_path = f"{base}_processed.gif"
            self.output_file_edit.setText(output_path)
    
def main():
    """Main entry point for the application"""
    import argparse

    parser = argparse.ArgumentParser(description='JIFMaker - Convert videos to GIFs')
    parser.add_argument('--version', action='version', version='%(prog)s 0.1.0')

    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = JIFMaker()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
