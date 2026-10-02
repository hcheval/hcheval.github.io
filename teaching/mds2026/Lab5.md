# Lab 5: Implementing AI Agents

## 1. Tool Calls

### Setup

Install the `openai` library (which is compatible with the Ollama API):

```bash
python -m venv .venv 
source .venv/bin/activate
pip install openai
```

We will use the `mistral` model as an example, which should run reasonably well on most machines. 
You can experiment with different models (they need to support tool-calls). Some other models to consider are `mistral-nemo` or `qwen3:4b`.
```
ollama pull mistral
```

### Basic conversation

The `openai` library lets us send messages to an LLM and receive responses. We configure the client to use the local Ollama server:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

response = client.chat.completions.create(
    model="mistral",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
)

print(response.choices[0].message.content)
```

The `messages` field is a list of messages, each with a `role` (`system`, `user`, or `assistant`) and `content`. The model responds based on the entire conversation history.

### Tool calls

An LLM can only generate text, and has no ability to perform side-effects.
A **tool call** allows the model to ask our application (also known as the agent harness) to execute a function and send the result back.

To define a tool, we essentially describe a function signature and an intended usage in a JSON object:

```python
import json

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic expression.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The expression to evaluate, e.g. '2 + 3 * 4'",
                    }
                },
                "required": ["expression"],
            },
        },
    }
]
```

We send the user's message along with the list of available tools:

```python
messages = [
    {"role": "user", "content": "What is 123 * 456?"},
]

response = client.chat.completions.create(
    model="mistral",
    messages=messages,
    tools=tools,
)

msg = response.choices[0].message
```

If the model decides it needs a tool, the response will contain `tool_calls` instead of (or alongside) text. We execute the requested function and send the result back:

```python
if msg.tool_calls:
    messages.append(msg)  # add the model's response to history

    for tool_call in msg.tool_calls:
        name = tool_call.function.name       # "calculate"
        args = json.loads(tool_call.function.arguments)  # {"expression": "123 * 456"}

        # Execute the function locally
        result = str(eval(args["expression"]))

        # Send the result back to the model
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    # Second call: the model formulates the final answer using the tool result
    response = client.chat.completions.create(
        model="mistral",
        messages=messages,
        tools=tools,
    )
    print(response.choices[0].message.content)
```

The pipeline is: **user -> LLM -> tool call -> local execution -> result -> LLM -> final answer**.

The system prompt might need adjusting in order for the model to use the available tools: 
`You are a helpful assistant. Use the provided tools when needed`. 
You can try to be more emphatic about it if tool-calls don't happen (another failure mode 
is for the model to recognize that it needs to call the tool, but instead of calling it to just say `I need to call the tool ...`).

### Exercise

Implement two tools: one for **arithmetic computations** and one for **weather** (see Lab1). Create an interactive loop that reads from stdin, sends to the LLM, executes tool calls if needed, and prints the response.
Compare the response of your model with tool calls to a plain one. 
Hopefully, tool calls allow your model to give a correct answer, whereas the plain model returns nonsense.


## 2. Task Scheduler

We continue from the task scheduler app from Lab 1.
It was a CLI app with commands like `add-task "Pay taxes" 25-05-2026` (the format for the commands was at your choice, this is just an example).

**Exercise**: Extend the app with an agent that can receive such commands in **natural language** instead:
```
Add a task for paying taxes by May 25 this year
```

## 3. Coding Agent

**Exercise**: Implement, through tool calls, a simple coding agent.
The agent will have the ability to **read and write files**, as well as **run commands**.

**Important:** When the agent wants to run a tool, you should not simply run it. That would mean that any command dreamt by the model will run on your machine, which is dangerous.
Instead, you should ask the user for permission before each tool call, displaying the command that needs to run, and wait for confirmation.

We cannot expect too much from such a small and general-purpose model, but filling in some short Python functions should work. 