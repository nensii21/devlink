
import os
import re

filepath = "frontend/src/features/dashboard/sections.tsx"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Add missing imports
if "dashboardService" not in content[:500]:
    content = content.replace("import { Card, SectionHeader, Avatar } from \"@/components/shared/primitives\";", "import { Card, SectionHeader, Avatar } from \"@/components/shared/primitives\";\nimport { dashboardService } from \"@/services\";\nimport { useQuery } from \"@tanstack/react-query\";")
if "FolderPlus" not in content[:500]:
    content = content.replace("  Plus,", "  Plus,\n  FolderPlus,")

# Now, we find the dynamic QuickActions and MessagesPreview at the bottom
# They start from: export function MessagesPreview() {
match = re.search(r"export function MessagesPreview\(\) \{.*?(?=export function NotificationsWidget|\Z)", content, flags=re.DOTALL)
if match:
    dynamic_part = match.group(0)
    # Remove dynamic part from bottom
    content = content.replace(dynamic_part, "")
    
    # Extract just dynamic QuickActions
    q_match = re.search(r"export function QuickActions\(\) \{.*?(?=export function|\Z)", dynamic_part, flags=re.DOTALL)
    if q_match:
        dyn_qa = q_match.group(0)
        # Replace static QuickActions
        static_match = re.search(r"// 3\. Quick Actions\nexport function QuickActions\(\) \{.*?(?=// 4\. Recent Activity)", content, flags=re.DOTALL)
        if static_match:
            content = content.replace(static_match.group(0), f"// 3. Quick Actions\n{dyn_qa}\n")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)

