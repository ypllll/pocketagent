from pocket_agent.models import TraceStep
class TraceRecorder:
    def __init__(self):
        self.steps=[]

    def record(self,*,step:int,kind:str,name:str,elapsed_ms:int,is_error:bool=False,detail:str=""):
        self.steps.append(TraceStep(
            step=step,
            kind=kind,
            name=name,
            elapsed_ms=elapsed_ms,
            is_error=is_error,
            detail=detail
        ))

    def summary(self)->str:
        lines=[f"{s.step}轮：{s.kind:<10} {s.name:<10} {s.elapsed_ms}ms" for s in self.steps]
        return "\n".join(lines)
