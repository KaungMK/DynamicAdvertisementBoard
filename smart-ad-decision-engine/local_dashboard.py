"""
Main dashboard application for the Smart Advertisement Board system using local files
(instead of AWS DynamoDB and S3) with two tabs: Ad Display and Admin Dashboard
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
import os
import logging
import random
from PIL import Image, ImageTk

# Import simulation components
from environmental_analysis import WeatherClassifier
from demographic_analysis import AudienceAnalyzer
from local_content_repository import LocalContentRepository
from decision_engine import ContentDecisionEngine
from display_manager import DisplayManager
from mock_data import ENVIRONMENT_SCENARIOS, AUDIENCE_SCENARIOS, map_age_group, map_gender

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartAdDashboard")

class SmartAdDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Advertisement Board Dashboard")
        self.root.state('zoomed')  # Start maximized on Windows
        
        # Initialize simulation components with local repository
        self.weather_classifier = WeatherClassifier()
        self.audience_analyzer = AudienceAnalyzer()
        self.content_repository = LocalContentRepository()
        self.decision_engine = ContentDecisionEngine(self.content_repository)
        self.display_manager = DisplayManager()
        
        # Current state
        self.current_environment = None
        self.current_audience = None
        self.current_ad = None
        self.ad_display_thread = None
        self.stop_thread = False
        self.auto_cycle_ads = False
        
        # Sensor readings (in real system, these would come from actual sensors)
        self.temperature = 25.0  # Default: 25°C
        self.humidity = 60.0     # Default: 60%
        self.audience_count = 0  # Default: No audience detected
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        # Create Ad Display Tab
        self.ad_display_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.ad_display_tab, text="Advertisement Display")
        
        # Create Admin Dashboard Tab
        self.admin_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.admin_tab, text="Admin Dashboard")
        
        # Pack the tab control to fill the window
        self.tab_control.pack(expand=1, fill="both")
        
        # Set up Ad Display tab
        self.setup_ad_display_tab()
        
        # Set up Admin Dashboard tab
        self.setup_admin_dashboard_tab()
        
        # Start with some initial data
        self.update_environment_data()
        self.update_audience_data()
        
        # Start the auto-refresh for admin panel
        self.auto_refresh_admin()

        # Start auto-cycling ads immediately
        self.auto_cycle_var.set(True)
        self.toggle_auto_cycle()
    
    def setup_ad_display_tab(self):
        # Main frame for ad display
        self.ad_frame = tk.Frame(self.ad_display_tab, bg="black")
        self.ad_frame.pack(expand=True, fill="both")
        
        # Label to display the ad image
        self.ad_image_label = tk.Label(self.ad_frame, bg="black")
        self.ad_image_label.pack(expand=True, fill="both")
        
        # Label to show ad info at the bottom
        self.ad_info_label = tk.Label(
            self.ad_frame, 
            text="No advertisement displayed", 
            bg="black", 
            fg="white",
            font=("Arial", 12)
        )
        self.ad_info_label.pack(side="bottom", fill="x", padx=10, pady=10)
    
    def setup_admin_dashboard_tab(self):
        # Split the admin tab into left and right sides
        admin_paned = ttk.PanedWindow(self.admin_tab, orient=tk.HORIZONTAL)
        admin_paned.pack(expand=True, fill="both")
        
        # Left side: Controls and inputs
        control_frame = ttk.LabelFrame(admin_paned, text="Controls")
        admin_paned.add(control_frame, weight=30)
        
        # Right side: Statistics and monitoring
        stats_frame = ttk.LabelFrame(admin_paned, text="Statistics & Monitoring")
        admin_paned.add(stats_frame, weight=70)
        
        # Set up controls
        self.setup_control_panel(control_frame)
        
        # Set up statistics
        self.setup_statistics_panel(stats_frame)
    
    def setup_control_panel(self, parent):
        # Environment controls
        env_frame = ttk.LabelFrame(parent, text="Environment Settings")
        env_frame.pack(fill="x", padx=10, pady=5)
        
        # Temperature slider
        ttk.Label(env_frame, text="Temperature (°C):").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.temp_var = tk.DoubleVar(value=25.0)
        self.temp_scale = ttk.Scale(
            env_frame, 
            from_=0, 
            to=40, 
            orient=tk.HORIZONTAL, 
            variable=self.temp_var,
            command=lambda x: self.update_temp_label()
        )
        self.temp_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.temp_label = ttk.Label(env_frame, text="25.0 °C")
        self.temp_label.grid(row=0, column=2, padx=5, pady=2)
        
        # Humidity slider
        ttk.Label(env_frame, text="Humidity (%):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.humidity_var = tk.DoubleVar(value=60.0)
        self.humidity_scale = ttk.Scale(
            env_frame, 
            from_=0, 
            to=100, 
            orient=tk.HORIZONTAL, 
            variable=self.humidity_var,
            command=lambda x: self.update_humidity_label()
        )
        self.humidity_scale.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        self.humidity_label = ttk.Label(env_frame, text="60.0 %")
        self.humidity_label.grid(row=1, column=2, padx=5, pady=2)
        
        # Weather condition dropdown
        ttk.Label(env_frame, text="Weather:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.weather_var = tk.StringVar(value="clear")
        weather_options = ["sunny", "clear", "cloudy", "rainy", "stormy"]
        weather_dropdown = ttk.Combobox(
            env_frame, 
            textvariable=self.weather_var, 
            values=weather_options,
            state="readonly"
        )
        weather_dropdown.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        # Time of day dropdown
        ttk.Label(env_frame, text="Time of Day:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.time_var = tk.StringVar(value="afternoon")
        time_options = ["morning", "afternoon", "evening", "night"]
        time_dropdown = ttk.Combobox(
            env_frame, 
            textvariable=self.time_var, 
            values=time_options,
            state="readonly"
        )
        time_dropdown.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
        
        # Update environment button
        ttk.Button(
            env_frame, 
            text="Update Environment", 
            command=self.update_environment_data
        ).grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Audience controls
        audience_frame = ttk.LabelFrame(parent, text="Audience Settings")
        audience_frame.pack(fill="x", padx=10, pady=5)
        
        # Audience size slider
        ttk.Label(audience_frame, text="Group Size:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.group_size_var = tk.IntVar(value=0)
        self.group_size_scale = ttk.Scale(
            audience_frame, 
            from_=0, 
            to=10, 
            orient=tk.HORIZONTAL, 
            variable=self.group_size_var,
            command=lambda x: self.update_group_size_label()
        )
        self.group_size_scale.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.group_size_label = ttk.Label(audience_frame, text="0 people")
        self.group_size_label.grid(row=0, column=2, padx=5, pady=2)
        
        # Age group dropdown
        ttk.Label(audience_frame, text="Age Group:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.age_group_var = tk.StringVar(value="all")
        age_options = ["children", "teenager", "adult", "elderly", "all"]
        age_dropdown = ttk.Combobox(
            audience_frame, 
            textvariable=self.age_group_var, 
            values=age_options,
            state="readonly"
        )
        age_dropdown.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        # Gender distribution dropdown
        ttk.Label(audience_frame, text="Gender:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.gender_var = tk.StringVar(value="mixed")
        gender_options = ["mostly_male", "mostly_female", "mixed"]
        gender_dropdown = ttk.Combobox(
            audience_frame, 
            textvariable=self.gender_var, 
            values=gender_options,
            state="readonly"
        )
        gender_dropdown.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
        
        # Update audience button
        ttk.Button(
            audience_frame, 
            text="Update Audience", 
            command=self.update_audience_data
        ).grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Ad display controls
        ad_control_frame = ttk.LabelFrame(parent, text="Ad Display Controls")
        ad_control_frame.pack(fill="x", padx=10, pady=5)
        
        # Show next ad button
        ttk.Button(
            ad_control_frame, 
            text="Show Next Advertisement", 
            command=self.select_next_ad
        ).pack(fill="x", padx=5, pady=5)
        
        # Auto-cycle ads checkbox
        self.auto_cycle_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            ad_control_frame, 
            text="Auto-cycle ads (5 seconds per ad)", 
            variable=self.auto_cycle_var,
            command=self.toggle_auto_cycle
        ).pack(anchor="w", padx=5, pady=2)
        
        # Scenario presets
        scenario_frame = ttk.LabelFrame(parent, text="Scenario Presets")
        scenario_frame.pack(fill="x", padx=10, pady=5)
        
        # Environment scenarios
        ttk.Label(scenario_frame, text="Environment:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.env_scenario_var = tk.StringVar()
        env_scenario_names = [scenario["name"] for scenario in ENVIRONMENT_SCENARIOS]
        env_scenario_dropdown = ttk.Combobox(
            scenario_frame, 
            textvariable=self.env_scenario_var, 
            values=env_scenario_names,
            state="readonly"
        )
        env_scenario_dropdown.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        
        # Audience scenarios
        ttk.Label(scenario_frame, text="Audience:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.audience_scenario_var = tk.StringVar()
        audience_scenario_names = [scenario["name"] for scenario in AUDIENCE_SCENARIOS]
        audience_scenario_dropdown = ttk.Combobox(
            scenario_frame, 
            textvariable=self.audience_scenario_var, 
            values=audience_scenario_names,
            state="readonly"
        )
        audience_scenario_dropdown.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        # Apply scenario button
        ttk.Button(
            scenario_frame, 
            text="Apply Selected Scenarios", 
            command=self.apply_scenarios
        ).grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
    
    def setup_statistics_panel(self, parent):
        # Create a notebook for statistics tabs
        stats_notebook = ttk.Notebook(parent)
        stats_notebook.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Current status tab
        status_tab = ttk.Frame(stats_notebook)
        stats_notebook.add(status_tab, text="Current Status")
        
        # Performance tab
        performance_tab = ttk.Frame(stats_notebook)
        stats_notebook.add(performance_tab, text="Performance")
        
        # Rules tab
        rules_tab = ttk.Frame(stats_notebook)
        stats_notebook.add(rules_tab, text="Decision Rules")
        
        # Ads inventory tab
        inventory_tab = ttk.Frame(stats_notebook)
        stats_notebook.add(inventory_tab, text="Ad Inventory")
        
        # Set up current status panel
        self.setup_current_status_panel(status_tab)
        
        # Set up performance panel
        self.setup_performance_panel(performance_tab)
        
        # Set up rules panel
        self.setup_rules_panel(rules_tab)
        
        # Set up inventory panel
        self.setup_inventory_panel(inventory_tab)
    
    def setup_current_status_panel(self, parent):
        # Current environment section
        env_frame = ttk.LabelFrame(parent, text="Current Environment")
        env_frame.pack(fill="x", padx=10, pady=5)
        
        # Environment details
        self.env_details = tk.Text(env_frame, height=6, width=50, wrap=tk.WORD)
        self.env_details.pack(fill="both", expand=True, padx=5, pady=5)
        self.env_details.insert(tk.END, "No environment data collected yet.")
        self.env_details.config(state=tk.DISABLED)
        
        # Current audience section
        audience_frame = ttk.LabelFrame(parent, text="Current Audience")
        audience_frame.pack(fill="x", padx=10, pady=5)
        
        # Audience details
        self.audience_details = tk.Text(audience_frame, height=6, width=50, wrap=tk.WORD)
        self.audience_details.pack(fill="both", expand=True, padx=5, pady=5)
        self.audience_details.insert(tk.END, "No audience data collected yet.")
        self.audience_details.config(state=tk.DISABLED)
        
        # Current advertisement section
        ad_frame = ttk.LabelFrame(parent, text="Current Advertisement")
        ad_frame.pack(fill="x", padx=10, pady=5)
        
        # Ad details
        self.ad_details = tk.Text(ad_frame, height=8, width=50, wrap=tk.WORD)
        self.ad_details.pack(fill="both", expand=True, padx=5, pady=5)
        self.ad_details.insert(tk.END, "No advertisement selected yet.")
        self.ad_details.config(state=tk.DISABLED)
        
        # Decision details section
        decision_frame = ttk.LabelFrame(parent, text="Decision Details")
        decision_frame.pack(fill="x", padx=10, pady=5)
        
        # Decision details
        self.decision_details = tk.Text(decision_frame, height=8, width=50, wrap=tk.WORD)
        self.decision_details.pack(fill="both", expand=True, padx=5, pady=5)
        self.decision_details.insert(tk.END, "No decision data available yet.")
        self.decision_details.config(state=tk.DISABLED)
    
    def setup_performance_panel(self, parent):
        # Performance metrics section
        metrics_frame = ttk.LabelFrame(parent, text="Performance Metrics")
        metrics_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create a canvas with a scrollbar for performance logs
        canvas_frame = ttk.Frame(metrics_frame)
        canvas_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Performance log text widget
        self.performance_log = tk.Text(scrollable_frame, height=20, width=80, wrap=tk.WORD)
        self.performance_log.pack(fill="both", expand=True, padx=5, pady=5)
        self.performance_log.insert(tk.END, "Performance log will appear here...")
        self.performance_log.config(state=tk.DISABLED)
        
        # Controls for performance metrics
        controls_frame = ttk.Frame(metrics_frame)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        # Refresh button
        ttk.Button(
            controls_frame, 
            text="Refresh Performance Data", 
            command=self.refresh_performance_data
        ).pack(side="left", padx=5)
        
        # Export button
        ttk.Button(
            controls_frame, 
            text="Export Performance Data", 
            command=self.export_performance_data
        ).pack(side="left", padx=5)
    
    def setup_rules_panel(self, parent):
        # Rules section
        rules_frame = ttk.LabelFrame(parent, text="Decision Engine Rules")
        rules_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Rules text widget with scrollbar
        self.rules_text = tk.Text(rules_frame, height=25, width=80, wrap=tk.WORD)
        rules_scrollbar = ttk.Scrollbar(rules_frame, orient="vertical", command=self.rules_text.yview)
        self.rules_text.configure(yscrollcommand=rules_scrollbar.set)
        
        self.rules_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        rules_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Display current rules
        self.refresh_rules_display()
        
        # Controls for rules
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Edit rules button (in a real system, this would open a rule editor)
        ttk.Button(
            controls_frame, 
            text="Edit Rules", 
            command=self.edit_rules
        ).pack(side="left", padx=5)
        
        # Apply rules button
        ttk.Button(
            controls_frame, 
            text="Update Rules", 
            command=self.update_rules
        ).pack(side="left", padx=5)
        
        # Reset rules button
        ttk.Button(
            controls_frame, 
            text="Reset to Default Rules", 
            command=self.reset_rules
        ).pack(side="left", padx=5)
    
    def setup_inventory_panel(self, parent):
        # Inventory section
        inventory_frame = ttk.LabelFrame(parent, text="Advertisement Inventory")
        inventory_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create treeview for ad inventory
        columns = ("ad_id", "title", "age_group", "gender", "temperature", "humidity")
        self.inventory_tree = ttk.Treeview(inventory_frame, columns=columns, show="headings")
        
        # Define headings
        self.inventory_tree.heading("ad_id", text="ID")
        self.inventory_tree.heading("title", text="Title")
        self.inventory_tree.heading("age_group", text="Age Group")
        self.inventory_tree.heading("gender", text="Gender")
        self.inventory_tree.heading("temperature", text="Temperature")
        self.inventory_tree.heading("humidity", text="Humidity")
        
        # Configure column widths
        self.inventory_tree.column("ad_id", width=50)
        self.inventory_tree.column("title", width=150)
        self.inventory_tree.column("age_group", width=100)
        self.inventory_tree.column("gender", width=80)
        self.inventory_tree.column("temperature", width=100)
        self.inventory_tree.column("humidity", width=100)
        
        # Add scrollbar
        inventory_scrollbar = ttk.Scrollbar(inventory_frame, orient="vertical", command=self.inventory_tree.yview)
        self.inventory_tree.configure(yscrollcommand=inventory_scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.inventory_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        inventory_scrollbar.pack(side="right", fill="y", pady=5)
        
        # Populate inventory
        self.refresh_inventory()
        
        # Add selection event
        self.inventory_tree.bind("<<TreeviewSelect>>", self.on_inventory_select)
        
        # Controls for inventory
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # Refresh inventory button
        ttk.Button(
            controls_frame, 
            text="Refresh Inventory", 
            command=self.refresh_inventory
        ).pack(side="left", padx=5)
        
        # View ad button
        ttk.Button(
            controls_frame, 
            text="View Selected Ad", 
            command=self.view_selected_ad
        ).pack(side="left", padx=5)
        
        # Ad metadata edit button
        ttk.Button(
            controls_frame, 
            text="Edit Ad Metadata", 
            command=self.edit_ad_metadata
        ).pack(side="left", padx=5)
    
    def update_temp_label(self):
        temp = self.temp_var.get()
        self.temp_label.config(text=f"{temp:.1f} °C")
        self.temperature = temp
    
    def update_humidity_label(self):
        humidity = self.humidity_var.get()
        self.humidity_label.config(text=f"{humidity:.1f} %")
        self.humidity = humidity
    
    def update_group_size_label(self):
        size = self.group_size_var.get()
        self.group_size_label.config(text=f"{size} people")
        self.audience_count = size
    
    def update_environment_data(self):
        """Update environment data based on current control settings"""
        self.current_environment = {
            "temperature": self.temperature,
            "humidity": self.humidity,
            "weather": self.weather_var.get(),
            "time_of_day": self.time_var.get()
        }
        
        # Process through the classifier
        self.current_environment = self.weather_classifier.classify(
            self.temperature,
            self.humidity,
            self.weather_var.get()
        )
        
        # Update the display
        self.update_environment_display()
        
        # If auto-cycle is on, this will trigger a new ad selection
        if self.auto_cycle_ads:
            self.select_next_ad()
    
    def update_audience_data(self):
        """Update audience data based on current control settings"""
        audience_data = {
            "estimated_age_group": self.age_group_var.get(),
            "gender_distribution": self.gender_var.get(),
            "group_size": self.group_size_var.get(),
            "attention_span": random.uniform(3, 10),  # Random value for simulation
            "audience_present": self.group_size_var.get() > 0
        }
        
        # Set current audience profile
        self.current_audience = audience_data
        
        # Update the display
        self.update_audience_display()
        
        # If auto-cycle is on, this will trigger a new ad selection
        if self.auto_cycle_ads:
            self.select_next_ad()
    
    def update_environment_display(self):
        """Update the environment details display"""
        if not self.current_environment:
            return
            
        # Update text display
        self.env_details.config(state=tk.NORMAL)
        self.env_details.delete(1.0, tk.END)
        
        env_text = f"Temperature: {self.current_environment['temperature']:.1f}°C "
        env_text += f"({self.current_environment['temperature_category']})\n"
        env_text += f"Humidity: {self.current_environment['humidity']:.1f}% "
        env_text += f"({self.current_environment['humidity_category']})\n"
        env_text += f"Weather: {self.current_environment['weather']}\n"
        env_text += f"Time of Day: {self.current_environment['time_of_day']}\n"
        env_text += f"Day of Week: {self.current_environment['day_of_week']}"
        
        self.env_details.insert(tk.END, env_text)
        self.env_details.config(state=tk.DISABLED)
    
    def update_audience_display(self):
        """Update the audience details display"""
        if not self.current_audience:
            return
            
        # Update text display
        self.audience_details.config(state=tk.NORMAL)
        self.audience_details.delete(1.0, tk.END)
        
        if self.current_audience.get("audience_present", False):
            audience_text = f"Group Size: {self.current_audience['group_size']} people\n"
            audience_text += f"Age Group: {self.current_audience['estimated_age_group']}\n"
            audience_text += f"Gender Distribution: {self.current_audience['gender_distribution']}\n"
            audience_text += f"Estimated Attention Span: {self.current_audience.get('attention_span', 0):.1f} seconds"
        else:
            audience_text = "No audience detected."
        
        self.audience_details.insert(tk.END, audience_text)
        self.audience_details.config(state=tk.DISABLED)
    
    def update_ad_display(self, ad, selection_data=None):
        """Update the ad display with the selected advertisement"""
        if not ad:
            return
        
        self.current_ad = ad
        
        # Update text display in admin panel
        self.ad_details.config(state=tk.NORMAL)
        self.ad_details.delete(1.0, tk.END)
        
        ad_text = f"Title: {ad['title']}\n"
        ad_text += f"ID: {ad['ad_id']}\n"
        ad_text += f"Target Demographics: {ad['age_group']} / {ad['gender']}\n"
        ad_text += f"Optimal Conditions: {ad['temperature']} temperature, {ad['humidity']} humidity\n"
        ad_text += f"Image File: {ad['image_file']}"
        
        self.ad_details.insert(tk.END, ad_text)
        self.ad_details.config(state=tk.DISABLED)
        
        # Update decision details if available
        if selection_data:
            self.decision_details.config(state=tk.NORMAL)
            self.decision_details.delete(1.0, tk.END)
            
            decision_text = f"Selection Score: {selection_data['score']:.2f}\n\n"
            
            if '_score_details' in ad:
                details = ad['_score_details']
                decision_text += f"Weather Match Score: {details['weather_score']:.1f}/40\n"
                decision_text += f"Audience Match Score: {details['audience_score']:.1f}/40\n"
                decision_text += f"Novelty Score: {details['novelty_score']:.1f}/20\n"
                decision_text += f"Rule Multiplier: {details['rule_multiplier']:.1f}x\n\n"
            
            if 'alternatives' in selection_data:
                decision_text += "Alternative Options:\n"
                for alt in selection_data['alternatives']:
                    decision_text += f"- {alt['title']} (Score: {alt['score']:.2f})\n"
            
            self.decision_details.insert(tk.END, decision_text)
            self.decision_details.config(state=tk.DISABLED)
    
    def select_next_ad(self):
        """Select and display the next advertisement based on current conditions"""
        if not self.current_environment or not self.current_audience:
            logger.warning("Cannot select ad: Missing environment or audience data")
            return
            
        # Use the decision engine to select the optimal content
        selection = self.decision_engine.select_optimal_content(
            self.current_environment, 
            self.current_audience
        )
        
        if not selection:
            logger.warning("No suitable advertisement found")
            return
            
        # Display the selected advertisement
        self.display_ad(selection['ad'], selection)
        
    def display_ad(self, ad, selection_data=None):
        """Display the selected advertisement in the UI"""
        if not ad:
            return
            
        try:
            # Update the admin dashboard display
            self.update_ad_display(ad, selection_data)
            
            # Get the image path from the repository
            image_path = self.content_repository.get_ad_image_path(ad)
            
            try:
                # Load and display the image
                img = Image.open(image_path)
                
                # Resize to fit screen
                screen_width = self.ad_frame.winfo_width()
                screen_height = self.ad_frame.winfo_height()
                
                # Only resize if we have valid dimensions
                if screen_width > 100 and screen_height > 100:
                    img = img.resize((screen_width, screen_height), Image.LANCZOS)
                
                # Convert to Tkinter format
                img_tk = ImageTk.PhotoImage(img)
                
                # Update the image label
                self.ad_image_label.config(image=img_tk)
                self.ad_image_label.image = img_tk  # Keep a reference
                
                # Update the info label
                self.ad_info_label.config(
                    text=f"Now Showing: {ad['title']} (Target: {ad['age_group']}, {ad['temperature']} weather)"
                )
                
                logger.info(f"Successfully displayed ad: {ad['title']} (ID: {ad['ad_id']})")
                
            except Exception as e:
                logger.error(f"Error displaying image: {e}")
                self.ad_image_label.config(image=None)
                self.ad_info_label.config(text=f"Error displaying image for: {ad['title']}")
        
        except Exception as e:
            logger.error(f"Error in display_ad: {e}")
    
    def toggle_auto_cycle(self):
        """Toggle automatic cycling of advertisements"""
        self.auto_cycle_ads = self.auto_cycle_var.get()
        
        if self.auto_cycle_ads:
            # Start the auto-cycle thread
            if not self.ad_display_thread or not self.ad_display_thread.is_alive():
                self.stop_thread = False
                self.ad_display_thread = threading.Thread(target=self.auto_cycle_thread)
                self.ad_display_thread.daemon = True
                self.ad_display_thread.start()
                logger.info("Started automatic ad cycling")
        else:
            # Stop the auto-cycle thread
            self.stop_thread = True
            logger.info("Stopped automatic ad cycling")
    
    def auto_cycle_thread(self):
        """Thread function for automatic cycling of advertisements"""
        while not self.stop_thread:
            # Select and display the next ad
            self.select_next_ad()
            
            # Wait for 5 seconds
            for _ in range(50):  # Check stop flag every 100ms
                if self.stop_thread:
                    break
                time.sleep(0.1)
    
    def apply_scenarios(self):
        """Apply the selected scenarios from presets"""
        # Find the selected environment scenario
        env_scenario_name = self.env_scenario_var.get()
        for scenario in ENVIRONMENT_SCENARIOS:
            if scenario["name"] == env_scenario_name:
                # Update UI controls to match scenario
                self.temp_var.set(scenario["temperature"])
                self.humidity_var.set(scenario["humidity"])
                self.weather_var.set(scenario["weather"])
                self.time_var.set(scenario["time_of_day"])
                
                # Update labels
                self.update_temp_label()
                self.update_humidity_label()
                
                # Apply the environment data
                self.update_environment_data()
                break
        
        # Find the selected audience scenario
        audience_scenario_name = self.audience_scenario_var.get()
        for scenario in AUDIENCE_SCENARIOS:
            if scenario["name"] == audience_scenario_name:
                # Update UI controls to match scenario
                self.group_size_var.set(scenario["group_size"])
                self.age_group_var.set(scenario["estimated_age_group"])
                self.gender_var.set(scenario["gender_distribution"])
                
                # Update labels
                self.update_group_size_label()
                
                # Apply the audience data
                self.update_audience_data()
                break
        
        logger.info(f"Applied scenarios - Environment: {env_scenario_name}, Audience: {audience_scenario_name}")
    
    def refresh_performance_data(self):
        """Refresh the performance data display"""
        # Get the performance log from the decision engine
        performance_data = self.decision_engine.performance_log
        
        # Update the performance log display
        self.performance_log.config(state=tk.NORMAL)
        self.performance_log.delete(1.0, tk.END)
        
        if not performance_data:
            self.performance_log.insert(tk.END, "No performance data available.")
        else:
            for entry in performance_data:
                log_entry = f"Timestamp: {entry['timestamp']}\n"
                log_entry += f"Ad ID: {entry['ad_id']}\n"
                log_entry += f"Score at Selection: {entry.get('score_at_selection', 'N/A')}\n"
                
                if 'metrics' in entry:
                    log_entry += "Metrics:\n"
                    for key, value in entry['metrics'].items():
                        log_entry += f"  - {key}: {value}\n"
                
                log_entry += "-" * 40 + "\n"
                self.performance_log.insert(tk.END, log_entry)
        
        self.performance_log.config(state=tk.DISABLED)
    
    def export_performance_data(self):
        """Export performance data to a file"""
        # Export to JSON file
        try:
            with open("performance_data.json", "w") as f:
                json.dump(self.decision_engine.performance_log, f, indent=2)
            logger.info("Exported performance data to performance_data.json")
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
    
    def refresh_rules_display(self):
        """Refresh the rules display"""
        # Get the current rules from the decision engine
        rules = self.decision_engine.rules
        
        # Update the rules text display
        self.rules_text.config(state=tk.NORMAL)
        self.rules_text.delete(1.0, tk.END)
        
        if not rules:
            self.rules_text.insert(tk.END, "No rules defined.")
        else:
            for rule in rules:
                rule_text = f"Rule ID: {rule['id']}\n"
                rule_text += f"Name: {rule['name']}\n"
                rule_text += f"Priority: {rule['priority']}\n"
                rule_text += f"Weight: {rule['weight']}\n"
                
                if 'conditions' in rule:
                    rule_text += "Conditions:\n"
                    for key, value in rule['conditions'].items():
                        rule_text += f"  - {key}: {value}\n"
                
                rule_text += "-" * 40 + "\n"
                self.rules_text.insert(tk.END, rule_text)
        
        self.rules_text.config(state=tk.NORMAL)
    
    def edit_rules(self):
        """Open a dialog to edit rules (simplified in this demo)"""
        # In a real system, this would open a proper rule editor dialog
        # For the demo, we just make the rules text editable
        if self.rules_text.cget("state") == tk.NORMAL:
            self.rules_text.config(state=tk.DISABLED)
        else:
            self.rules_text.config(state=tk.NORMAL)
    
    def update_rules(self):
        """Update the rules based on the editor (simplified)"""
        # In a real system, this would parse the text and update the rules
        # For the demo, we just simulate rule updates
        
        # Simulate updating rule weights
        for rule in self.decision_engine.rules:
            # Small random adjustment (±10%)
            adjustment = random.uniform(-0.1, 0.1)
            rule["weight"] = max(0.5, min(2.0, rule["weight"] + adjustment))
        
        # Refresh the display
        self.refresh_rules_display()
        logger.info("Updated decision rules")
    
    def reset_rules(self):
        """Reset rules to defaults"""
        # In a real system, this would load default rules from a file
        # For the demo, we just re-initialize the decision engine
        self.decision_engine = ContentDecisionEngine(self.content_repository)
        
        # Refresh the display
        self.refresh_rules_display()
        logger.info("Reset decision rules to defaults")
    
    def refresh_inventory(self):
        """Refresh the ad inventory display"""
        # Clear existing items
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        
        # Get all ads from the repository
        ads = self.content_repository.get_all_ads()
        
        # Add ads to the treeview
        for ad in ads:
            self.inventory_tree.insert(
                "", "end", 
                values=(
                    ad["ad_id"], 
                    ad["title"], 
                    ad["age_group"], 
                    ad["gender"],
                    ad["temperature"], 
                    ad["humidity"]
                )
            )
    
    def on_inventory_select(self, event):
        """Handle inventory selection event"""
        # This method is called when an ad is selected in the inventory view
        pass
    
    def view_selected_ad(self):
        """Display the ad selected in the inventory"""
        # Get the selected item
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            return
            
        # Get the ad_id from the selected item
        item = selected_items[0]
        ad_id = self.inventory_tree.item(item, "values")[0]
        
        # Get the ad from the repository
        ad = self.content_repository.get_ad_by_id(ad_id)
        if ad:
            # Display the ad
            self.display_ad(ad)
    
    def edit_ad_metadata(self):
        """Edit metadata for the selected ad"""
        # Get the selected item
        selected_items = self.inventory_tree.selection()
        if not selected_items:
            logger.warning("No ad selected for metadata editing")
            return
            
        # Get the ad_id from the selected item
        item = selected_items[0]
        ad_id = self.inventory_tree.item(item, "values")[0]
        
        # Get the ad from the repository
        ad = self.content_repository.get_ad_by_id(ad_id)
        if not ad:
            logger.warning(f"Ad {ad_id} not found")
            return
        
        # Create a dialog to edit the metadata
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title(f"Edit Ad Metadata: {ad['title']}")
        edit_dialog.geometry("400x300")
        edit_dialog.transient(self.root)  # Make it modal
        
        # Create form fields
        ttk.Label(edit_dialog, text="Title:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        title_var = tk.StringVar(value=ad['title'])
        ttk.Entry(edit_dialog, textvariable=title_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(edit_dialog, text="Age Group:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        age_group_var = tk.StringVar(value=ad['age_group'])
        age_options = ["children", "teenager", "adult", "elderly", "all"]
        ttk.Combobox(
            edit_dialog, 
            textvariable=age_group_var, 
            values=age_options,
            state="readonly"
        ).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(edit_dialog, text="Gender:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        gender_var = tk.StringVar(value=ad['gender'])
        gender_options = ["male", "female", "both"]
        ttk.Combobox(
            edit_dialog, 
            textvariable=gender_var, 
            values=gender_options,
            state="readonly"
        ).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(edit_dialog, text="Temperature:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        temp_var = tk.StringVar(value=ad['temperature'])
        temp_options = ["cold", "moderate", "hot", "rainy"]
        ttk.Combobox(
            edit_dialog, 
            textvariable=temp_var, 
            values=temp_options,
            state="readonly"
        ).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(edit_dialog, text="Humidity:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        humidity_var = tk.StringVar(value=ad['humidity'])
        humidity_options = ["low", "medium", "high"]
        ttk.Combobox(
            edit_dialog, 
            textvariable=humidity_var, 
            values=humidity_options,
            state="readonly"
        ).grid(row=4, column=1, padx=5, pady=5)
        
        # Save button
        def save_metadata():
            # Collect updated values
            updates = {
                "title": title_var.get(),
                "age_group": age_group_var.get(),
                "gender": gender_var.get(),
                "temperature": temp_var.get(),
                "humidity": humidity_var.get()
            }
            
            # Update the repository
            if self.content_repository.update_ad_metadata(ad_id, updates):
                logger.info(f"Updated metadata for ad {ad_id}")
                # Refresh the inventory display
                self.refresh_inventory()
                # Close the dialog
                edit_dialog.destroy()
            else:
                logger.error(f"Failed to update metadata for ad {ad_id}")
        
        ttk.Button(
            edit_dialog, 
            text="Save Changes", 
            command=save_metadata
        ).grid(row=5, column=0, columnspan=2, padx=5, pady=10)
        
        # Cancel button
        ttk.Button(
            edit_dialog, 
            text="Cancel", 
            command=edit_dialog.destroy
        ).grid(row=6, column=0, columnspan=2, padx=5, pady=5)
    
    def auto_refresh_admin(self):
        """Auto-refresh the admin panel every 5 seconds"""
        # In a real system, this would update with real-time data
        try:
            if self.current_environment and self.current_audience:
                self.update_environment_display()
                self.update_audience_display()
        except Exception as e:
            logger.error(f"Error in auto-refresh: {e}")
            
        # Schedule next refresh
        self.root.after(5000, self.auto_refresh_admin)


def main():
    """Main function to run the dashboard"""
    root = tk.Tk()
    app = SmartAdDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()