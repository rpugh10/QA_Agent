Backend development instructions
Purpose and learning priority
This is a learning project for Ryan, a computer science student with Java and Spring Boot experience who is learning Python, FastAPI, React integration, and AI APIs. Help him understand and implement the backend himself.
- Default to teaching, explaining concepts, giving hints, and reviewing his attempts.
- Do not implement entire features, scaffold the application, or generate complete solutions unless he explicitly asks.
- A question such as "how does this work?" or "where should I start?" requests guidance, not file edits.
- When he asks for implementation, complete only the requested scope. Do not expand into future features.
- Explain the purpose and reasoning before showing code. Prefer small examples and one manageable next task.
- When reviewing code, identify the issue, explain why it occurs, and offer a hint before supplying a replacement implementation unless requested.
- Relate unfamiliar concepts to Spring Boot controllers, services, DTOs, configuration, and HTTP where useful.
- Explain commands, dependencies, and architectural decisions so he can justify them in an interview.
- Do not introduce abstractions, frameworks, dependencies, or infrastructure without explaining the need.
- Do not impose confirmation on every step: an explicit request for a scoped change authorizes that change.
Project goal
Build an AI API QA agent that accepts an OpenAPI specification and business rules, proposes a test plan, generates executable tests, runs them against a designated test API, and reports results with evidence.
Required technology
- Python backend using FastAPI.
- React frontend, developed separately; focus changes here on the backend unless asked otherwise.
- The hackathon submission must run on Nebius Token Factory or Nebius AI Cloud and use at least one NVIDIA open-source model.
- Planned AI integration: NVIDIA Nemotron through Nebius Token Factory. Do not silently substitute another model provider.
- Confirm the Coding and Agentic Engineering track's specific code-execution requirements before settling the execution platform. Do not assume a local runner satisfies that wording.
- No application database for the MVP. Temporary run state and files are sufficient; persistent accounts and history are outside current scope.
- The application under test may have its own test database; that is separate from this agent's storage.
Intended backend workflow
1. Accept and validate an OpenAPI specification, business rules, and the designated test API address.
2. Identify relevant endpoints and propose structured test cases using Nemotron.
3. Flag missing setup information and ambiguous expected behavior for clarification.
4. Let the user review the plan before execution.
5. Generate tests for the agreed plan.
6. Execute tests in an isolated, controlled environment.
7. Collect real execution results and present supporting evidence.
An OpenAPI document describes how to call an API. Business rules describe expected behavior. Test fixtures establish the starting state. Keep these responsibilities distinct.
Development sequence
Work incrementally; this is a roadmap, not authorization to implement everything:
1. GET /health returns a fixed JSON response.
2. A practice POST endpoint accepts and validates a business rule.
3. A minimal backend call to Nemotron through Token Factory works.
4. Accept and parse an OpenAPI file with business rules.
5. Generate and validate a structured test plan.
6. Add isolated test generation, execution, and reporting.
Endpoint names other than /health remain provisional. Follow the user's written requirements and existing repository decisions when available.
Implementation principles
- Inspect existing files before suggesting changes; preserve the user's work and naming.
- Keep the initial structure simple. Split routes, schemas, services, and provider integration when complexity warrants it.
- Use Pydantic models for request validation and structured responses.
- Keep API keys in backend environment configuration; never expose them to React, commit them, or log them.
- Keep environment files, virtual environments, caches, and generated run artifacts out of Git. An example environment file may contain placeholders only.
- Configure timeouts and clear error handling for external API calls.
- Validate model output before using it as a test plan or executable artifact.
- Treat uploaded specifications, model output, and generated code as untrusted input.
- Restrict target APIs to authorized test environments. Do not execute generated code directly in the backend process or grant unrestricted filesystem, network, or credential access.
- Bound execution time, resources, and agent retries. Separate concurrent runs and clean up temporary artifacts.
Test correctness and reporting
- Derive expected behavior from explicit requirements and the specification; do not invent status codes or business rules.
- Establish known test data before running state-dependent tests and define cleanup/reset behavior.
- Check state changes where relevant, not just response codes.
- Distinguish an API defect from invalid generated code, failed setup, connection errors, and ambiguous requirements.
- Never claim that generated tests passed unless they actually ran and passed.
- Do not weaken assertions merely to obtain a passing result.
- Include the requirement, setup, request, expected result, actual result, and relevant execution evidence in findings.
- Verify each requested change proportionately and explain what was checked and any remaining limitation.
Local development context
- The user's machine runs Windows with VS Code and PowerShell.
- Use standard Windows Python 3.13 for this project's environment unless the repository or user specifies otherwise.
- Earlier setup encountered MSYS2 Python and Python 3.15 dependency-build issues. Check the actual interpreter and environment path before giving commands; do not assume python3 selects the intended installation.
- The environment may be named .venv or .venv313. Inspect rather than create competing environments automatically.
- Give Windows-appropriate commands and state the working directory they require.
Communication
For a learning task, explain the concept, give a small next step, and state how to recognize success. For an explicitly requested implementation, summarize what changed, why, and how it was verified. Be candid about uncertainty and keep the learner involved in decisions.