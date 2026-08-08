
import re

with open("upstream_sections.tsx", "r", encoding="utf-16") as f:
    upstream = f.read()

# Extract from NotificationsWidget to the end
match = re.search(r"// 6\. Notifications \(Sidebar Widget\)\r?\nexport function NotificationsWidget\(\) \{.*", upstream, flags=re.DOTALL)
if match:
    widgets = match.group(0)
    with open("frontend/src/features/dashboard/sections.tsx", "a", encoding="utf-8") as f:
        f.write("\n" + widgets)

