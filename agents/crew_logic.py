import os
import json
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv

from crewai import Agent, Task, Crew, Process, LLM

# Load environment variables
load_dotenv()


def _load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _config_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "config")


class ComplianceCrew:
    """
    4-agent CrewAI regulatory compliance pipeline.

    Execution model:
      1. run_extraction_and_audit(document_path) -> tasks 1-3
      2. Streamlit displays results; human clicks Approve
      3. run_execution(approval_event) -> task 4 (IT Dispatcher)
    """

    def __init__(self, llm=None, verbose: bool = True):
        # Use Gemini LLM by default if no LLM is provided
        if llm is None:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
            if gemini_api_key:
                self.llm = LLM(
                    model="gemini/gemini-flash-latest",
                    api_key=gemini_api_key
                )
            else:
                self.llm = None
        else:
            self.llm = llm

        self.verbose = verbose
        self._agents_cfg = _load_yaml(os.path.join(_config_dir(), "agents.yaml"))
        self._tasks_cfg = _load_yaml(os.path.join(_config_dir(), "tasks.yaml"))

        self._agents: Dict[str, Agent] = {}
        self._tasks: Dict[str, Task] = {}
        self._last_result: Optional[str] = None
        self._map_output: Optional[str] = None
        self._audit_output: Optional[str] = None

    def _get_agent(self, name: str) -> Agent:
        if name not in self._agents:
            cfg = self._agents_cfg.get(name)
            if not cfg:
                raise KeyError(f"Agent '{name}' not found in agents.yaml")
            self._agents[name] = Agent(
                role=cfg["role"],
                goal=cfg["goal"],
                backstory=cfg["backstory"],
                llm=self.llm,
                verbose=self.verbose,
                allow_delegation=False,
            )
        return self._agents[name]

    def _build_task(
        self,
        name: str,
        description_kwargs: Optional[Dict[str, str]] = None,
        context_tasks: Optional[List[Task]] = None,
    ) -> Task:
        cfg = self._tasks_cfg.get(name)
        if not cfg:
            raise KeyError(f"Task '{name}' not found in tasks.yaml")

        description = cfg["description"]
        if description_kwargs:
            description = description.format(**description_kwargs)

        task = Task(
            description=description,
            expected_output=cfg["expected_output"],
            agent=self._get_agent(cfg["agent"]),
            context=context_tasks or [],
        )
        self._tasks[name] = task
        return task

    # ------------------------------------------------------------------
    # Phase 1: Extract → MAP → Audit  (returns JSON strings)
    # ------------------------------------------------------------------

    def run_extraction_and_audit(self, document_path: str) -> Dict[str, Any]:
        """
        Run the first three tasks. Returns raw crew outputs as strings.
        Streamlit is responsible for parsing JSON and presenting the HITL gate.
        """
        # Task 1
        t_extract = self._build_task(
            "extract_regulatory_clauses",
            description_kwargs={"document_path": document_path},
        )

        # Task 2 (depends on 1)
        t_generate = self._build_task(
            "generate_action_points",
            context_tasks=[t_extract],
        )

        # Task 3 (depends on 1 & 2)
        t_audit = self._build_task(
            "audit_action_points",
            context_tasks=[t_extract, t_generate],
        )

        crew = Crew(
            agents=list(self._agents.values()),
            tasks=[t_extract, t_generate, t_audit],
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        self._last_result = result

        # Persist intermediate outputs so Phase 2 can reference them
        self._map_output = t_generate.output.raw if t_generate.output else ""
        self._audit_output = t_audit.output.raw if t_audit.output else ""

        return {
            "extract_output": t_extract.output.raw if t_extract.output else "",
            "map_output": self._map_output,
            "audit_output": self._audit_output,
            "crew_result": result,
        }

    # ------------------------------------------------------------------
    # Phase 2: Execute & Log  (triggered after HITL approval)
    # ------------------------------------------------------------------

    def run_execution(self, approval_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Trigger the IT Dispatcher after human approval.
        `approval_event` must match the schema defined in tasks.yaml.
        """
        # Rehydrate prior task objects so Task 4 has full context
        t_generate = self._tasks.get("generate_action_points")
        t_audit = self._tasks.get("audit_action_points")

        # Build a synthetic human_approval_gate task carrying the approval event
        t_hitl = self._build_task(
            "human_approval_gate",
            context_tasks=[t_audit] if t_audit else [],
        )
        # Override expected output with the actual approval JSON
        t_hitl.expected_output = json.dumps(approval_event, indent=2)

        t_execute = self._build_task(
            "execute_and_log",
            context_tasks=[t_generate, t_audit, t_hitl]
            if (t_generate and t_audit)
            else [],
        )

        crew = Crew(
            agents=[self._get_agent("it_dispatcher")],
            tasks=[t_execute],
            process=Process.sequential,
            verbose=self.verbose,
        )

        result = crew.kickoff()
        return {
            "execution_output": t_execute.output.raw if t_execute.output else "",
            "crew_result": result,
            "approval_event": approval_event,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    print("🚀 Starting the Compliance Crew Run...")

    # Define the input variables expected by your tasks.yaml
    pdf_path = "../data_assets/sample_rbi_circular.pdf"

    try:
        # Instantiate your crew and kick it off
        crew_instance = ComplianceCrew()
        result = crew_instance.run_extraction_and_audit(document_path=pdf_path)

        print("\n==============================================")
        print("✅ FINAL PIPELINE OUTPUT (Pending HITL Approval):")
        print("==============================================")
        print("\n--- Extract Output ---")
        print(result.get("extract_output", ""))
        print("\n--- MAP Output ---")
        print(result.get("map_output", ""))
        print("\n--- Audit Output ---")
        print(result.get("audit_output", ""))
        print("\n--- Full Crew Result ---")
        print(result.get("crew_result", ""))

    except Exception as e:
        print(f"\n❌ PIPELINE CRASHED: {e}")
        import traceback
        traceback.print_exc()
