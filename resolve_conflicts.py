import os
def resolve_both(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    out = []
    in_conflict = False
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_conflict = True
        elif line.startswith('======='):
            pass
        elif line.startswith('>>>>>>> upstream/main'):
            in_conflict = False
        else:
            out.append(line)
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(out)

def resolve_upstream(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    out = []
    in_conflict = False
    in_head = False
    for line in lines:
        if line.startswith('<<<<<<< HEAD'):
            in_conflict = True
            in_head = True
        elif line.startswith('======='):
            in_head = False
        elif line.startswith('>>>>>>> upstream/main'):
            in_conflict = False
        elif not in_conflict:
            out.append(line)
        elif in_conflict and not in_head:
            out.append(line)
            
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(out)

resolve_both('frontend/src/routes/_app.settings.tsx')
resolve_both('backend/app/models/__init__.py')

files_to_upstream = [
    'frontend/src/components/applications/ApplicationsList.tsx',
    'frontend/src/components/github/RepositoryStats.tsx',
    'frontend/src/components/profile/ActivityTimeline.tsx',
    'frontend/src/components/profile/BioCard.tsx',
    'frontend/src/components/profile/EducationCard.tsx',
    'frontend/src/components/profile/ExperienceCard.tsx',
    'frontend/src/components/ui/card.tsx',
    'frontend/src/components/ui/filter-drawer.tsx',
    'frontend/src/features/dashboard/GreetingHero.tsx',
    'frontend/src/features/dashboard/StatsRow.tsx',
    'frontend/src/routes/_app.messages.$conversationId.tsx',
    'frontend/src/routes/_app.projects.tsx',
    'frontend/src/routes/_app.templates.tsx',
    'frontend/src/services/index.ts',
]
for f in files_to_upstream:
    resolve_upstream(f)
