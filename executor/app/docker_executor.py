"""Docker Executor - Выполнение кода в Docker контейнерах"""

import asyncio
import base64
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import docker


class DockerExecutor:
    """Выполняет код в изолированных Docker контейнерах"""

    # Маппинг языков на Docker образы
    LANGUAGE_CONFIG = {
        'python': {
            'image': 'python:3.12-slim',
            'main_file': 'main.py',
        },
        'typescript': {
            'image': 'node:20-slim',
            'main_file': 'main.ts',
            'setup_command': 'npm install -g typescript ts-node',  # Предустановка для ускорения
        },
        'go': {
            'image': 'golang:1.23-alpine',
            'main_file': 'main.go',
        },
        'java': {
            'image': 'openjdk:21-jdk-slim',
            'main_file': 'Main.java',
        },
    }

    def __init__(self):
        self.client = docker.from_env()
        self._thread_pool = ThreadPoolExecutor(max_workers=4)

    async def _exec_in_container(self, container, command: str, timeout: int) -> tuple[int, str, str]:
        """Выполнить команду внутри контейнера с таймаутом."""

        def _run():
            res = container.exec_run(command, demux=True)
            exit_code = int(res.exit_code) if hasattr(res, 'exit_code') else int(res[0])
            stdout_b, stderr_b = (res.output if hasattr(res, 'output') else res[1])
            stdout = (stdout_b or b'').decode('utf-8', errors='replace')
            stderr = (stderr_b or b'').decode('utf-8', errors='replace')
            return exit_code, stdout, stderr

        return await asyncio.wait_for(asyncio.to_thread(_run), timeout=timeout)

    def _detect_language_from_file(self, filepath: str) -> str | None:
        """Определить язык по расширению файла"""
        ext = os.path.splitext(filepath)[1].lower()
        ext_map = {
            '.py': 'python',
            '.ts': 'typescript',
            '.js': 'typescript',  
            '.go': 'go',
            '.java': 'java',
        }
        return ext_map.get(ext)

    async def execute_code(
        self, language: str, files: dict[str, str], timeout: int = 30, test_cases: list | None = None
    ) -> dict[str, Any]:
        """
        Выполнить код в Docker контейнере
        
        Args:
            language: Язык программирования (может быть переопределен по расширению файла)
            files: Словарь {path: content}
            timeout: Таймаут в секундах
            
        Returns:
            dict с stdout, stderr, exit_code, duration_ms
        """
        start_time = time.time()
        stdout = ''
        stderr = ''
        exit_code = 0

        # Создаем временную директорию
        # Используем /app/tmp внутри executor контейнера для совместимости с Docker-in-Docker
        tmp_base = '/app/tmp'
        os.makedirs(tmp_base, exist_ok=True)
        # Генерируем уникальное имя для volume
        import uuid
        volume_name = f"executor_run_{uuid.uuid4().hex[:12]}"
        tmpdir = os.path.join(tmp_base, volume_name)
        os.makedirs(tmpdir, exist_ok=True)
        try:
            # Записываем файлы
            print(f"📁 Received files: {list(files.keys())}")
            for filepath, content in files.items():
                full_path = os.path.join(tmpdir, filepath)
                print(f"📝 Writing file: {filepath} -> {full_path}")
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ File written: {full_path} (exists: {os.path.exists(full_path)})")

            # Определяем язык по расширению файла (приоритет над переданным языком)
            detected_language = None
            main_file_path = None
            
            # Находим главный файл и определяем язык
            # Приоритет: файлы с расширением языка программирования
            for filepath in files.keys():
                file_lang = self._detect_language_from_file(filepath)
                if file_lang:
                    detected_language = file_lang
                    main_file_path = filepath
                    break
            
            # Если не определили по расширению, используем переданный язык
            if not detected_language:
                detected_language = language
            
            # Если не нашли главный файл, ищем любой файл с нужным расширением
            if not main_file_path:
                ext_map = {
                    'python': '.py',
                    'typescript': '.ts',
                    'go': '.go',
                    'java': '.java',
                }
                target_ext = ext_map.get(detected_language, '.py')
                for filepath in files.keys():
                    if filepath.endswith(target_ext):
                        main_file_path = filepath
                        break
            
            # Если всё ещё не нашли, берём первый файл
            if not main_file_path:
                main_file_path = list(files.keys())[0]
            
            print(f"🔍 Detected language: {detected_language}")
            print(f"📄 Main file path: {main_file_path}")

            # Проверяем, поддерживается ли язык
            if detected_language not in self.LANGUAGE_CONFIG:
                raise ValueError(f'Unsupported language: {detected_language}')

            config = self.LANGUAGE_CONFIG[detected_language]
            language = detected_language  # Используем определенный язык

            # Определяем команду запуска на основе определенного языка
            if language == 'typescript':
                # Для TypeScript компилируем в JavaScript и запускаем
                # Используем tsc для компиляции всех .ts файлов
                js_file = main_file_path.replace('.ts', '.js')
                # Компилируем все .ts файлы в текущей директории и запускаем главный
                # npx -y tsc скачает и запустит TypeScript компилятор
                command = f'/bin/sh -c "cd /workspace && npx -y tsc --target ES2020 --module commonjs --esModuleInterop --skipLibCheck *.ts 2>&1 && node {js_file}"'
            elif language == 'java':
                # Для Java нужно скомпилировать
                class_name = os.path.splitext(os.path.basename(main_file_path))[0]
                command = f'/bin/sh -c "cd /workspace && javac {main_file_path} && java {class_name}"'
            elif language == 'go':
                command = f'go run /workspace/{main_file_path}'
            else:
                # Python
                command = f'python /workspace/{main_file_path}'
            
            print(f"🐳 Docker command: {command}")
            print(f"📂 tmpdir: {tmpdir}")
            print(f"📂 tmpdir is absolute: {os.path.isabs(tmpdir)}")
            print(f"📂 tmpdir exists: {os.path.exists(tmpdir)}")
            print(f"📂 Files in tmpdir: {os.listdir(tmpdir)}")
            for f in os.listdir(tmpdir):
                full = os.path.join(tmpdir, f)
                print(f"   - {f}: size={os.path.getsize(full)} bytes")

            runner_command = None

            if not test_cases:
                # Запускаем контейнер напрямую только если нет набора тестов.
                container = None
                try:
                    use_network = language == 'typescript'
                    # Создаем контейнер без запуска
                    container = self.client.containers.create(
                        image=config['image'],
                        command=command,
                        mem_limit='512m',
                        cpu_period=100000,
                        cpu_quota=50000,
                        network_disabled=not use_network,
                        working_dir='/workspace',
                        environment={'NPM_CONFIG_CACHE': '/tmp/.npm'} if use_network else None,
                    )
                    
                    # Копируем файлы в контейнер
                    import tarfile
                    import io
                    tar_stream = io.BytesIO()
                    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                        for filename in os.listdir(tmpdir):
                            filepath = os.path.join(tmpdir, filename)
                            if os.path.isfile(filepath):
                                tar.add(filepath, arcname=filename)
                    tar_stream.seek(0)
                    container.put_archive('/workspace', tar_stream)
                    
                    # Запускаем контейнер
                    container.start()
                    try:
                        container.wait(timeout=timeout)
                    except Exception as wait_exc:  # noqa: BLE001
                        container.stop(timeout=1)
                        raise TimeoutError(f'Execution timeout after {timeout} seconds') from wait_exc

                    stdout_bytes = container.logs(stdout=True, stderr=False)
                    stderr_bytes = container.logs(stdout=False, stderr=True)
                    container.reload()
                    exit_code = container.attrs['State']['ExitCode'] or 0
                    stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ''
                    stderr_raw = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ''
                    stderr = stderr_raw if exit_code != 0 and stderr_raw.strip() else ''
                except TimeoutError as exc:
                    stdout = ''
                    stderr = str(exc)
                    exit_code = -1
                except docker.errors.ContainerError as exc:
                    stdout = exc.stdout.decode('utf-8', errors='replace') if exc.stdout else ''
                    stderr = exc.stderr.decode('utf-8', errors='replace') if exc.stderr else str(exc)
                    exit_code = exc.exit_status
                except Exception as exc:  # noqa: BLE001
                    stdout = ''
                    stderr = f'Docker error: {str(exc)}'
                    exit_code = -1
                finally:
                    try:
                        if container:
                            container.remove(force=True)
                    except Exception:  # noqa: BLE001
                        pass

            # Если есть тесты, выполняем их в ОДНОМ контейнере (вместо контейнера на каждый тест)
            test_results = []
            if test_cases:
                container = None
                first_error_output = ''
                try:
                    use_network = language == 'typescript'
                    container = self.client.containers.create(
                        image=config['image'],
                        command='/bin/sh -c "sleep 3600"',
                        mem_limit='512m',
                        cpu_period=100000,
                        cpu_quota=50000,
                        network_disabled=not use_network,
                        working_dir='/workspace',
                        environment={'NPM_CONFIG_CACHE': '/tmp/.npm'} if use_network else None,
                    )
                    container.start()

                    import tarfile
                    import io
                    tar_stream = io.BytesIO()
                    with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                        for filename in os.listdir(tmpdir):
                            filepath = os.path.join(tmpdir, filename)
                            if os.path.isfile(filepath):
                                tar.add(filepath, arcname=filename)
                    tar_stream.seek(0)
                    container.put_archive('/workspace', tar_stream)

                    # Подготовка (компиляция) один раз
                    if language == 'typescript':
                        await self._exec_in_container(
                            container,
                            '/bin/sh -lc "cd /workspace && npx -y tsc --target ES2020 --module commonjs --esModuleInterop --skipLibCheck *.ts"',
                            timeout=timeout,
                        )
                        runner_command = f"node {main_file_path.replace('.ts', '.js')}"
                    elif language == 'java':
                        await self._exec_in_container(
                            container,
                            f'/bin/sh -lc "cd /workspace && javac {main_file_path}"',
                            timeout=timeout,
                        )
                        class_name = os.path.splitext(os.path.basename(main_file_path))[0]
                        runner_command = f"java {class_name}"
                    elif language == 'go':
                        await self._exec_in_container(
                            container,
                            f'/bin/sh -lc "cd /workspace && go build -o main_bin {main_file_path}"',
                            timeout=timeout,
                        )
                        runner_command = "./main_bin"
                    else:
                        runner_command = f"python {main_file_path}"

                    for test_idx, test_case in enumerate(test_cases):
                        if isinstance(test_case, dict):
                            test_input = test_case.get('input', '')
                            expected_output = test_case.get('output', '').strip()
                        else:
                            test_input = test_case.input
                            expected_output = test_case.output.strip()

                        test_start_time = time.time()
                        b64 = base64.b64encode((test_input or '').encode('utf-8')).decode('ascii')
                        cmd = f'/bin/sh -lc "cd /workspace && echo {b64} | base64 -d | {runner_command}"'
                        try:
                            t_exit, t_out, t_err = await self._exec_in_container(container, cmd, timeout=timeout)
                        except TimeoutError:
                            t_exit, t_out, t_err = -1, '', f'Execution timeout after {timeout} seconds'
                        except asyncio.TimeoutError:
                            t_exit, t_out, t_err = -1, '', f'Execution timeout after {timeout} seconds'

                        test_duration_ms = int((time.time() - test_start_time) * 1000)
                        actual_output = (t_out or '').strip()
                        passed = (t_exit == 0) and (actual_output == expected_output)

                        actual_output_with_error = actual_output
                        if t_err and str(t_err).strip():
                            if not first_error_output:
                                first_error_output = str(t_err).strip()
                            actual_output_with_error = (
                                f"{actual_output}\nОшибка: {str(t_err).strip()}" if actual_output else f"Ошибка: {str(t_err).strip()}"
                            )

                        test_results.append({
                            'test_index': test_idx + 1,
                            'input': test_input,
                            'expected_output': expected_output,
                            'actual_output': actual_output_with_error,
                            'passed': passed,
                            'exit_code': t_exit,
                            'duration_ms': test_duration_ms,
                        })

                    passed_count = sum(1 for tr in test_results if tr['passed'])
                    total_count = len(test_results)
                    all_passed = passed_count == total_count
                    verdict = 'ACCEPTED' if all_passed else 'WRONG ANSWER'

                    stdout_lines = [f'Вердикт: {verdict}', f'Пройдено тестов: {passed_count}/{total_count}', '']
                    for tr in test_results:
                        status_icon = '✅' if tr['passed'] else '❌'
                        stdout_lines.append(
                            f'{status_icon} Тест {tr["test_index"]}: {tr["actual_output"]} (ожидалось: {tr["expected_output"]})'
                        )

                    stdout = '\n'.join(stdout_lines)
                    if not all_passed and first_error_output:
                        stderr = first_error_output
                    exit_code = 0 if all_passed else 1
                finally:
                    try:
                        if container:
                            container.remove(force=True)
                    except Exception:  # noqa: BLE001
                        pass
            else:
                verdict = None
                test_results = None

            return {
                'stdout': stdout,
                'stderr': stderr,
                'exit_code': exit_code,
                'duration_ms': int((time.time() - start_time) * 1000),
                'test_results': test_results,
                'verdict': verdict,
            }
        finally:
            # Cleanup temporary directory
            import shutil
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir, ignore_errors=True)

    async def _run_test(
        self,
        language: str,
        main_file_path: str,
        tmpdir: str,
        test_input: str,
        timeout: int,
        runner_command: str | None = None,
    ) -> dict[str, Any]:
        """Запустить код на одном тесте"""
        config = self.LANGUAGE_CONFIG[language]
        
        # Записываем входные данные во временный файл для надежной передачи
        input_file_path = os.path.join(tmpdir, 'test_input.txt')
        # Убеждаемся, что входные данные не пустые и правильно записаны
        test_input_normalized = test_input if test_input else ''
        with open(input_file_path, 'w', encoding='utf-8') as f:
            f.write(test_input_normalized)
        
        # Проверяем, что файл создан
        if not os.path.exists(input_file_path):
            return {
                'stdout': '',
                'stderr': 'Failed to create input file',
                'exit_code': -1,
            }
        
        # Определяем команду запуска с перенаправлением из файла
        # working_dir = /workspace, используем абсолютные пути
        if runner_command:
            command = f'/bin/sh -c "cd /workspace && cat test_input.txt | {runner_command}"'
        else:
            if language == 'typescript':
                js_file = main_file_path.replace('.ts', '.js')
                command = f'/bin/sh -c "cd /workspace && npx -y tsc --target ES2020 --module commonjs --esModuleInterop --skipLibCheck *.ts 2>&1 && cat test_input.txt | node {js_file}"'
            elif language == 'java':
                class_name = os.path.splitext(os.path.basename(main_file_path))[0]
                command = f'/bin/sh -c "cd /workspace && cat test_input.txt | java {class_name}"'
            elif language == 'go':
                command = f'/bin/sh -c "cd /workspace && cat test_input.txt | go run {main_file_path}"'
            else:
                # Python  
                command = f'sh -c "cd /workspace && cat test_input.txt | python {main_file_path}"'
            
        print(f"🐳 Test command: {command}")
        
        container = None
        try:
            use_network = language == 'typescript'
            # Создаем контейнер без запуска
            container = self.client.containers.create(
                image=config['image'],
                command=command,
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=50000,
                network_disabled=not use_network,
                working_dir='/workspace',
                environment={'NPM_CONFIG_CACHE': '/tmp/.npm'} if use_network else None,
            )
            
            # Копируем файлы в контейнер
            import tarfile
            import io
            tar_stream = io.BytesIO()
            with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                for filename in os.listdir(tmpdir):
                    filepath = os.path.join(tmpdir, filename)
                    if os.path.isfile(filepath):
                        tar.add(filepath, arcname=filename)
            tar_stream.seek(0)
            container.put_archive('/workspace', tar_stream)
            
            # Запускаем контейнер
            container.start()
            container.wait(timeout=timeout)
            
            stdout_bytes = container.logs(stdout=True, stderr=False)
            stderr_bytes = container.logs(stdout=False, stderr=True)
            
            container.reload()
            exit_code = container.attrs['State']['ExitCode'] or 0
            
            stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ''
            # Показываем stderr только если есть реальная ошибка (exit_code != 0)
            # Игнорируем предупреждения компилятора и другие несущественные сообщения
            stderr_raw = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ''
            stderr = stderr_raw if exit_code != 0 and stderr_raw.strip() else ''
            
        except Exception as exc:  # noqa: BLE001
            stdout = ''
            stderr = str(exc)
            exit_code = -1
        finally:
            try:
                if container:
                    container.remove(force=True)
            except Exception:  # noqa: BLE001
                pass
        
        return {
            'stdout': stdout,
            'stderr': stderr,
            'exit_code': exit_code,
        }

    def _prepare_runner(
        self,
        language: str,
        main_file_path: str,
        tmpdir: str,
        timeout: int,
    ) -> str:
        """
        Предварительно компилирует/подготавливает окружение и возвращает команду запуска
        без учёта передачи входных данных (stdin подключается отдельно).
        """
        config = self.LANGUAGE_CONFIG[language]
        use_network = language == 'typescript'
        compile_container = None

        def run_compile(command: str):
            nonlocal compile_container
            try:
                # Создаем контейнер без запуска
                compile_container = self.client.containers.create(
                    image=config['image'],
                    command=command,
                    mem_limit='512m',
                    cpu_period=100000,
                    cpu_quota=50000,
                    network_disabled=not use_network,
                    working_dir='/workspace',
                    environment={'NPM_CONFIG_CACHE': '/tmp/.npm'} if use_network else None,
                )
                
                # Копируем файлы в контейнер
                import tarfile
                import io
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    for filename in os.listdir(tmpdir):
                        filepath = os.path.join(tmpdir, filename)
                        if os.path.isfile(filepath):
                            tar.add(filepath, arcname=filename)
                tar_stream.seek(0)
                compile_container.put_archive('/workspace', tar_stream)
                
                # Запускаем контейнер
                compile_container.start()
                compile_container.wait(timeout=timeout)
            except Exception as exc:  # noqa: BLE001
                logs = ''
                if compile_container:
                    try:
                        logs_bytes = compile_container.logs(stdout=True, stderr=True)
                        logs = logs_bytes.decode('utf-8', errors='replace')
                    except Exception:  # noqa: BLE001
                        logs = ''
                raise RuntimeError(f'Failed to prepare {language} environment: {exc}\n{logs}') from exc
            finally:
                try:
                    if compile_container:
                        compile_container.remove(force=True)
                except Exception:  # noqa: BLE001
                    pass

        if language == 'typescript':
            js_file = main_file_path.replace('.ts', '.js')
            compile_cmd = '/bin/sh -c "cd /workspace && npx -y tsc --target ES2020 --module commonjs --esModuleInterop --skipLibCheck *.ts"'
            run_compile(compile_cmd)
            return f'node {js_file}'

        if language == 'go':
            binary_name = 'main_bin'
            compile_cmd = f'/bin/sh -c "cd /workspace && go build -o {binary_name} {main_file_path}"'
            run_compile(compile_cmd)
            return f'./{binary_name}'

        if language == 'java':
            class_name = os.path.splitext(os.path.basename(main_file_path))[0]
            compile_cmd = f'/bin/sh -c "cd /workspace && javac {main_file_path}"'
            run_compile(compile_cmd)
            return f'java {class_name}'

        # Python и прочее без подготовки
        return f'python {main_file_path}'

