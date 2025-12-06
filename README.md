# Checklist Manager: Multi-Step Checklist Management System

## Project Overview

This project is a multi-step checklist management system designed to help users organize and execute complex workflows that consist of multiple sequential or parallel steps. Each step contains a list of tasks that need to be completed, with support for task status tracking (Done or N/A), comments, and reference documentation links.

### Example

Think of it as a recipe/procedure management system where:

A Project is like planning a dinner party
Steps are major phases (grocery shopping, cleaning, cooking, etc.)
Tasks are individual actions within each step
Steps can be instantiated multiple times (e.g., "Grocery Shopping - Day 1", "Grocery Shopping - Day 2")
Each task can have links (recipe website) and comments that the user can write

### Primary Goals

Provide a template-based workflow system where admins can define reusable step and task templates
Allow users to create projects based on these templates with customization options
Enable flexible step instantiation - users can add 0 to N instances of each step type
Track execution progress with visual indicators and status management
Support collaborative features through comments and shared documentation

### Business Value

Standardize complex workflows across teams
Reduce errors by providing structured checklists
Track progress and completion metrics
Enable knowledge sharing through embedded documentation links
Support iterative processes (multiple instances of same step)

## Technical Stack

- Backend Framework: Django 5.2+
- Frontend: Django Templates with HTMX (tailwing & DaisyUI)
- State Management:
  - Server-side: Django session
  - Client-side: localStorage for checklist state persistence
- Database: PostgreSQL (Production) / SQLite (Development)
- Deployment Stack: Docker

## Development

1. Setup `checklistapp/.env` from `checklistapp/.env.dist`
1. Install the venv with `uv sync`
1. Create database
   ```
   uv run python manage.py migrate
   ```
1. setup a superuser to be able to manage steps & tasks templates
   ```
   uv run python manage.py createsuperuser
   ```
1. Start the app
   ```
   uv run python manage.py tailwind start
   uv run python manage.py runserver
   ```
1. Open `localhost:8000`, Register an account or login with the superadmin account (not recommended in Production obviously)

## Deployment

1. Refer to `docker-compose.yaml`. It is highly not recommended to use a database in Production in the docker-compose.

> The image is not compatible with a `DEBUG=on` as several dependancies are not installed

> Refer to [this link](https://hub.docker.com/r/coni57/project-checklist) for images
