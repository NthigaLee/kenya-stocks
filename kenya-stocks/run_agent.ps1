$task = Get-Content "C:\Users\nthig\.openclaw\workspace\kenya-stocks\agent_task.md" -Raw
claude --dangerously-skip-permissions -p $task
