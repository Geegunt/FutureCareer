export type SupportedLanguage = 'typescript' | 'python' | 'java' | 'go'

export type IdeFile = {
  id: string
  name: string
  path: string
  language: SupportedLanguage
  content: string
  readOnly?: boolean
}

export type ConsoleLine = {
  id: string
  level: 'info' | 'success' | 'error'
  message: string
  timestamp: string
}

export type RuntimeTarget = {
  id: string
  label: string
  description: string
  version: string
}

export type QuickTest = {
  id: string
  name: string
  status: 'pending' | 'passed' | 'failed'
  durationMs?: number
}

const tsSource = `type TestCase = { input: number[]; expected: number }

const sum = (values: number[]) =>
  values.reduce((acc, value) => acc + value, 0)

export const solve = (cases: TestCase[]) => {
  return cases.map(({ input, expected }, idx) => {
    const actual = sum(input)
    return actual === expected
      ? { idx, status: 'ok' }
      : { idx, status: 'fail', actual, expected }
  })
}

if (import.meta.vitest) {
  const sample = [{ input: [1, 2, 3], expected: 6 }]
  console.log(JSON.stringify(solve(sample), null, 2))
}
`

const pySource = `from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class Result:
    idx: int
    passed: bool
    stdout: str


def solve(cases: Iterable[List[int]]) -> List[Result]:
    results: List[Result] = []
    for idx, values in enumerate(cases):
        total = sum(values)
        results.append(Result(idx=idx, passed=total % 2 == 0, stdout=str(total)))
    return results


if __name__ == '__main__':
    print('Executor bootstrapped')
`

const goSource = `package main

import (
  "bufio"
  "fmt"
  "os"
  "strings"
)

func normalize(line string) string {
  return strings.TrimSpace(line)
}

func main() {
  reader := bufio.NewScanner(os.Stdin)
  for reader.Scan() {
    fmt.Println(">>>", normalize(reader.Text()))
  }
}
`

const javaSource = `package sandbox;

import java.time.Instant;
import java.util.List;

public class Runner {
  public record Check(String name, boolean passed, long nanos) {}

  public static List<Check> execute() {
    var started = System.nanoTime();
    return List.of(
        new Check("bootstrap", true, System.nanoTime() - started),
        new Check("health", true, System.nanoTime() - started));
  }

  public static void main(String[] args) {
    System.out.printf("IDE ready @ %s%n", Instant.now());
    execute().forEach(check -> System.out.println(check));
  }
}
`

export const sampleFiles: IdeFile[] = [
  {
    id: 'ts-main',
    name: 'main.ts',
    path: 'src/main.ts',
    language: 'typescript',
    content: tsSource,
  },
  {
    id: 'py-solution',
    name: 'solution.py',
    path: 'tasks/solution.py',
    language: 'python',
    content: pySource,
  },
  {
    id: 'go-runner',
    name: 'runner.go',
    path: 'tasks/runner.go',
    language: 'go',
    content: goSource,
  },
  {
    id: 'java-runner',
    name: 'Runner.java',
    path: 'sandbox/src/Runner.java',
    language: 'java',
    content: javaSource,
    readOnly: true,
  },
]

export const defaultConsole: ConsoleLine[] = [
  {
    id: 'log-1',
    level: 'info',
    message: 'Connected to LSP gateway → TypeScript',
    timestamp: '17:40:12',
  },
  {
    id: 'log-2',
    level: 'success',
    message: 'Static checks passed (fast tier)',
    timestamp: '17:40:32',
  },
  {
    id: 'log-3',
    level: 'info',
    message: 'Docker executor idle. Click "Run" to enqueue job.',
    timestamp: '17:40:45',
  },
]

export const runtimeTargets: RuntimeTarget[] = [
  {
    id: 'ts-runtime',
    label: 'TypeScript • Node 20',
    version: 'node:20-slim',
    description: 'ESM + ts-node@beta + vi-test',
  },
  {
    id: 'py-runtime',
    label: 'Python 3.12',
    version: 'python:3.12-slim',
    description: 'pytest + debugpy',
  },
  {
    id: 'go-runtime',
    label: 'Go 1.23',
    version: 'golang:1.23-alpine',
    description: 'go test + delve dap',
  },
  {
    id: 'java-runtime',
    label: 'Java 21',
    version: 'amazoncorretto:21',
    description: 'maven + jdwp',
  },
]

export const quickTests: QuickTest[] = [
  { id: 'syntax', name: 'Syntax & lint', status: 'passed', durationMs: 750 },
  { id: 'unit', name: 'Core unit tests', status: 'pending' },
  { id: 'io', name: 'I/O contract', status: 'pending' },
  { id: 'perf', name: 'Performance budget', status: 'pending' },
]

