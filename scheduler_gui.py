import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from io import BytesIO
import traceback
import ast
import os
import base64
import csv
import datetime
import tempfile
import webbrowser
from PIL import Image, ImageTk

# Import your existing modules
from scheduler_sim import Scheduler, SchedulerType, SchedulingMode, Task, FreeRTOSScheduler
from benchmark_simulator import BenchmarkSimulator
from task_manager import TaskManager

class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Scheduler Simulator")
        self.root.geometry("1200x800")
        
        # Initialize task manager
        self.task_manager = TaskManager()
        
        # Store last simulation results
        self.last_scheduler = None
        self.last_benchmark = None
        self.last_rtos = None
        self.last_sim_duration = 100
        self.last_rtos_duration = 100
        self.last_bench_duration = 200
        self.last_bench_img = None
        self.last_gantt_img = None
        self.last_rtos_img = None
        
        # Create the main layout
        self.create_widgets()
        
    def create_widgets(self):
        # Create main title
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = ttk.Label(title_frame, text="Real-Time EC Task Scheduler", 
                               font=('Arial', 18, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="Simulate and visualize embedded systems task scheduling",
                                  font=('Arial', 11))
        subtitle_label.pack()
        
        # Create separator
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, pady=5)
        
        # Create notebook (tab control)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Create tabs
        self.simulation_tab = ttk.Frame(self.notebook)
        self.benchmark_tab = ttk.Frame(self.notebook)
        self.freertos_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.simulation_tab, text='Single Simulation')
        self.notebook.add(self.benchmark_tab, text='Benchmarking')
        self.notebook.add(self.freertos_tab, text='FreeRTOS')
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Build each tab
        self.create_simulation_tab()
        self.create_benchmark_tab()
        self.create_freertos_tab()
        
    def create_simulation_tab(self):
        # Task Configuration Frame
        task_frame = ttk.LabelFrame(self.simulation_tab, text="Task Configuration")
        task_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Task table
        columns = ("Task Name", "Period (ms)", "Exec (ms)", "Priority")
        self.task_table = ttk.Treeview(task_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.task_table.heading(col, text=col)
            self.task_table.column(col, width=100)
        
        self.task_table.column("Task Name", width=150)
        
        # Add scrollbar to table
        scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_table.yview)
        self.task_table.configure(yscrollcommand=scrollbar.set)
        
        self.task_table.grid(row=0, column=0, columnspan=4, sticky='nsew', padx=5, pady=5)
        scrollbar.grid(row=0, column=4, sticky='ns', pady=5)
        
        # Task input fields
        input_frame = ttk.Frame(task_frame)
        input_frame.grid(row=1, column=0, columnspan=5, sticky='ew', padx=5, pady=5)
        
        ttk.Label(input_frame, text="Name:").grid(row=0, column=0, padx=5)
        self.task_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.task_name_var, width=15).grid(row=0, column=1, padx=5)
        
        ttk.Label(input_frame, text="Period:").grid(row=0, column=2, padx=5)
        self.task_period_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.task_period_var, width=8).grid(row=0, column=3, padx=5)
        
        ttk.Label(input_frame, text="Exec:").grid(row=0, column=4, padx=5)
        self.task_exec_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.task_exec_var, width=6).grid(row=0, column=5, padx=5)
        
        ttk.Label(input_frame, text="Priority:").grid(row=0, column=6, padx=5)
        self.task_prio_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.task_prio_var, width=5).grid(row=0, column=7, padx=5)
        
        # Task buttons
        button_frame = ttk.Frame(task_frame)
        button_frame.grid(row=2, column=0, columnspan=5, sticky='ew', padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Task", command=self.add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Update Task", command=self.update_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Task", command=self.remove_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset Tasks", command=self.reset_tasks).pack(side=tk.LEFT, padx=5)
        
        # Scheduler Settings Frame
        sched_frame = ttk.LabelFrame(self.simulation_tab, text="Scheduler Settings")
        sched_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Scheduler type
        sched_left = ttk.Frame(sched_frame)
        sched_left.pack(side=tk.LEFT, padx=10, pady=10)
        
        ttk.Label(sched_left, text="Scheduler Type:").grid(row=0, column=0, sticky='w', pady=2)
        self.sched_type_var = tk.StringVar(value="Priority")
        sched_combo = ttk.Combobox(sched_left, textvariable=self.sched_type_var, 
                                  values=['Priority', 'Round Robin'], width=15, state='readonly')
        sched_combo.grid(row=1, column=0, sticky='w', pady=2)
        
        ttk.Label(sched_left, text="Scheduling Mode:").grid(row=2, column=0, sticky='w', pady=2)
        self.sched_mode_var = tk.StringVar(value="Preemptive")
        ttk.Radiobutton(sched_left, text="Preemptive", variable=self.sched_mode_var, 
                       value="Preemptive").grid(row=3, column=0, sticky='w', pady=2)
        ttk.Radiobutton(sched_left, text="Cooperative", variable=self.sched_mode_var, 
                       value="Cooperative").grid(row=4, column=0, sticky='w', pady=2)
        
        # Simulation parameters
        sched_middle = ttk.Frame(sched_frame)
        sched_middle.pack(side=tk.LEFT, padx=20, pady=10)
        
        ttk.Label(sched_middle, text="Simulation Duration (ms):").grid(row=0, column=0, sticky='w', pady=2)
        self.duration_var = tk.StringVar(value="100")
        ttk.Entry(sched_middle, textvariable=self.duration_var, width=10).grid(row=1, column=0, sticky='w', pady=2)
        
        ttk.Label(sched_middle, text="Time Quantum (ms):").grid(row=2, column=0, sticky='w', pady=2)
        self.quantum_var = tk.StringVar(value="5")
        ttk.Entry(sched_middle, textvariable=self.quantum_var, width=10).grid(row=3, column=0, sticky='w', pady=2)
        
        # Run button
        sched_right = ttk.Frame(sched_frame)
        sched_right.pack(side=tk.LEFT, padx=20, pady=10)
        
        ttk.Button(sched_right, text="Run Simulation", command=self.run_simulation, 
                  style='Accent.TButton').pack(expand=True)
        
        # Simulation Results Frame
        results_frame = ttk.LabelFrame(self.simulation_tab, text="Simulation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Export buttons
        export_frame = ttk.Frame(results_frame)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(export_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Export PNG", command=self.export_png).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Open Full Size", command=self.view_gantt).pack(side=tk.LEFT, padx=5)
        ttk.Button(export_frame, text="Export Metrics", command=self.export_metrics).pack(side=tk.LEFT, padx=5)
        
        # Gantt chart
        gantt_frame = ttk.Frame(results_frame)
        gantt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.gantt_fig = Figure(figsize=(12, 5), dpi=100)
        self.gantt_canvas = FigureCanvasTkAgg(self.gantt_fig, gantt_frame)
        self.gantt_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Metrics text
        metrics_frame = ttk.Frame(results_frame)
        metrics_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.metrics_text = scrolledtext.ScrolledText(metrics_frame, height=8, state=tk.DISABLED)
        self.metrics_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights
        task_frame.columnconfigure(0, weight=1)
        task_frame.rowconfigure(0, weight=1)
        
        # Bind table selection event
        self.task_table.bind('<<TreeviewSelect>>', self.on_task_select)
        
        # Initialize task table
        self.update_task_table()
        
    def create_benchmark_tab(self):
        # Info text
        info_label = ttk.Label(self.benchmark_tab, 
                              text="Tasks are shared with Simulation tab", 
                              font=('Arial', 10, 'italic'), foreground='green')
        info_label.pack(padx=10, pady=5)
        
        # Variations Frame
        variations_frame = ttk.LabelFrame(self.benchmark_tab, text="Variations")
        variations_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Variations text area
        self.variations_text = scrolledtext.ScrolledText(variations_frame, height=10)
        self.variations_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Set default variations
        default_variations = '[\n    {"sched_type":"PRIORITY","mode":"PREEMPTIVE"},\n    {"sched_type":"PRIORITY","mode":"COOPERATIVE"},\n    {"sched_type":"ROUND_ROBIN","mode":"PREEMPTIVE"}\n]'
        self.variations_text.insert('1.0', default_variations)
        
        # Benchmark parameters
        bench_params = ttk.Frame(variations_frame)
        bench_params.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(bench_params, text="Duration (ms):").pack(side=tk.LEFT, padx=5)
        self.bench_duration_var = tk.StringVar(value="200")
        ttk.Entry(bench_params, textvariable=self.bench_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(bench_params, text="Run Benchmark", command=self.run_benchmark).pack(side=tk.LEFT, padx=20)
        
        # Benchmark Results Frame
        bench_results_frame = ttk.LabelFrame(self.benchmark_tab, text="Benchmark Results")
        bench_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Export buttons
        bench_export_frame = ttk.Frame(bench_results_frame)
        bench_export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(bench_export_frame, text="Export CSV", command=self.export_bench_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(bench_export_frame, text="Export PNG", command=self.export_bench_png).pack(side=tk.LEFT, padx=5)
        ttk.Button(bench_export_frame, text="Open Full Size", command=self.view_bench).pack(side=tk.LEFT, padx=5)
        ttk.Button(bench_export_frame, text="Export Report", command=self.export_report).pack(side=tk.LEFT, padx=5)
        
        # Benchmark plot
        bench_plot_frame = ttk.Frame(bench_results_frame)
        bench_plot_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.bench_fig = Figure(figsize=(12, 8), dpi=100)
        self.bench_canvas = FigureCanvasTkAgg(self.bench_fig, bench_plot_frame)
        self.bench_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Benchmark results text
        bench_text_frame = ttk.Frame(bench_results_frame)
        bench_text_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.bench_results_text = scrolledtext.ScrolledText(bench_text_frame, height=6, state=tk.DISABLED)
        self.bench_results_text.pack(fill=tk.BOTH, expand=True)
        
    def create_freertos_tab(self):
        # Info text
        info_label = ttk.Label(self.freertos_tab, 
                              text="Tasks are shared with Simulation tab", 
                              font=('Arial', 10, 'italic'), foreground='green')
        info_label.pack(padx=10, pady=5)
        
        # FreeRTOS Settings Frame
        rtos_frame = ttk.LabelFrame(self.freertos_tab, text="FreeRTOS Settings")
        rtos_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(rtos_frame, text="Simulation Duration (ms):").pack(side=tk.LEFT, padx=10, pady=10)
        self.rtos_duration_var = tk.StringVar(value="100")
        ttk.Entry(rtos_frame, textvariable=self.rtos_duration_var, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(rtos_frame, text="Run FreeRTOS Sim", command=self.run_rtos).pack(side=tk.LEFT, padx=20)
        
        # FreeRTOS Results Frame
        rtos_results_frame = ttk.LabelFrame(self.freertos_tab, text="FreeRTOS Results")
        rtos_results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Export buttons
        rtos_export_frame = ttk.Frame(rtos_results_frame)
        rtos_export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(rtos_export_frame, text="Export CSV", command=self.export_rtos_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(rtos_export_frame, text="Export PNG", command=self.export_rtos_png).pack(side=tk.LEFT, padx=5)
        ttk.Button(rtos_export_frame, text="Open Full Size", command=self.view_rtos).pack(side=tk.LEFT, padx=5)
        
        # RTOS Gantt chart
        rtos_gantt_frame = ttk.Frame(rtos_results_frame)
        rtos_gantt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.rtos_fig = Figure(figsize=(12, 5), dpi=100)
        self.rtos_canvas = FigureCanvasTkAgg(self.rtos_fig, rtos_gantt_frame)
        self.rtos_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # RTOS results text
        rtos_text_frame = ttk.Frame(rtos_results_frame)
        rtos_text_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.rtos_results_text = scrolledtext.ScrolledText(rtos_text_frame, height=4, state=tk.DISABLED)
        self.rtos_results_text.pack(fill=tk.BOTH, expand=True)
        
    def update_task_table(self):
        # Clear existing items
        for item in self.task_table.get_children():
            self.task_table.delete(item)
            
        # Add tasks from task manager
        for task in self.task_manager.get_task_list():
            self.task_table.insert('', tk.END, values=task)
            
    def on_task_select(self, event):
        selected = self.task_table.selection()
        if selected:
            item = self.task_table.item(selected[0])
            values = item['values']
            self.task_name_var.set(values[0])
            self.task_period_var.set(values[1])
            self.task_exec_var.set(values[2])
            self.task_prio_var.set(values[3])
            
    def add_task(self):
        try:
            self.task_manager.update_task(
                self.task_name_var.get(),
                self.task_period_var.get(),
                self.task_exec_var.get(),
                self.task_prio_var.get()
            )
            self.update_task_table()
            self.status_var.set("Task added successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid task parameters: {str(e)}")
            
    def update_task(self):
        selected = self.task_table.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a task to update")
            return
            
        try:
            task_name = self.task_table.item(selected[0])['values'][0]
            self.task_manager.update_task(
                task_name,
                self.task_period_var.get() or None,
                self.task_exec_var.get() or None,
                self.task_prio_var.get() or None
            )
            self.update_task_table()
            self.status_var.set("Task updated successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid update: {str(e)}")
            
    def remove_task(self):
        selected = self.task_table.selection()
        if not selected:
            messagebox.showerror("Error", "Please select a task to remove")
            return
            
        task_name = self.task_table.item(selected[0])['values'][0]
        self.task_manager.remove_task(task_name)
        self.update_task_table()
        self.status_var.set("Task removed successfully")
        
    def reset_tasks(self):
        self.task_manager.__init__()
        self.update_task_table()
        self.status_var.set("Tasks reset to defaults")
        
    def create_gantt_chart(self, gantt_data, max_time=100, figsize=(14, 6), dpi=100):
        """Create a Gantt chart visualization with improved visibility"""
        if not gantt_data:
            return None
            
        fig = Figure(figsize=figsize, dpi=dpi)
        ax = fig.add_subplot(111)
        
        # Get unique tasks and assign colors
        tasks = sorted(set([item[0] for item in gantt_data]))
        colors = plt.cm.tab10.colors
        color_map = {task: colors[i % len(colors)] for i, task in enumerate(tasks)}
        
        # Create y-axis positions
        y_pos = {task: i for i, task in enumerate(tasks)}
        
        # Plot each task execution
        for entry in gantt_data:
            task, start, end = entry
            ax.barh(y_pos[task], end-start, left=start, 
                    height=0.6, color=color_map[task], label=task)
        
        ax.set_yticks(list(range(len(tasks))))
        ax.set_yticklabels(tasks, fontsize=10)
        ax.set_xlabel('Time (ms)', fontsize=12)
        ax.set_title('Task Execution Timeline', fontsize=14)
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax.set_xlim(0, max_time)
        ax.tick_params(axis='x', labelsize=10)
        
        return fig
        
    def run_simulation(self):
        try:
            self.status_var.set("Preparing simulation...")
            self.root.update()
            
            # Get tasks from manager
            tasks_dict = {}
            for name, params in self.task_manager.get_task_dict().items():
                tasks_dict[name] = Task(
                    name=name,
                    period_ms=params["period_ms"],
                    exec_ms=params["exec_ms"],
                    priority=params["priority"]
                )
                
            if not tasks_dict:
                messagebox.showerror("Error", "Please define at least one task!")
                return
                
            # Run simulation
            scheduler = Scheduler(tasks_dict)
            s_type = SchedulerType.PRIORITY if self.sched_type_var.get() == 'Priority' else SchedulerType.ROUND_ROBIN
            mode = SchedulingMode.PREEMPTIVE if self.sched_mode_var.get() == 'Preemptive' else SchedulingMode.COOPERATIVE
            
            self.last_sim_duration = int(self.duration_var.get())
            scheduler.run(self.last_sim_duration, s_type, mode)
            self.last_scheduler = scheduler
            
            # Update UI
            self.gantt_fig.clf()
            ax = self.gantt_fig.add_subplot(111)
            
            # Get unique tasks and assign colors
            gantt_data = scheduler.gantt_log
            tasks = sorted(set([item[0] for item in gantt_data]))
            colors = plt.cm.tab10.colors
            color_map = {task: colors[i % len(colors)] for i, task in enumerate(tasks)}
            
            # Create y-axis positions
            y_pos = {task: i for i, task in enumerate(tasks)}
            
            # Plot each task execution
            for entry in gantt_data:
                task, start, end = entry
                ax.barh(y_pos[task], end-start, left=start, 
                        height=0.6, color=color_map[task], label=task)
            
            ax.set_yticks(list(range(len(tasks))))
            ax.set_yticklabels(tasks, fontsize=10)
            ax.set_xlabel('Time (ms)', fontsize=12)
            ax.set_title('Task Execution Timeline', fontsize=14)
            ax.grid(True, axis='x', linestyle='--', alpha=0.7)
            ax.set_xlim(0, self.last_sim_duration)
            ax.tick_params(axis='x', labelsize=10)
            
            self.gantt_canvas.draw()
            
            # Create image for export
            buf = BytesIO()
            self.gantt_fig.savefig(buf, format='png', bbox_inches='tight')
            self.last_gantt_img = buf.getvalue()
            
            # Show metrics
            metrics_text = (
                f"CPU Load: {scheduler.metrics['cpu_load']:.2%}\n"
                f"Idle Time: {scheduler.metrics['cpu_idle']} ms\n"
                f"Busy Time: {scheduler.metrics['cpu_busy']} ms\n"
                f"Missed Deadlines: {scheduler.metrics['deadlines_missed']}\n"
                f"Buffer Usage (avg): {sum(scheduler.metrics['buffer_state'])/len(scheduler.metrics['buffer_state']):.2f}"
            )
            
            self.metrics_text.config(state=tk.NORMAL)
            self.metrics_text.delete(1.0, tk.END)
            self.metrics_text.insert(1.0, metrics_text)
            self.metrics_text.config(state=tk.DISABLED)
            
            self.status_var.set("Simulation complete!")
            
        except Exception as e:
            self.status_var.set("Error occurred")
            error_msg = f"Simulation Error: {str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("Error", error_msg)
            
    def run_benchmark(self):
        try:
            self.status_var.set("Preparing benchmark...")
            self.root.update()
            
            # Get tasks from manager
            tasks_dict = self.task_manager.get_task_dict()
            
            if not tasks_dict:
                messagebox.showerror("Error", "Please define tasks in the table!")
                return
                
            # Parse variations
            variations_text = self.variations_text.get(1.0, tk.END)
            if not variations_text.strip():
                messagebox.showerror("Error", "Please enter variations!")
                return
                
            try:
                variations = ast.literal_eval(variations_text)
            except Exception as e:
                messagebox.showerror("Error", f"Error parsing variations: {str(e)}")
                return
                
            # Run benchmark
            benchmark = BenchmarkSimulator()
            self.last_bench_duration = int(self.bench_duration_var.get())
            benchmark.run_batch(tasks_dict, variations, self.last_bench_duration)
            self.last_benchmark = benchmark
            
            # Update UI
            self.bench_fig.clf()
            ax1 = self.bench_fig.add_subplot(211)
            ax2 = self.bench_fig.add_subplot(212)
            
            # CPU Load plot
            config_ids = [f"Config {i}" for i in range(len(benchmark.comparison_data))]
            cpu_loads = [d['cpu_load'] for d in benchmark.comparison_data]
            ax1.bar(config_ids, cpu_loads, color='skyblue')
            ax1.set_title("CPU Utilization Comparison", fontsize=14)
            ax1.set_ylabel("CPU Load", fontsize=12)
            ax1.set_ylim(0, 1)
            ax1.tick_params(axis='x', labelsize=10)
            ax1.tick_params(axis='y', labelsize=10)
            
            # Add value labels
            for i, v in enumerate(cpu_loads):
                ax1.text(i, v + 0.02, f"{v:.1%}", ha='center', fontsize=10)
            
            # Missed deadlines plot
            deadlines = [d['missed_deadlines'] for d in benchmark.comparison_data]
            ax2.bar(config_ids, deadlines, color='lightcoral')
            ax2.set_title("Missed Deadlines Comparison", fontsize=14)
            ax2.set_ylabel("Count", fontsize=12)
            ax2.tick_params(axis='x', labelsize=10)
            ax2.tick_params(axis='y', labelsize=10)
            
            # Add value labels
            for i, v in enumerate(deadlines):
                ax2.text(i, v + 0.1, str(v), ha='center', fontsize=10)
            
            self.bench_fig.tight_layout()
            self.bench_canvas.draw()
            
            # Create image for export
            buf = BytesIO()
            self.bench_fig.savefig(buf, format='png', bbox_inches='tight')
            self.last_bench_img = buf.getvalue()
            
            # Show summary
            summary = f"Benchmark complete! {len(variations)} configurations tested.\n"
            summary += f"Average CPU Load: {sum(c['cpu_load'] for c in benchmark.comparison_data)/len(benchmark.comparison_data):.2%}\n"
            summary += f"Total Missed Deadlines: {sum(c['missed_deadlines'] for c in benchmark.comparison_data)}"
            
            self.bench_results_text.config(state=tk.NORMAL)
            self.bench_results_text.delete(1.0, tk.END)
            self.bench_results_text.insert(1.0, summary)
            self.bench_results_text.config(state=tk.DISABLED)
            
            self.status_var.set("Benchmark complete!")
            
        except Exception as e:
            self.status_var.set("Benchmark failed")
            error_msg = f"Benchmark Error: {str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("Error", error_msg)
            
    def run_rtos(self):
        try:
            self.status_var.set("Preparing FreeRTOS simulation...")
            self.root.update()
            
            # Get tasks from manager
            tasks_dict = {}
            for name, params in self.task_manager.get_task_dict().items():
                tasks_dict[name] = Task(
                    name=name,
                    period_ms=params["period_ms"],
                    exec_ms=params["exec_ms"],
                    priority=params["priority"]
                )
                
            if not tasks_dict:
                messagebox.showerror("Error", "Please define tasks in the table!")
                return
                
            # Run simulation
            rtos_scheduler = FreeRTOSScheduler(tasks_dict)
            self.last_rtos_duration = int(self.rtos_duration_var.get())
            rtos_scheduler.run_rtos_simulation(self.last_rtos_duration)
            self.last_rtos = rtos_scheduler
            
            # Update UI
            self.rtos_fig.clf()
            ax = self.rtos_fig.add_subplot(111)
            
            # Get unique tasks and assign colors
            gantt_data = rtos_scheduler.gantt_log
            tasks = sorted(set([item[0] for item in gantt_data]))
            colors = plt.cm.tab10.colors
            color_map = {task: colors[i % len(colors)] for i, task in enumerate(tasks)}
            
            # Create y-axis positions
            y_pos = {task: i for i, task in enumerate(tasks)}
            
            # Plot each task execution
            for entry in gantt_data:
                task, start, end = entry
                ax.barh(y_pos[task], end-start, left=start, 
                        height=0.6, color=color_map[task], label=task)
            
            ax.set_yticks(list(range(len(tasks))))
            ax.set_yticklabels(tasks, fontsize=10)
            ax.set_xlabel('Time (ms)', fontsize=12)
            ax.set_title('FreeRTOS Task Execution Timeline', fontsize=14)
            ax.grid(True, axis='x', linestyle='--', alpha=0.7)
            ax.set_xlim(0, self.last_rtos_duration)
            ax.tick_params(axis='x', labelsize=10)
            
            self.rtos_canvas.draw()
            
            # Create image for export
            buf = BytesIO()
            self.rtos_fig.savefig(buf, format='png', bbox_inches='tight')
            self.last_rtos_img = buf.getvalue()
            
            # Show metrics
            metrics_text = (
                f"FreeRTOS Simulation Results\n"
                f"CPU Load: {rtos_scheduler.metrics['cpu_load']:.2%}\n"
                f"Missed Deadlines: {rtos_scheduler.metrics['deadlines_missed']}"
            )
            
            self.rtos_results_text.config(state=tk.NORMAL)
            self.rtos_results_text.delete(1.0, tk.END)
            self.rtos_results_text.insert(1.0, metrics_text)
            self.rtos_results_text.config(state=tk.DISABLED)
            
            self.status_var.set("FreeRTOS simulation complete!")
            
        except Exception as e:
            self.status_var.set("FreeRTOS error")
            error_msg = f"FreeRTOS Error: {str(e)}\n\n{traceback.format_exc()}"
            messagebox.showerror("Error", error_msg)
            
    def view_gantt(self):
        if self.last_gantt_img:
            self.open_image_in_viewer(self.last_gantt_img)
        else:
            messagebox.showerror("Error", "No simulation results to view!")
            
    def view_bench(self):
        if self.last_bench_img:
            self.open_image_in_viewer(self.last_bench_img)
        else:
            messagebox.showerror("Error", "No benchmark results to view!")
            
    def view_rtos(self):
        if self.last_rtos_img:
            self.open_image_in_viewer(self.last_rtos_img)
        else:
            messagebox.showerror("Error", "No FreeRTOS results to view!")
            
    def open_image_in_viewer(self, image_data):
        """Open image in default viewer for detailed inspection"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_file.write(image_data)
            temp_file.close()
            
            # Open in default viewer
            webbrowser.open(f"file://{temp_file.name}")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error opening image: {str(e)}")
            return False
            
    def export_csv(self):
        try:
            if self.last_scheduler:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")]
                )
                if filename:
                    success = self.last_scheduler.export_csv(filename)
                    if success:
                        messagebox.showinfo("Success", "CSV exported successfully!")
                    else:
                        messagebox.showerror("Error", "Export failed")
            else:
                messagebox.showerror("Error", "No simulation results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")
            
    def export_png(self):
        try:
            if self.last_scheduler and self.last_scheduler.gantt_log:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG Files", "*.png")]
                )
                if filename:
                    # Create high-quality version
                    fig = self.create_gantt_chart(
                        self.last_scheduler.gantt_log, 
                        self.last_sim_duration,
                        figsize=(16, 8),
                        dpi=300
                    )
                    if fig:
                        fig.savefig(filename, bbox_inches='tight')
                        messagebox.showinfo("Success", "Gantt chart exported successfully!")
            else:
                messagebox.showerror("Error", "No simulation results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")
            
    def export_metrics_to_csv(self, metrics, filename):
        """Export metrics to CSV file"""
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["CPU Load", f"{metrics['cpu_load']:.2%}"])
                writer.writerow(["Idle Time", f"{metrics['cpu_idle']} ms"])
                writer.writerow(["Busy Time", f"{metrics['cpu_busy']} ms"])
                writer.writerow(["Missed Deadlines", metrics['deadlines_missed']])
                writer.writerow(["Buffer State (avg)", f"{sum(metrics['buffer_state'])/len(metrics['buffer_state']):.2f}"])
                
                writer.writerow([])
                writer.writerow(["Task", "Deadlines Missed", "Avg Jitter (ms)"])
                for name in metrics['task_jitter']:
                    jitters = metrics['task_jitter'][name]
                    avg_jitter = sum(jitters)/len(jitters) if jitters else 0
                    writer.writerow([name, metrics.get(name+'_missed', 'N/A'), f"{avg_jitter:.2f}"])
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Export error: {str(e)}")
            return False
            
    def export_metrics(self):
        try:
            if self.last_scheduler:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")]
                )
                if filename:
                    success = self.export_metrics_to_csv(self.last_scheduler.metrics, filename)
                    if success:
                        messagebox.showinfo("Success", "Metrics exported successfully!")
                    else:
                        messagebox.showerror("Error", "Export failed")
            else:
                messagebox.showerror("Error", "No simulation results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")
            
    def export_bench_csv(self):
        try:
            if self.last_benchmark:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")]
                )
                if filename:
                    success = self.last_benchmark.export_comparison_csv(filename)
                    if success:
                        messagebox.showinfo("Success", "Benchmark CSV exported successfully!")
                    else:
                        messagebox.showerror("Error", "Export failed")
            else:
                messagebox.showerror("Error", "No benchmark results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")
            
    def export_bench_png(self):
        try:
            if self.last_benchmark:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG Files", "*.png")]
                )
                if filename:
                    # Create high-quality version
                    fig = Figure(figsize=(14, 10), dpi=300)
                    ax1 = fig.add_subplot(211)
                    ax2 = fig.add_subplot(212)
                    
                    # CPU Load plot
                    config_ids = [f"Config {i}" for i in range(len(self.last_benchmark.comparison_data))]
                    cpu_loads = [d['cpu_load'] for d in self.last_benchmark.comparison_data]
                    ax1.bar(config_ids, cpu_loads, color='skyblue')
                    ax1.set_title("CPU Utilization Comparison", fontsize=14)
                    ax1.set_ylabel("CPU Load", fontsize=12)
                    ax1.set_ylim(0, 1)
                    
                    # Add value labels
                    for i, v in enumerate(cpu_loads):
                        ax1.text(i, v + 0.02, f"{v:.1%}", ha='center', fontsize=10)
                    
                    # Missed deadlines plot
                    deadlines = [d['missed_deadlines'] for d in self.last_benchmark.comparison_data]
                    ax2.bar(config_ids, deadlines, color='lightcoral')
                    ax2.set_title("Missed Deadlines Comparison", fontsize=14)
                    ax2.set_ylabel("Count", fontsize=12)
                    
                    # Add value labels
                    for i, v in enumerate(deadlines):
                        ax2.text(i, v + 0.1, str(v), ha='center', fontsize=10)
                    
                    fig.tight_layout()
                    fig.savefig(filename, bbox_inches='tight')
                    messagebox.showinfo("Success", "Benchmark plot exported successfully!")
            else:
                messagebox.showerror("Error", "No benchmark results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")
            
    def export_report(self):
        try:
            if self.last_benchmark:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".md",
                    filetypes=[("Markdown Files", "*.md")]
                )
                if filename:
                    report = self.last_benchmark.generate_summary()
                    with open(filename, 'w') as f:
                        f.write(report)
                    messagebox.showinfo("Success", "Report exported successfully!")
            else:
                messagebox.showerror("Error", "No benchmark results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Report Export Error: {str(e)}")
            
    def export_rtos_csv(self):
        try:
            if self.last_rtos:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV Files", "*.csv")]
                )
                if filename:
                    success = self.last_rtos.export_csv(filename)
                    if success:
                        messagebox.showinfo("Success", "CSV exported successfully!")
                    else:
                        messagebox.showerror("Error", "Export failed")
            else:
                messagebox.showerror("Error", "No FreeRTOS results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")
            
    def export_rtos_png(self):
        try:
            if self.last_rtos and self.last_rtos.gantt_log:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG Files", "*.png")]
                )
                if filename:
                    # Create high-quality version
                    fig = self.create_gantt_chart(
                        self.last_rtos.gantt_log, 
                        self.last_rtos_duration,
                        figsize=(16, 8),
                        dpi=300
                    )
                    if fig:
                        fig.savefig(filename, bbox_inches='tight')
                        messagebox.showinfo("Success", "Gantt chart exported successfully!")
            else:
                messagebox.showerror("Error", "No FreeRTOS results to export!")
        except Exception as e:
            messagebox.showerror("Error", f"Export Error: {str(e)}")

def main():
    root = tk.Tk()
    app = SchedulerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()