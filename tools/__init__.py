from llm_client import LLMClient
from sandbox import run_python_code
from tools.registry import ToolRegistry
from tools.generate_code import GenerateCodeTool
from tools.repair_code import RepairCodeTool
from tools.run_tests import RunTestsTool
from tools.read_file import ReadFileTool
from tools.write_file import WriteFileTool
from tools.run_shell import RunShellTool
from tools.run_linter import RunLinterTool
from tools.search_codebase import SearchCodebaseTool
from tools.final_answer import FinalAnswerTool


def create_default_registry(llm: LLMClient) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(GenerateCodeTool(llm))
    registry.register(RepairCodeTool(llm))
    registry.register(RunTestsTool(run_python_code))
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(RunShellTool())
    registry.register(RunLinterTool())
    registry.register(SearchCodebaseTool())
    registry.register(FinalAnswerTool())
    return registry
