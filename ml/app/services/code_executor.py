import sys
import io
import contextlib
import traceback
from typing import List, Tuple, Any

class CodeExecutor:
    """Исполнитель кода Python в песочнице."""
    
    def execute(self, code: str, inputs: List[str]) -> List[dict]:
        """Выполняет код на списке входных данных.
        
        Args:
            code: Python код для выполнения
            inputs: Список входных данных (каждый - строка)
            
        Returns:
            List[dict]: Результаты выполнения для каждого теста
        """
        passed_count = 0
        results = []
        
        for i, inp in enumerate(inputs):
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            success = False
            output = ""
            error = ""
            
            try:
                stdin_capture = io.StringIO(inp)
                
                input_lines = inp.split('\n') if inp else []
                input_index = [0]
                
                def custom_input(prompt=''):
                    if input_index[0] < len(input_lines):
                        line = input_lines[input_index[0]]
                        input_index[0] += 1
                        return line
                    return ''
                
                with contextlib.redirect_stdout(stdout_capture), \
                     contextlib.redirect_stderr(stderr_capture):
                    
                    exec_globals = {
                        '__builtins__': __builtins__,
                        'input': custom_input,
                    }
                    try:
                        exec(code, exec_globals)
                        success = True
                    except Exception:
                        error = traceback.format_exc()
                        success = False
                
                output = stdout_capture.getvalue().strip()
                if not success:
                    print(f"❌ CodeExecutor: Test {i+1} failed")
                    print(f"   Input: {inp[:50]}...")
                    print(f"   Error: {error}")
                else:
                    print(f"✅ CodeExecutor: Test {i+1} passed")
                    print(f"   Input: {inp[:50]}...")
                    print(f"   Output: {output[:50]}...")
                
                results.append({
                    "input": inp,
                    "output": output,
                    "error": error,
                    "success": success
                })
                
            except Exception as e:
                results.append({
                    "input": inp,
                    "output": "",
                    "error": str(e),
                    "success": False
                })
        
        return results

code_executor = CodeExecutor()
