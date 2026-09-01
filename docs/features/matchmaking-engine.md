# Matchmaking Engine

The Matchmaking Engine solves the problem of pairing developers to open source projects or hackathon teams. Instead of relying on naive linear sorting (where top developers are heavily fought over while perfectly capable developers are ignored), DevLink uses a Stable Matching algorithm to balance the market.

## Architecture

### 1. The Algorithm: Gale-Shapley (Deferred Acceptance)
The engine executes a variation of the Gale-Shapley algorithm for two-sided markets.
- **Projects are Proposers**: Projects iterate down their ranked preference list of developers and extend offers.
- **Developers are Acceptors**: A developer tentatively accepts the best offer they have received so far. If a better offer comes along later in the iteration, they drop the current project and accept the better one.
- **Result**: The algorithm mathematically guarantees *stability* — there will never be a situation where a Developer and a Project would both rather be with each other than their current assigned matches.

### 2. Preference Weights
The preference lists are generated internally by calculating a bi-directional compatibility score consisting of:
- **Skill Overlap** (65% weight)
- **Timezone Proximity** (20% weight)
- **Experience Compatibility** (15% weight)
- **Availability Penalty**: A 30% penalty is applied to the final score if a developer does not meet the minimum weekly hours requested by the project.

### 3. Team Capacities
The algorithm natively supports multi-participant projects. If a project has a `capacity` of 3, it behaves as if it were 3 independent identical projects making proposals, safely grouping multiple developers without overallocating.

### 4. Conflict Avoidance
Profiles can list `conflicts` (IDs of users or projects they refuse to work with, e.g., due to past toxic interactions). The engine intercepts these during the preference generation phase, setting their compatibility score effectively to 0 and preventing the Gale-Shapley loop from ever proposing the match.

## Usage

```python
from app.services.matchmaking_service import matchmaking_service

response = matchmaking_service.execute_stable_match(
    developers=available_devs_list,
    projects=open_projects_list
)

print(response.matches)               # Stable pairings with explanations
print(response.unmatched_developers)  # Fallback queue
print(response.unmatched_projects)    # Fallback queue
```
