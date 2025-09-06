import csv
import matplotlib.pyplot as plt
from io import BytesIO, StringIO
import pandas as pd
from scheduler_sim import Scheduler, SchedulerType, SchedulingMode, Task

class BenchmarkSimulator:
    def __init__(self):
        self.results = []
        self.comparison_data = []
    
    def run_batch(self, base_tasks, variations, duration=100):
        """Run batch simulations with varying parameters"""
        self.results = []
        self.comparison_data = []
        
        for i, variation in enumerate(variations):
            # Create modified task set
            tasks = {}
            for name, params in base_tasks.items():
                modified_params = params.copy()
                
                # Apply variation if specified
                if "tasks" in variation and name in variation["tasks"]:
                    for param, value in variation["tasks"][name].items():
                        modified_params[param] = value
                
                tasks[name] = Task(
                    name=name,
                    period_ms=modified_params["period_ms"],
                    exec_ms=modified_params["exec_ms"],
                    priority=modified_params["priority"]
                )
            
            # Get scheduler type and mode
            sched_type_str = variation.get("sched_type", "PRIORITY")
            sched_type = getattr(SchedulerType, sched_type_str.upper(), SchedulerType.PRIORITY)
            
            mode_str = variation.get("mode", "PREEMPTIVE")
            mode = getattr(SchedulingMode, mode_str.upper(), SchedulingMode.PREEMPTIVE)
            
            # Create and run scheduler
            scheduler = Scheduler(tasks)
            gantt, metrics = scheduler.run(duration, sched_type, mode)
            
            # Collect results
            result = {
                "id": i,
                "variation": variation,
                "scheduler": scheduler,
                "metrics": metrics,
                "gantt": gantt
            }
            
            # Collect comparison data
            comp_entry = {
                "config_id": i,
                "scheduler": sched_type.value,
                "mode": mode.value,
                "cpu_load": metrics["cpu_load"],
                "idle_time": metrics["cpu_idle"],
                "busy_time": metrics["cpu_busy"],
                "missed_deadlines": metrics["deadlines_missed"]
            }
            
            # Add task-specific metrics
            for name, task in tasks.items():
                jitter_list = metrics["task_jitter"][name]
                avg_jitter = sum(jitter_list)/len(jitter_list) if jitter_list else 0
                comp_entry[f"{name}_jitter"] = avg_jitter
                comp_entry[f"{name}_missed"] = task.deadline_missed
            
            self.results.append(result)
            self.comparison_data.append(comp_entry)
        
        return self.results
    
    def plot_comparison(self, figsize=(12, 8), dpi=100):
        """Create comparison plots with better layout"""
        if not self.comparison_data:
            return None
        
        # Create figure with proper spacing
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, dpi=dpi)
        fig.subplots_adjust(hspace=0.4)  # Add space between subplots
        
        # CPU Load plot
        config_ids = [f"Config {i}" for i in range(len(self.comparison_data))]
        cpu_loads = [d['cpu_load'] for d in self.comparison_data]
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
        deadlines = [d['missed_deadlines'] for d in self.comparison_data]
        ax2.bar(config_ids, deadlines, color='lightcoral')
        ax2.set_title("Missed Deadlines Comparison", fontsize=14)
        ax2.set_ylabel("Count", fontsize=12)
        ax2.tick_params(axis='x', labelsize=10)
        ax2.tick_params(axis='y', labelsize=10)
        
        # Add value labels
        for i, v in enumerate(deadlines):
            ax2.text(i, v + 0.1, str(v), ha='center', fontsize=10)
        
        plt.tight_layout()
        
        # Save to buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        return buf.getvalue()
    
    def export_comparison_csv(self, filename="benchmark_results.csv"):
        """Export comparison data to CSV"""
        if not self.comparison_data:
            return False
        
        df = pd.DataFrame(self.comparison_data)
        df.to_csv(filename, index=False)
        return True
    
    def export_comparison_data(self):
        """Export comparison data as string"""
        if not self.comparison_data:
            return ""
        
        df = pd.DataFrame(self.comparison_data)
        return df.to_string(index=False)
    
    def generate_summary(self, include_verilog=True):
        """Generate project summary markdown"""
        if not self.comparison_data:
            return "# Benchmark Report\nNo data available"
            
        md = "# Real-Time EC Task Scheduler Simulation Report\n\n"
        md += "## Project Overview\n"
        md += "This project simulates how embedded systems schedule concurrent tasks under real-time constraints.\n\n"
        md += "## Simulation Results\n"
        md += "### Key Metrics Across Configurations\n\n"
        md += "| Config | Scheduler | Mode | CPU Load | Missed Deadlines |\n"
        md += "|--------|-----------|------|----------|------------------|\n"
        
        for config in self.comparison_data:
            md += f"| {config['config_id']} | {config['scheduler']} | {config['mode']} "
            md += f"| {config['cpu_load']:.2%} | {config['missed_deadlines']} |\n"
        
        md += "\n## Insights\n"
        md += "- Priority-based scheduling generally provides better real-time performance\n"
        md += "- Preemptive scheduling reduces missed deadlines for high-priority tasks\n"
        md += "- CPU utilization increases with more frequent tasks\n"
        md += "- Jitter is minimized with proper priority assignment\n\n"
        
        # Add statistics
        avg_load = sum(c['cpu_load'] for c in self.comparison_data)/len(self.comparison_data)
        total_missed = sum(c['missed_deadlines'] for c in self.comparison_data)
        md += f"**Average CPU Load:** {avg_load:.2%}\n\n"
        md += f"**Total Missed Deadlines:** {total_missed}\n\n"
        
        if include_verilog:
            md += "## SystemVerilog Compatibility\n"
            md += "The simulation logic can be adapted for hardware verification:\n"
            md += "```systemverilog\n"
            md += "module task_scheduler (\n"
            md += "  input clk,\n"
            md += "  input rst\n"
            md += ");\n"
            md += "  // Task state registers\n"
            md += "  // Scheduling logic similar to Python implementation\n"
            md += "endmodule\n"
            md += "```\n"
        
        return md