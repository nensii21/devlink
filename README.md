````md
# DevLink

<p align="center">
  <img src="public/logo.png" alt="DevLink Logo" width="180">
</p>

<h1 align="center">DevLink</h1>

<p align="center">
  <strong>Build With People Who Actually Ship.</strong>
</p>

<p align="center">
  A modern platform where developers, founders, designers, AI engineers, and builders discover teammates, collaborate on projects, and launch products together.
</p>

<p align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![React](https://img.shields.io/badge/React-19-61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Vite](https://img.shields.io/badge/Vite-Latest-646CFF)
![Open Source](https://img.shields.io/badge/Open%20Source-Welcome-success)

</p>

---

## Project Purpose

Finding great people to build with is harder than building the product itself.

Current platforms solve only part of the problem.

- GitHub helps developers write code.
- LinkedIn helps professionals network.
- Discord helps communities communicate.

DevLink combines these experiences into a single platform focused on building products together.

Whether you're launching a startup, contributing to open source, or preparing for a hackathon, DevLink helps you find teammates, discover projects, collaborate effectively, and ship faster.

---

## Who Is DevLink For?

- Developers
- Startup Founders
- AI Engineers
- Product Designers
- Students
- Open Source Contributors
- Hackathon Participants
- Indie Hackers

---

# Features

## Builder Discovery

- Search developers by skills
- Public developer profiles
- AI-powered recommendations
- Smart filtering

---

## Project Marketplace

- Browse active projects
- Join startups
- Discover side projects
- Explore hackathons

---

## Team Matching

- Skill matching
- Compatibility scoring
- Team recommendations
- Role suggestions

---

## Builder Profiles

- Skills
- Experience
- Portfolio
- GitHub integration
- LinkedIn integration

---

## Reputation System

- Contribution history
- Builder score
- Project achievements
- Community endorsements

---

## Collaboration Workspace

- Shared workspace
- Progress tracking
- Activity feeds
- Team management

---

## Messaging

- Direct messages
- Team chats
- Real-time conversations

---

# Platform Modules

### Landing Page

- Hero
- Features
- Screenshots
- Roadmap
- FAQ
- Waitlist

### Authentication

- Sign Up
- Login
- Google OAuth
- GitHub OAuth
- Password Recovery
- Email Verification

### Dashboard

- Recommended Builders
- Recommended Projects
- Notifications
- Activity Feed

### Project Hub

- Create Projects
- Manage Team
- Applications
- Project Timeline

### Startup Hub

- Startup Profiles
- Recruitment
- Roadmaps
- Milestones

---

# Tech Stack

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui
- Framer Motion

## Backend

- Next.js API Routes
- Node.js
- TypeScript

## Database

- PostgreSQL

## ORM

- Prisma

## Authentication

- Clerk / NextAuth

## Deployment

- Vercel
- Neon PostgreSQL

---

# Project Structure

```text
devlink
│
├── public/
├── prisma/
├── src/
│   ├── assets/
│   ├── components/
│   ├── hooks/
│   ├── layouts/
│   ├── lib/
│   ├── pages/
│   ├── services/
│   ├── styles/
│   ├── types/
│   └── utils/
│
├── docs/
│   ├── architecture.png
│   └── screenshots/
│
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── package.json
````

---

# Architecture

```text
                    ┌────────────────────────┐
                    │      Web Browser       │
                    └────────────┬───────────┘
                                 │
                           HTTPS / REST
                                 │
             ┌───────────────────▼───────────────────┐
             │      React + TypeScript + Vite        │
             │       Tailwind CSS + shadcn/ui        │
             └───────────────────┬───────────────────┘
                                 │
                         Authentication
                     (Clerk / NextAuth)
                                 │
             ┌───────────────────▼───────────────────┐
             │       Next.js API / Node.js           │
             │        Business Logic Layer           │
             └───────────────────┬───────────────────┘
                                 │
                              Prisma ORM
                                 │
             ┌───────────────────▼───────────────────┐
             │          PostgreSQL Database          │
             └───────────────────────────────────────┘
```

### Application Flow

1. User signs in using Google or GitHub.
2. Frontend sends authenticated requests.
3. Backend processes business logic.
4. Prisma communicates with PostgreSQL.
5. Results are returned to the frontend.

---

# Screenshots

> Screenshots will be added as the project evolves.

| Screen              | Status      |
| ------------------- | ----------- |
| Landing Page        | Coming Soon |
| Login               | Coming Soon |
| Dashboard           | Coming Soon |
| Builder Profile     | Coming Soon |
| Project Marketplace | Coming Soon |
| Messaging           | Coming Soon |

Store screenshots inside:

```text
docs/
└── screenshots/
    ├── landing.png
    ├── dashboard.png
    ├── profile.png
    ├── projects.png
    ├── messaging.png
    └── settings.png
```

---

# Design Philosophy

Inspired by products such as:

* Linear
* Vercel
* Stripe
* Notion
* Railway

Core principles:

* Simplicity
* Performance
* Accessibility
* Professionalism
* Consistency

---

# Roadmap

## Phase 1

* Landing Page
* Authentication
* Builder Profiles
* Project Discovery

## Phase 2

* Team Matching
* Applications
* Messaging

## Phase 3

* Collaboration Workspace
* Reputation System
* AI Recommendations

## Phase 4

* Startup Hub
* Founder Dashboard
* Team Analytics

## Phase 5

* AI Collaboration Assistant
* Productivity Insights
* Smart Team Building

---

# Getting Started

## Prerequisites

* Node.js 20+
* npm
* Git

---

## Clone Repository

```bash
git clone https://github.com/nensii21/devlink.git
cd devlink
```

---

## Install Dependencies

```bash
npm install
```

---

## Configure Environment Variables

Create a `.env.local`

```env
DATABASE_URL=

NEXTAUTH_SECRET=

NEXTAUTH_URL=

GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

## Run Development Server

```bash
npm run dev
```

Visit

```
http://localhost:5173
```

---

## Build Production

```bash
npm run build
```

---

## Preview Production Build

```bash
npm run preview
```

---

# Contributing

Contributions are welcome.

## How to Contribute

1. Fork the repository.

2. Create a feature branch.

```bash
git checkout -b feat/amazing-feature
```

3. Commit your changes.

```bash
git commit -m "feat: add amazing feature"
```

4. Push the branch.

```bash
git push origin feat/amazing-feature
```

5. Open a Pull Request.

---

## Contribution Guidelines

* Follow the existing folder structure.
* Keep pull requests focused on a single feature.
* Write clean and maintainable code.
* Update documentation when required.
* Ensure the project builds successfully.

---

# Future Vision

DevLink aims to become the leading platform where builders connect, collaborate, and launch products together.

The long-term vision includes:

* Startup formation
* AI-powered team matching
* Open source collaboration
* Hackathon ecosystem
* Builder reputation network

---

# License

Distributed under the MIT License.

---

# Author

**nensii21**

Building developer tools that empower builders to collaborate, innovate, and launch impactful products.

---

<p align="center">
Made  for developers, founders, designers, and builders worldwide.
</p>
```
