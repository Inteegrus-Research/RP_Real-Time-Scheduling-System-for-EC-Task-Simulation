import csv
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

class SchedulerType(Enum):
    ROUND_ROBIN = "Round Robin"
    PRIORITY = "Priority"

class SchedulingMode(Enum):
    PREEMPTIVE = "Preemptive"
    COOPERATIVE = "Cooperative"

@dataclass
class Task:
    name: str
    period_ms: int
    exec_ms: int
    priority: int
    next_release: int = 0
    deadline_missed: int = 0
    remaining_exec: int = 0
    executions: List[Tuple[int, int]] = field(default_factory=list)

class Scheduler:
    def __init__(self, tasks: Dict[str, Task]):
        self.tasks = tasks
        self.current_time = 0
        self.gantt_log = []
        self.ready_queue = []
        self.current_task = None
        self.metrics = {
            'cpu_idle': 0,
            'cpu_busy': 0,
            'deadlines_missed': 0,
            'task_jitter': {name: [] for name in tasks},
            'buffer_state': []
        }
        # Initialize task states
        for task in self.tasks.values():
            task.remaining_exec = task.exec_ms
            task.next_release = 0

    def reset(self):
        self.current_time = 0
        self.gantt_log = []
        self.ready_queue = []
        self.current_task = None
        self.metrics = {
            'cpu_idle': 0,
            'cpu_busy': 0,
            'deadlines_missed': 0,
            'task_jitter': {name: [] for name in self.tasks},
            'buffer_state': []
        }
        for task in self.tasks.values():
            task.next_release = 0
            task.deadline_missed = 0
            task.remaining_exec = task.exec_ms
            task.executions = []

    def _release_tasks(self):
        for task in self.tasks.values():
            if self.current_time >= task.next_release:
                if task.next_release > 0:  # Not initial release
                    if task.remaining_exec > 0:
                        task.deadline_missed += 1
                        self.metrics['deadlines_missed'] += 1
                    
                    # Calculate jitter
                    jitter = abs((self.current_time - task.next_release) - task.period_ms)
                    self.metrics['task_jitter'][task.name].append(jitter)
                
                # Reset task state
                task.remaining_exec = task.exec_ms
                task.next_release = self.current_time + task.period_ms
                if task not in self.ready_queue:
                    self.ready_queue.append(task)

    def run(self, duration: int, s_type: SchedulerType, mode: SchedulingMode):
        self.reset()
        print(f"Starting simulation for {duration}ms")
        print(f"Tasks: {[t.name for t in self.tasks.values()]}")
        
        # Initialize first releases
        for task in self.tasks.values():
            task.next_release = 0
        
        while self.current_time < duration:
            self._release_tasks()
            self.metrics['buffer_state'].append(len(self.ready_queue))
            
            # Handle task completion
            if self.current_task and self.current_task.remaining_exec <= 0:
                self.current_task = None
            
            # Scheduling decision
            if not self.ready_queue:
                self.metrics['cpu_idle'] += 1
                self.gantt_log.append(("IDLE", self.current_time, self.current_time + 1))
                self.current_time += 1
                continue
            
            if s_type == SchedulerType.ROUND_ROBIN:
                if mode == SchedulingMode.PREEMPTIVE or not self.current_task:
                    self.current_task = self.ready_queue.pop(0)
                    # For RR, put back at the end if not finished
                    if self.current_task.remaining_exec > 1:
                        self.ready_queue.append(self.current_task)
            else:  # Priority
                if mode == SchedulingMode.PREEMPTIVE or not self.current_task:
                    # Find highest priority task (lowest number)
                    self.ready_queue.sort(key=lambda t: t.priority)
                    self.current_task = self.ready_queue.pop(0)
            
            # Execute current task
            exec_slice = min(1, self.current_task.remaining_exec)
            start = self.current_time
            end = start + exec_slice
            
            self.current_task.executions.append((start, end))
            self.current_task.remaining_exec -= exec_slice
            self.gantt_log.append((self.current_task.name, start, end))
            self.metrics['cpu_busy'] += exec_slice
            self.current_time = end
        
        # Calculate final metrics
        total_time = self.metrics['cpu_idle'] + self.metrics['cpu_busy']
        self.metrics['cpu_load'] = self.metrics['cpu_busy'] / total_time if total_time else 0
        
        print(f"Simulation complete! CPU Load: {self.metrics['cpu_load']:.2%}")
        return self.gantt_log, self.metrics

    def export_csv(self, filename: str):
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Task", "Start", "End"])
                writer.writerows(self.gantt_log)
                
                writer.writerow([])
                writer.writerow(["Metric", "Value"])
                writer.writerow(["CPU Load", f"{self.metrics['cpu_load']:.2%}"])
                writer.writerow(["Idle Time", f"{self.metrics['cpu_idle']} ms"])
                writer.writerow(["Busy Time", f"{self.metrics['cpu_busy']} ms"])
                writer.writerow(["Missed Deadlines", self.metrics['deadlines_missed']])
                
                writer.writerow([])
                writer.writerow(["Task", "Deadlines Missed", "Avg Jitter (ms)"])
                for name, task in self.tasks.items():
                    jitters = self.metrics['task_jitter'][name]
                    avg_jitter = sum(jitters)/len(jitters) if jitters else 0
                    writer.writerow([name, task.deadline_missed, f"{avg_jitter:.2f}"])
            return True
        except Exception as e:
            print(f"Export error: {str(e)}")
            return False

# FreeRTOS compatibility layer
class FreeRTOSScheduler(Scheduler):
    def __init__(self, tasks: Dict[str, Task]):
        super().__init__(tasks)
        # FreeRTOS-specific parameters
        self.tick_rate_hz = 1000  # 1ms tick rate
    
    def create_task(self, name, period, exec_time, priority):
        self.tasks[name] = Task(name, period, exec_time, priority)
    
    def run_rtos_simulation(self, duration):
        return self.run(duration, SchedulerType.PRIORITY, SchedulingMode.PREEMPTIVE)