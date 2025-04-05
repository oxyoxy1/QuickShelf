#!/usr/bin/env python3
import os
import shutil
import time
from datetime import datetime
import PySimpleGUI as sg
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import platform

class QuickShelf:
    def __init__(self):
        self.desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.config_path = os.path.join(os.path.expanduser('~'), '.quickshelf')
        self.history_file = os.path.join(self.config_path, 'file_history.csv')
        self.preferences = {}
        self.load_preferences()
        
        # Default categories with sample file extensions/patterns
        self.default_categories = {
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.heic'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv'],
            'Music': ['.mp3', '.m4a', '.wav', '.flac'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Applications': ['.app', '.dmg', '.pkg'],
            'Spreadsheets': ['.xls', '.xlsx', '.csv'],
            'Presentations': ['.ppt', '.pptx', '.key'],
            'Code': ['.py', '.js', '.html', '.css', '.json']
        }
        
    def load_preferences(self):
        """Load user preferences from config file"""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
            
        prefs_file = os.path.join(self.config_path, 'preferences.json')
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, 'r') as f:
                    import json
                    self.preferences = json.load(f)
            except:
                self.preferences = {}
    
    def save_preferences(self):
        """Save user preferences to config file"""
        prefs_file = os.path.join(self.config_path, 'preferences.json')
        with open(prefs_file, 'w') as f:
            import json
            json.dump(self.preferences, f)
    
    def scan_desktop(self):
        """Scan desktop files and return categorized list"""
        files = [f for f in os.listdir(self.desktop_path) 
                if os.path.isfile(os.path.join(self.desktop_path, f))]
        
        # Use ML to categorize files based on name (simple version)
        if len(files) > 3:  # Need minimum files for clustering
            vectorizer = TfidfVectorizer()
            X = vectorizer.fit_transform(files)
            kmeans = KMeans(n_clusters=min(5, len(files)), random_state=42)
            kmeans.fit(X)
            clusters = kmeans.labels_
            
            # Create temp categories
            categories = {}
            for i, file in enumerate(files):
                cat_name = f"Category {clusters[i]+1}"
                if cat_name not in categories:
                    categories[cat_name] = []
                categories[cat_name].append(file)
        else:
            # Fallback to extension-based categorization
            categories = {}
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                matched = False
                for cat, exts in self.default_categories.items():
                    if ext in exts:
                        if cat not in categories:
                            categories[cat] = []
                        categories[cat].append(file)
                        matched = True
                        break
                if not matched:
                    if 'Others' not in categories:
                        categories['Others'] = []
                    categories['Others'].append(file)
        
        return categories
    
    def organize_files(self, categories):
        """Organize files into folders based on categories"""
        for category, files in categories.items():
            # Create category folder if it doesn't exist
            cat_folder = os.path.join(self.desktop_path, category)
            if not os.path.exists(cat_folder):
                os.makedirs(cat_folder)
            
            # Move files
            for file in files:
                src = os.path.join(self.desktop_path, file)
                dst = os.path.join(cat_folder, file)
                shutil.move(src, dst)
                
                # Log the action
                self.log_action(file, category)
    
    def log_action(self, filename, category):
        """Log file organization actions"""
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                f.write("timestamp,filename,category,action\n")
        
        with open(self.history_file, 'a') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp},{filename},{category},moved\n")
    
    def get_recent_files(self, days=7):
        """Get recently accessed files from history"""
        if os.path.exists(self.history_file):
            df = pd.read_csv(self.history_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            recent = df[df['timestamp'] > (datetime.now() - pd.Timedelta(days=days))]
            return recent.to_dict('records')
        return []
    
    def create_dashboard(self):
        """Create a visualization of desktop usage"""
        if os.path.exists(self.history_file):
            df = pd.read_csv(self.history_file)
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            
            # Plot 1: Files per category
            cat_counts = df['category'].value_counts()
            cat_counts.plot(kind='bar', ax=ax1, color='skyblue')
            ax1.set_title('Files per Category')
            ax1.tick_params(axis='x', rotation=45)
            
            # Plot 2: Activity over time
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            time_series = df.groupby('date').size()
            time_series.plot(ax=ax2, marker='o', color='orange')
            ax2.set_title('Organization Activity')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Files Organized')
            
            plt.tight_layout()
            return fig
        return None

def main():
    # Set theme and layout
    sg.theme('LightGrey1')
    
    # Create QuickShelf instance
    qs = QuickShelf()
    
    # Main layout
    layout = [
        [sg.Text("QuickShelf - Smart Desktop Organizer", font=('Helvetica', 16))],
        [sg.Text("Your Desktop:", font=('Helvetica', 12))],
        [sg.Listbox(values=os.listdir(qs.desktop_path), size=(50, 10), key='-FILELIST-')],
        [sg.Button("Scan Desktop"), sg.Button("Organize Now"), sg.Button("Recent Files")],
        [sg.Button("View Dashboard"), sg.Button("Settings"), sg.Button("Exit")],
        [sg.StatusBar("Ready", key='-STATUS-')]
    ]
    
    # Create window
    window = sg.Window("QuickShelf", layout, finalize=True)
    
    # Event loop
    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break
            
        elif event == 'Scan Desktop':
            categories = qs.scan_desktop()
            category_text = "\n".join([f"{k}: {len(v)} files" for k, v in categories.items()])
            sg.popup("Scan Results", f"Found these categories:\n\n{category_text}")
            
        elif event == 'Organize Now':
            categories = qs.scan_desktop()
            qs.organize_files(categories)
            window['-FILELIST-'].update(values=os.listdir(qs.desktop_path))
            window['-STATUS-'].update("Files organized successfully!")
            
        elif event == 'Recent Files':
            recent = qs.get_recent_files()
            if recent:
                recent_text = "\n".join([f"{r['filename']} ({r['category']})" for r in recent])
                sg.popup("Recent Files", f"Recently organized files:\n\n{recent_text}")
            else:
                sg.popup("Recent Files", "No recent file activity found.")
                
        elif event == 'View Dashboard':
            fig = qs.create_dashboard()
            if fig:
                # Embed matplotlib figure in PySimpleGUI window
                layout_dash = [
                    [sg.Text("Desktop Organization Dashboard", font=('Helvetica', 14))],
                    [sg.Canvas(key='-CANVAS-')],
                    [sg.Button("Close")]
                ]
                window_dash = sg.Window("Dashboard", layout_dash, finalize=True)
                
                # Draw the figure
                canvas = FigureCanvasTkAgg(fig, window_dash['-CANVAS-'].TKCanvas)
                canvas.draw()
                canvas.get_tk_widget().pack(side='top', fill='both', expand=1)
                
                # Event loop for dashboard
                while True:
                    ev, vals = window_dash.read()
                    if ev == sg.WINDOW_CLOSED or ev == 'Close':
                        break
                window_dash.close()
            else:
                sg.popup("No data available", "Organize some files first to see the dashboard.")
                
        elif event == 'Settings':
            # Simple settings window
            layout_settings = [
                [sg.Text("QuickShelf Settings", font=('Helvetica', 14))],
                [sg.Checkbox("Auto-organize on startup", key='-AUTO-')],
                [sg.Checkbox("Show notifications", key='-NOTIFY-')],
                [sg.Button("Save"), sg.Button("Cancel")]
            ]
            window_settings = sg.Window("Settings", layout_settings)
            
            while True:
                ev, vals = window_settings.read()
                if ev == sg.WINDOW_CLOSED or ev == 'Cancel':
                    break
                elif ev == 'Save':
                    qs.preferences['auto_organize'] = vals['-AUTO-']
                    qs.preferences['show_notifications'] = vals['-NOTIFY-']
                    qs.save_preferences()
                    sg.popup("Settings saved!")
                    break
            window_settings.close()
    
    window.close()

if __name__ == "__main__":
    # Check if running on macOS
    if platform.system() == 'Darwin':
        main()
    else:
        print("Error: QuickShelf is designed for macOS only.")