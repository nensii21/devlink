from app.schemas.readme import ReadmeGenerationRequest, ReadmeGenerationResponse

class ReadmeService:
    @staticmethod
    def generate_readme(payload: ReadmeGenerationRequest) -> ReadmeGenerationResponse:
        sections = ["Overview", "Features", "Installation", "Tech Stack", "Roadmap", "License"]
        
        features_md = "\n".join([f"- {feature}" for feature in payload.features]) if payload.features else "- Feature 1\n- Feature 2"
        tech_stack_md = "\n".join([f"- {tech}" for tech in payload.tech_stack]) if payload.tech_stack else "- Python / FastAPI\n- React / TypeScript"
        installation_md = payload.installation_steps or "```bash\n# Clone the repository\ngit clone [https://github.com/your-username/your-repo.git](https://github.com/your-username/your-repo.git)\n\n# Install dependencies\nnpm install\n```"

        markdown = f"""# {payload.project_title}

> {payload.tagline}

## Overview
Welcome to **{payload.project_title}**, a cutting-edge platform designed to streamline your workflow and deliver exceptional results.

## Features
{features_md}

## Installation
{installation_md}

## Tech Stack
{tech_stack_md}

## Roadmap
- [x] Initial release & core architecture setup
- [ ] Advanced user customisation and metrics dashboard
- [ ] Production scaling and community feedback integrations

## License
Distributed under the {payload.license_type} License. See `LICENSE` for more information.
"""

        return ReadmeGenerationResponse(
            markdown_content=markdown,
            sections_included=sections
        )
    