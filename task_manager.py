from dataclasses import dataclass

@dataclass
class TaskParams:
    period_ms: int
    exec_ms: int
    priority: int

class TaskManager:
    def __init__(self):
        self.tasks = {
            "ADC": TaskParams(10, 2, 2),
            "Filter": TaskParams(30, 6, 1),
            "DataTX": TaskParams(20, 4, 3)
        }
    
    def get_task_list(self):
        return [
            [name, params.period_ms, params.exec_ms, params.priority]
            for name, params in self.tasks.items()
        ]
    
    def update_task(self, name, period_ms=None, exec_ms=None, priority=None):
        if name in self.tasks:
            if period_ms is not None:
                self.tasks[name].period_ms = int(period_ms)
            if exec_ms is not None:
                self.tasks[name].exec_ms = int(exec_ms)
            if priority is not None:
                self.tasks[name].priority = int(priority)
        else:
            self.tasks[name] = TaskParams(
                int(period_ms),
                int(exec_ms),
                int(priority)
            )
    
    def remove_task(self, name):
        if name in self.tasks:
            del self.tasks[name]
    
    def get_task_dict(self):
        return {
            name: {
                "period_ms": params.period_ms,
                "exec_ms": params.exec_ms,
                "priority": params.priority
            }
            for name, params in self.tasks.items()
        }