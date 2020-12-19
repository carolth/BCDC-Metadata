![workflow_diagram.png](workflow_diagram.png)

The workflow diagram above was produced using PlantUML (the renderer is contained in 1 file, [plantuml.jar](https://plantuml.com/download)).

```
@startuml

participant User

User -> A: DoWork
activate A

A -> B: << createRequest >>
activate B

B -> C: DoWork
activate C

C --> B: WorkDone
destroy C

B --> A: RequestCreated
deactivate B

A -> User: Done
deactivate A

@enduml
```